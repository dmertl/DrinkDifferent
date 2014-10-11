"""
Upgrades v1 cache files to v2.

File naming change:
- Remove "menu_"
- Include chain name
- Location names use "-" as separator instead of "_"
menu_2014-09-08_santa_monica.json = 2014-09-08_stout_santa-monica.json

File format change:
- Remove sections, just list beverages
- Location object instead of string
- Add URL metadata
- Changed "parsed" to "date"
"""

import argparse
import os
import json
import logging
import urllib2
import sys
import re
import dateutil.parser
from datetime import datetime

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)

# Copy of old model.py

data_version = '2.0.0'


class Beverage(object):
    def __init__(self, name=None):
        # Beverage name
        self.name = name
        # Brewery/Winery name
        self.brewery = None
        # Beer or Wine
        self.type = None
        # Beer style, IPA, Lager, etc.
        self.style = None
        # Brewery location
        self.location = None
        # ABV
        self.abv = None
        # Year
        self.year = None
        # Description
        self.description = None
        # On Tap or Bottle
        self.availability = None
        # Price
        self.price = None
        # Bottle volume dimension
        self.volume = None
        # Bottle volume units
        self.volume_units = None
        # Untappd beer ID
        self.untappd_id = None
        # Untappd brewery ID
        self.untappd_brewery_id = None
        # Beverage info as scraped (prior to parsing)
        self.scraped_value = None

    def __eq__(self, other):
        if self.untappd_id and other.untappd_id:
            return self.untappd_id == other.untappd_id
        else:
            return self.name == other.name

    def __hash__(self):
        return hash(str(self.untappd_id) + str(self.name))


class Location(object):
    def __init__(self, name=None, url=None, chain=None):
        # Location name
        self.name = name
        # Beverage menu URL
        self.url = url
        # Chain name
        self.chain = chain


class MenuScrape(object):
    def __init__(self, location=None, url=None, date=None, beverages=None, version=data_version):
        # Location scraped
        self.location = location
        # URL scraped
        self.url = url
        # Date of scraping
        self.date = date or datetime.now
        # Beverages found
        self.beverages = beverages or []
        # Data format version number
        self.version = version


# End copy of old model.py

# Copy of stout locations
stout_locations = [
    Location('Hollywood', 'http://www.stoutburgersandbeers.com/hollywood-beer-menu/', 'Stout'),
    Location('Studio City', 'http://www.stoutburgersandbeers.com/studio-city-beer-menu/', 'Stout'),
    Location('Santa Monica', 'http://www.stoutburgersandbeers.com/santa-monica-beer-menu/', 'Stout'),
]

# Copy of old util


def flatten_menu_scrape(menu_scrape):
    """
    Convert a MenuScrape into a flat format that can easily be dumped to JSON.

    :param menu_scrape: MenuScrape
    :type menu_scrape: MenuScrape
    :return:
    :rtype: dict
    """
    return {
        'location': flatten_location(menu_scrape.location),
        'url': menu_scrape.url,
        'date': menu_scrape.date.isoformat() if menu_scrape.date else None,
        'beverages': flatten_beverages(menu_scrape.beverages),
        'version': menu_scrape.version
    }


def flatten_location(location):
    """
    Flatten a Location into a dict that can be easily converted to JSON.

    :param location: Location.
    :type location: Location
    :return: Dict.
    :rtype: dict
    """
    return location.__dict__.copy()


def flatten_beverages(beverages):
    """
    Convert a list of beverages into a flat format that can easily be dumped to JSON.

    :param beverages:
    :type beverages: Beverage[]
    :return:
    :rtype: dict[]
    """
    flat = []
    for beverage in beverages:
        flat.append(
            dict((k, v) for k, v in beverage.__dict__.iteritems() if v)
        )
    return flat

# End copy of old util

