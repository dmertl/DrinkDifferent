import argparse
import os
import json
import logging
import urllib2
import sys
from scraper.util import expand_menu_scrape, flatten_beverages

root_log = logging.getLogger()
root_log.setLevel(logging.WARN)


class DiffException(Exception):
    pass


def diff_beverages(old_beverages, new_beverages):
    """
    Return the difference in beverages between an old list and a new list.

    :param old_beverages: Old beverage list.
    :type old_beverages: Beverage[]
    :param new_beverages: New beverage list.
    :type new_beverages: Beverage[]
    :return: List of added, removed Beverages
    :rtype: Beverage[], Beverage[]
    """
    unchanged = set(old_beverages).intersection(new_beverages)
    removed = set(old_beverages).symmetric_difference(unchanged)
    added = set(new_beverages).symmetric_difference(unchanged)
    return added, removed


def _log(message, level=logging.INFO):
    root_log.log(level, message)


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Command line arguments
    parser = argparse.ArgumentParser(description='Find beverages that were added or removed between menu scrapings.')
    parser.add_argument('old', type=str, help='path to old menu scraping file')
    parser.add_argument('new', type=str, help='path to new menu scraping file')
    parser.add_argument('--pretty', action='store_true', help='pretty print JSON output')
    args = parser.parse_args()

    # Load menus
    old = expand_menu_scrape(
        json.loads(
            urllib2.urlopen('file:{0}'.format(urllib2.quote(os.path.abspath(args.old)))).read()
        )
    )
    new = expand_menu_scrape(
        json.loads(
            urllib2.urlopen('file:{0}'.format(urllib2.quote(os.path.abspath(args.new)))).read()
        )
    )

    # Find differences in beverages
    added, removed = diff_beverages(old.beverages, new.beverages)
    flat = {
        'old_date': old.date.isoformat(),
        'new_date': new.date.isoformat(),
        'added': flatten_beverages(added),
        'removed': flatten_beverages(removed)
    }

    # Output diff as JSON
    if args.pretty:
        print json.dumps(flat, indent=2)
    else:
        print json.dumps(flat)
