"""
Moves old menu cache files to sqlite database.

Each cache file becomes a MenuScrape. Each beverage becomes a Beverage.
"""

import argparse
import os
import json
import logging
import sys
import dateutil.parser
import scraper.cache
import scraper.stout
from web.models import MenuScrape, Beverage, Location
from web import db

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)

# Location reference
locations = Location.query.all()


def to_database(json_data, filename):
    """
    Insert menu scrap cache data into the database.

    :param json_data:
    :type json_data: dict
    :param filename:
    :type filename: str
    :return:
    :rtype:
    """
    menu_scrape = create_menu_scrape(json_data, filename)
    db.session.add(menu_scrape)
    # Beverages
    beverages = []
    for json_beverage in json_data.get('beverages'):
        beverage = create_beverage(json_beverage)
        beverage.created = menu_scrape.created
        beverage.location = menu_scrape.location
        beverages.append(beverage)
        db.session.add(beverage)
    menu_scrape.beverages = beverages
    db.session.commit()
    return menu_scrape


def create_menu_scrape(json_data, filename):
    """

    :param json_data:
    :type json_data: dict
    :param filename:
    :type filename: str
    :return:
    :rtype: MenuScrape
    """
    menu_scrape = MenuScrape()
    # Scraped date
    if 'date' in json_data:
        menu_scrape.created = dateutil.parser.parse(json_data.get('date'))
    else:
        root_log.warn('No parsed timestamp found in menu cache. filename={}'.format(filename))
    # Location
    if 'location' in json_data:
        json_location = json_data.get('location')
        if 'name' in json_location and 'chain' in json_location:
            for location in locations:
                if location.name == json_location.get('name') and location.chain.name == json_location.get('chain'):
                    menu_scrape.location = location
                    break
            if not menu_scrape.location:
                root_log.warn('Unable to find matching location in database. name={}, chain={}, filename={}'
                              .format(json_location.get('name', json_location.get('chain'), filename)))
        else:
            root_log.warn('Missing "name" or "chain" from location in cache file. filename={}'.format(filename))
    else:
        root_log.warn('Missing "location" from cache file. filename={}'.format(filename))
    return menu_scrape


def create_beverage(json_beverage):
    """

    :param json_beverage:
    :type json_beverage: dict
    :param filename:
    :type filename: str
    :return:
    :rtype: Beverage
    """
    beverage = Beverage()
    for field in ['name', 'brewery', 'type', 'style', 'abv', 'year', 'description', 'availability', 'price',
                  'volume', 'volume_units', 'scraped_value']:
        if field in json_beverage:
            beverage.__setattr__(field, json_beverage.get(field))
    if 'location' in json_beverage:
        beverage.brewery_location = json_beverage['location']
    return beverage


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Command line arguments
    parser = argparse.ArgumentParser(description='Move cache files to database.')

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
                root_log.debug('Upgrading file {}'.format(file_path))
                with file(file_path) as f:
                    json_data = json.load(f)
                menu_scrape = to_database(json_data, filename)
                root_log.info('Added cache file {} to the database. MenuScrape.id='.format(file_path, menu_scrape.id))
