from web import app, db
from flask import render_template, request, make_response
from datetime import datetime, timedelta
import dateutil.parser
from sqlalchemy.sql import expression
from menu_diff import diff_beverages
from models import Location, MenuScrape, Chain, User


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/locations/')
def location_index():
    return render_template('location_index.html', locations=Location.query.all())


@app.route('/locations/<id>')
def location(id):
    return render_template('location_view.html', location=Location.query.get_or_404(id))


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
        #TODO: match on day, not entire created timestamp
        #TODO: always return a menu if possible (nearest matching date)
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
            #TODO: If we have an end date, set this to the nearest scrape of same location ~week before
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
            message = 'Logged in as new user "{}".'.format(username)
        else:
            message = 'Logged in as user "{}".'.format(username)
        resp = make_response(render_template('users_login.html', current_user=user.username, message=message))
        resp.set_cookie('username', username)
    else:
        resp = render_template('users_login.html', current_user=current_user)
    return resp