def upgrade_filename(old_filename):
    """
    Upgrade a filename from v1 to v2. Assumes chain is "stout".

    :param old_filename:
    :type old_filename: str
    :return:
    :rtype: str
    """
    # Remove "menu_"
    no_menu = old_filename.replace('menu_', '')
    # Separate date
    date = no_menu[:no_menu.index('_')]
    # Separate location, replace all "_" with "-" in location name
    location = no_menu[no_menu.index('_') + 1:].replace('.json', '').replace('_', '-')
    # Re-combine with chain name
    return '{}_stout_{}.json'.format(date, location)


def upgrade_content(content):
    """
    Upgrade file content from v1 to v2. Assumes data is in old stout format.

    :param content:
    :type content: str
    :return:
    :rtype: str
    """
    data = json.loads(content)
    # Convert sections into simple beverages list
    beverages = []
    for section in data.get('sections'):
        for old_bev in section.get('beverages'):
            if old_bev.get('name'):
                beverage = Beverage()
                # Old stout scraping saved the pre-parsed beverage title under 'name'
                beverage.scraped_value = old_bev.get('name')
                details = old_bev.get('details')
                if details:
                    beverage.name = details.get('name') or None
                    beverage.style = details.get('style') or None
                    try:
                        beverage.price = float(details.get('price').replace('$', '')) if details.get('price') else None
                    except ValueError:
                        pass
                    try:
                        beverage.abv = float(details.get('alcohol_percentage').replace('%', '')) if details.get(
                            'alcohol_percentage') else None
                    except ValueError:
                        pass
                    beverage.location = details.get('location') or None
                    if details.get('type') in ['beer', 'wine']:
                        beverage.type = details.get('type').title() if details.get('type') else None
                    if details.get('brewery'):
                        beverage.brewery = details.get('brewery')
                    elif details.get('winery'):
                        beverage.brewery = details.get('winery')
                    if details.get('size'):
                        match = re.match('([0-9]+)([a-zA-Z]+)', details.get('size'))
                        if match and len(match.groups()) == 2:
                            try:
                                beverage.volume = float(match.group(1))
                                beverage.volume_units = match.group(2)
                            except ValueError:
                                pass
                        beverage.availability = 'Bottle'
                    else:
                        beverage.availability = 'On Tap'
                    beverage.year = details.get('year') or None
                beverages.append(beverage)
    # Find location by name
    location = Location('Unknown', '', 'Stout')
    if data.get('location'):
        found = [x for x in stout_locations if x.name == data.get('location')]
        if found:
            location = found[0]
    # Get date
    date = None
    if data.get('parsed'):
        date = dateutil.parser.parse(data.get('parsed'))
    # Build MenuScrape
    menu_scrape = MenuScrape(location, location.url, date, beverages)
    return json.dumps(flatten_menu_scrape(menu_scrape))


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Command line arguments
    parser = argparse.ArgumentParser(description='Upgrade cache files from v1 to v2.')

    root_dir = cache_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'menu_cache')
    root_log.debug('Upgrading root dir {}'.format(root_dir))
    for year in os.listdir(root_dir):
        year_dir = os.path.join(root_dir, year)
        if not os.path.isdir(year_dir):
            continue
        root_log.debug('Upgrading year dir {}'.format(year_dir))
        for month in os.listdir(year_dir):
            month_dir = os.path.join(year_dir, month)
            if not os.path.isdir(month_dir):
                continue
            root_log.debug('Upgrading month dir {}'.format(month_dir))
            for filename in os.listdir(month_dir):
                if not filename.endswith('.json'):
                    continue
                file_path = os.path.join(month_dir, filename)
                if filename.startswith('menu_'):
                    root_log.debug('Found v1 file {}'.format(file_path))
                    new_filename = upgrade_filename(filename)
                    new_file_path = os.path.join(month_dir, new_filename)
                    old_content = urllib2.urlopen('file:{0}'.format(urllib2.quote(os.path.abspath(file_path)))).read()
                    new_content = upgrade_content(old_content)
                    with open(new_file_path, 'w') as fh:
                        fh.write(new_content)
                    os.remove(file_path)
                    root_log.info('Upgraded cache file {} to v2'.format(file_path))
                else:
                    root_log.debug('Ignoring v2 file {}'.format(filename))
