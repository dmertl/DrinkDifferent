from web import app, db
from flask import render_template, request, make_response, abort, redirect, session, g, url_for
from datetime import datetime, timedelta
import json
import dateutil.parser
from sqlalchemy.sql import expression
from menu_diff import diff_beverages
from models import Location, MenuScrape, Chain, User, Beverage, DistinctBeer
from untappd import Untappd


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.route('/')
def home():
    return render_template('home.html', user=g.user)


@app.route('/locations/')
def location_index():
    return render_template('location_index.html', locations=Location.query.all())


@app.route('/locations/<id>')
def location(id):
    location = Location.query.get_or_404(id)
    # TODO: moved user to shared location
    # TEST username
    current_user = User.query.filter_by(username='dmertl').first()
    # current_user = None
    # if 'username' in request.cookies:
    # current_user = User.query.filter_by(username=request.cookies.get('username')).first()
    #TODO: Join to find consumed/unconsumed
    consumed = []
    unconsumed = location.beverages[:]
    for loc_bev in location.beverages:
        if loc_bev.untappd_id:
            for user_bev in current_user.distinct_beers:
                if str(user_bev.untappd_bid) == str(loc_bev.untappd_id):
                    consumed.append(loc_bev)
                    for con_bev in unconsumed:
                        if con_bev.untappd_id == loc_bev.untappd_id:
                            del con_bev

    return render_template('location_view.html', location=location, current_user=current_user, consumed=consumed,
                           unconsumed=unconsumed)


@app.route('/beverages', methods=['GET', 'POST'])
def beverage_index():
    bids = request.form.getlist('bid[]')
    beverage_ids = request.form.getlist('beverage_id[]')
    if bids:
        cnt = 0
        for bid in bids:
            if bid:
                # Assumes sequential data
                beverage_id = beverage_ids[cnt]
                beverage = Beverage.query.get(beverage_id)
                if beverage:
                    beverage.untappd_id = str(bid)
                    db.session.add(beverage)
                    distinct = DistinctBeer.query.filter_by(untappd_bid=bid).first()
                    if distinct:
                        distinct.beverage_id = beverage.id
            cnt += 1
        db.session.commit()
    beverages = Beverage.query.filter_by(type='Beer')
    return render_template('beverage_index.html', beverages=beverages)


@app.route('/menus/')
def menu_index():
    return render_template('menu_index.html', menus=MenuScrape.query.all())


@app.route('/menus/<id>')
def menu(id):
    return render_template('menu_view.html', menu=MenuScrape.query.get_or_404(id))


@app.route('/menus/diff')
def menu_diff():
    context = {}
    # TODO: add nearest cache support back
    # TODO: JS datepicker widget
    # Grab parameters
    chain_id = request.args.get('chain_id')
    location_id = request.args.get('location_id')
    start = request.args.get('start')
    if start:
        start = dateutil.parser.parse(start)
    end = request.args.get('end')
    if end:
        end = dateutil.parser.parse(end)
    # Compute diff
    if location and start:
        context['diff'] = {'added': [], 'removed': []}
        # TODO: match on day, not entire created timestamp
        # TODO: always return a menu if possible (nearest matching date)
        # TODO: lean newer
        context['old_menu'] = MenuScrape.query.filter(
            expression.between(MenuScrape.created, start, start + timedelta(days=1)),
            MenuScrape.location_id == location_id
        ).first_or_404()
        # TODO: lean older
        context['new_menu'] = MenuScrape.query.filter(
            expression.between(MenuScrape.created, end, end + timedelta(days=1)),
            MenuScrape.location_id == location_id
        ).first_or_404()
        # TODO: if no end provided, get newest
        added, removed = diff_beverages(context['old_menu'].beverages, context['new_menu'].beverages)
        context['diff'] = {
            'added': added,
            'removed': removed
        }
    else:
        # Form defaults
        if not end:
            newest = db.session.query(expression.func.max(MenuScrape.created))
            if newest:
                end = newest[0][0]
            else:
                end = datetime.now()
        if not start:
            # TODO: If we have an end date, set this to the nearest scrape of same location ~week before
            start = datetime.now() - timedelta(days=7)

    chains = Chain.query.all()
    chain_opts = dict((c.id, {l.id: l.name for l in c.locations}) for c in chains)

    context.update({
                       'chain_id': chain_id,
                       'location_id': location_id,
                       'start': start,
                       'end': end,
                       'chains': chains,
                       'chain_opts': chain_opts
                   }.items())

    return render_template('menu_diff.html', **context)


@app.route('/auth')
def untappd_auth():
    untappd = Untappd(client_id='04513C89D24C72DD55C71441835D7BF4FF70077E',
                      client_secret='02D05C33B6152E3BC9183ECB5BE58DF289D47457',
                      redirect_uri='http://dmertl.com/drink_different/auth')

    if 'code' in request.args:
        access_token = untappd.oauth.get_token(request.args.get('code'))
        untappd.set_access_token(access_token)
        untappd_user = untappd.user.info()
        user = User.query.filter_by(username=untappd_user['user']['user_name']).first()
        if not user:
            user = User(username=untappd_user['user']['user_name'], access_token=access_token)
            db.session.add(user)
            db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('home'))
    else:
        auth_uri = untappd.oauth.auth_url()
        return redirect(auth_uri)


@app.route('/sync_distinct')
def sync_distinct():
    if g.user:
        untappd = Untappd(client_id='04513C89D24C72DD55C71441835D7BF4FF70077E',
                          client_secret='02D05C33B6152E3BC9183ECB5BE58DF289D47457',
                          redirect_uri='http://dmertl.com/drink_different/auth')
        untappd.set_access_token(g.user.access_token)
        next_offset = 0
        while True:
            beers = untappd.user.beers(g.user.username, {'offset': next_offset, 'sort': 'date'})
            if not beers or not beers['beers']['items']:
                break
            next_offset += beers['beers']['count']
            for beer in beers['beers']['items']:
                beverage = Beverage.query.filter_by(untappd_id=beer['beer']['bid']).first()
                if not beverage:
                    beverage = None
                distinct_beer = DistinctBeer(untappd_bid=beer['beer']['bid'], untappd_username=g.user.username,
                                             user=g.user, beverage=beverage)
                db.session.add(distinct_beer)
            db.session.commit()
        return 'Done!'
    else:
        return abort(401)
