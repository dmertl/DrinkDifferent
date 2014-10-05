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
from scraper.model import Beverage, Location, MenuScrape
import scraper.cache
from scraper.util import flatten_menu_scrape
import scraper.stout

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)


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
        found = [x for x in scraper.stout.locations if x.name == data.get('location')]
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

    root_dir = scraper.cache.cache_root
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
