from scraper.util import expand_menu_scrape
from web import app, db
from scraper.cache import get_cache, get_cache_near, get_cache_extreme
from flask import render_template, request
from datetime import datetime, timedelta
import dateutil.parser
from menu_diff import diff_beverages
from scraper import stout, ball_and_chain
from models import Location, Chain


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/locations/')
def location_index():
    context = {
        'chains': Chain.query.all()
    }
    return render_template('location_index.html', **context)


@app.route('/location/<id>')
def location(id):
    location = Location.query.get(id)
    return render_template('location_view.html', location=location)


@app.route('/menu/')
def menu_index():
    # TODO: List all menu scrapes, click to view
    return render_template('menu_index.html')


@app.route('/menu/<menu_name>/')
def menu_view(menu_name):
    menu = get_cache(name=menu_name)
    return render_template('table_view.html', menu=menu)


@app.route('/menu/diff/')
def menu_diff():
    context = {}
    # TODO: Display note if exact cache wasn't available
    # TODO: JS datepicker widget
    # Grab parameters
    chain = request.args.get('chain')
    location = request.args.get('location')
    start = request.args.get('start')
    end = request.args.get('end')
    # Compute diff
    if location and start:
        old_menu = get_cache_near(chain, location, dateutil.parser.parse(start), 'new')
        if end:
            new_menu = get_cache_near(chain, location, dateutil.parser.parse(end), 'old')
        else:
            new_menu = get_cache_extreme(chain, location, 'new')
        context['old_menu'] = expand_menu_scrape(old_menu)
        context['new_menu'] = expand_menu_scrape(new_menu)
        context['added'], context['removed'] = \
            diff_beverages(context['old_menu'].beverages, context['new_menu'].beverages)
    else:
        # Form defaults
        if not start:
            start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end:
            end = datetime.now().strftime('%Y-%m-%d')

    context.update({
                       'chain': chain,
                       'location': location,
                       'start': start,
                       'end': end,
                       'chain_opts': get_chain_dict()
                   }.items())

    return render_template('diff.html', **context)


def get_chain_dict():
    """
    Get a simple dict of chains and their locations

    :return: Dictionary of 'Chain': ['Location', 'Location']
    :rtype: dict
    """
    return {
        'Stout': {x.name: x.name for x in stout.locations},
        'Ball and Chain': {x.name: x.name for x in ball_and_chain.locations}
    }
