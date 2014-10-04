import os
import json
import logging
import urllib2
from datetime import datetime, timedelta
import sys
import re

# Scraper modules
from scraper.model import MenuScrape
from scraper.util import flatten_menu_scrape
import stout
import ball_and_chain

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)

# Root cache directory
cache_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'menu_cache')


def scrape_location(location, scraper):
    """
    Scrape all beverages from a location.

    :param location: Location to scrape
    :type location: Location
    :param scraper: Scraper to use
    :type scraper: base.Scraper
    :return:
    :rtype:
    """
    _log('Scraping {0} - {1}'.format(location.name, location.url), logging.INFO)
    menu_scrape = MenuScrape(location, location.url, datetime.now())
    menu_html = urllib2.urlopen(location.url).read()
    if menu_html:
        _log('Read {0} bytes'.format(len(menu_html)), logging.INFO)
        menu_scrape.beverages = scraper.scrape(menu_html)
        cache_menu(menu_scrape)
    else:
        _log('Unable to retrieve menu from {0}'.format(location.url), logging.ERROR)


def cache_menu(menu_scrape):
    """
    Cache the scraped menu data on the filesystem.

    :param menu_scrape: Scraped menu.
    :type menu_scrape: MenuScrape
    :return: Path to the cached file.
    :rtype: str
    """
    # Name files menu_YYYY-MM-DD_location.json
    file_path = _build_cache_path(menu_scrape.location.name, time=menu_scrape.date)
    # Organize cache into directories by location/year/month
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Write file
    with open(file_path, 'w') as fh:
        fh.write(json.dumps(flatten_menu_scrape(menu_scrape)))
    return file_path


def get_cache_near(location, time, lean='new'):
    cache_path = _build_cache_path(location, time=time)
    i = 0
    while not os.path.exists(cache_path):
        i += 1
        if lean == 'new':
            time = time + timedelta(days=1)
        else:
            time = time - timedelta(days=1)
        cache_path = _build_cache_path(location, time=time)
        if i > 100:
            # Unable to find nearby cache, return oldest/newest
            return get_cache_extreme(location, lean)
    return json.load(open(cache_path))


def get_cache_extreme(location, extreme='new'):
    location = _safe_location(location)
    year = min(os.listdir(cache_root))
    year_dir = os.path.join(cache_root, year)
    month = min(os.listdir(year_dir))
    month_dir = os.path.join(year_dir, month)
    regex = re.compile('.*[0-9]{4}-[0-9]{2}-([0-9]{2})_' + location + '.json')
    days = []
    for menu_file in os.listdir(month_dir):
        matches = regex.match(menu_file)
        if matches:
            days.append(matches.group(1))
    if extreme == 'new':
        day = max(days)
    else:
        day = min(days)
    return get_cache(location=location, year=year, month=month, day=day)


def get_cache(name=None, location=None, time=None, year=None, month=None, day=None):
    if name:
        regex = re.compile('.*([0-9]{4})-([0-9]{2})-([0-9]{2})_(.*)')
        matches = regex.match(name)
        cache_path = _build_cache_path(matches.group(4), year=matches.group(1), month=matches.group(2),
                                       day=matches.group(3))
    else:
        if time:
            cache_path = _build_cache_path(location=location, time=time)
        else:
            cache_path = _build_cache_path(location=location, year=year, month=month, day=day)

    return json.load(open(cache_path))


def _build_cache_path(location, year=None, month=None, day=None, time=None):
    location = _safe_location(location)
    if time:
        _dir = os.path.join(time.strftime('%Y'), time.strftime('%m'))
        filename = 'menu_{0}_{1}.json'.format(time.strftime('%Y-%m-%d'), location)
    else:
        _dir = os.path.join(year, month)
        filename = 'menu_{0}-{1}-{2}_{3}.json'.format(year, month, day, location)
    return os.path.join(cache_root, _dir, filename)


def _safe_location(location):
    return location.replace(' ', '_').lower()


def _log(message, level=logging.INFO):
    root_log.log(level, message)


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Stout
    for loc in stout.locations:
        scrape_location(loc, stout.Scraper())

    # Ball and Chain
    for loc in ball_and_chain.locations:
        scrape_location(loc, ball_and_chain.Scraper())
