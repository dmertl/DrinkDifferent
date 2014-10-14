from web import app, db
from flask import render_template, request, make_response, abort, redirect
from datetime import datetime, timedelta
import json
import dateutil.parser
from sqlalchemy.sql import expression
from menu_diff import diff_beverages
from models import Location, MenuScrape, Chain, User, BeverageCheckoff, Beverage
from untappd import Untappd


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/locations/')
def location_index():
    return render_template('location_index.html', locations=Location.query.all())


@app.route('/locations/<id>')
def location(id):
    location = Location.query.get_or_404(id)
    # TODO: moved user to shared location
    current_user = None
    if 'username' in request.cookies:
        current_user = User.query.filter_by(username=request.cookies.get('username')).first()
        # Better system for getting checkoffs
        for beverage in location.beverages:
            for checkoff in current_user.beverage_checkoffs:
                if checkoff.compare(beverage):
                    beverage.checkoff = checkoff
                    break
    return render_template('location_view.html', location=location, current_user=current_user)


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


@app.route('/users/login', methods=['GET', 'POST'])
def users_login():
    current_user = request.cookies.get('username')
    username = request.form.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
            message = 'Logged in as new user "{}".'.format(username)
        else:
            message = 'Logged in as user "{}".'.format(username)
        resp = make_response(render_template('users_login.html', current_user=user.username, message=message))
        resp.set_cookie('username', username)
    else:
        resp = render_template('users_login.html', current_user=current_user)
    return resp


@app.route('/beverage_checkoffs/add', methods=['PUT'])
def beverage_checkoffs_add():
    name = request.form.get('name')
    brewery = request.form.get('brewery')
    beverage_id = request.form.get('beverage_id')
    username = request.cookies.get('username')
    if name and brewery and beverage_id and username:
        # TODO: Handle this in JS
        if brewery == 'None':
            brewery = None
        user = User.query.filter_by(username=username).first_or_404()
        checkoff = BeverageCheckoff.query.filter_by(name=name, brewery=brewery, beverage_id=beverage_id,
                                                    user_id=user.id).first()
        if not checkoff:
            beverage = Beverage.query.get_or_404(beverage_id)
            checkoff = BeverageCheckoff(name=name, brewery=brewery, beverage_id=beverage.id, user=user)
            db.session.add(checkoff)
            db.session.commit()
        resp = make_response(json.dumps(checkoff.flatten()))
        resp.mimetype = 'application/json'
        return resp
    else:
        abort(400)


@app.route('/beverage_checkoffs/delete/<id>', methods=['DELETE'])
def beverage_checkoffs_delete(id):
    username = request.cookies.get('username')
    if username:
        user = User.query.filter_by(username=username).first_or_404()
        checkoff = BeverageCheckoff.query.get_or_404(id)
        if user == checkoff.user:
            db.session.delete(checkoff)
            db.session.commit()
            resp = make_response(json.dumps(checkoff.flatten()))
            resp.mimetype = 'application/json'
            return resp
        else:
            abort(401)
    else:
        abort(401)


@app.route('/auth')
def untappd_auth():
    # TODO: Store access token in DB
    untappd = Untappd(client_id='04513C89D24C72DD55C71441835D7BF4FF70077E',
                      client_secret='02D05C33B6152E3BC9183ECB5BE58DF289D47457',
                      redirect_uri='http://dmertl.com/drink_different/auth')
    # TEST
    access_token = None
    # TEST
    if not access_token:
        if 'code' in request.args:
            access_token = untappd.oauth.get_token(request.args.get('code'))
            untappd.set_access_token(access_token)
        else:
            auth_uri = untappd.oauth.auth_url()
            return redirect(auth_uri)

    info = untappd.user.info('dmertl')
    return json.dumps(info)
