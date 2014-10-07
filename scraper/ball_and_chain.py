import logging
import argparse
import sys
import urllib2
import json
import base
from bs4 import BeautifulSoup
from model import Beverage, Location
from scraper.util import flatten_beverages, url_from_arg
from unidecode import unidecode

root_log = logging.getLogger()
root_log.setLevel(logging.DEBUG)

# Ball and Chain locations
locations = [
    Location('Hollywood', 'http://www.ball-and-chain-restaurant.com/', 'Ball and Chain')
]


class Scraper(base.Scraper):
    def __init__(self):
        pass

    def scrape(self, html):
        """

        :param html:
        :type html:
        :return:
        :rtype: Beverage[]
        """
        beverages = []
        # Do a little cleanup to help BeautifulSoup parse correctly
        html = html.replace('</br />', '<br />')
        html = html.replace('<img src="images/chain.png" class="chain_rule">',
                            '<img src="images/chain.png" class="chain_rule" />')
        parser = BeautifulSoup(html)
        beverages += self.scrape_on_tap(parser)
        beverages += self.scrape_bottles(parser)
        return beverages

    def scrape_on_tap(self, parser):
        beverages = []
        container = parser.find(id='on_tap_content')
        beverage = None
        for element in container:
            if element.name == 'h2':
                # h2 is Brewery - Name
                if beverage:
                    beverages.append(beverage)
                beverage = Beverage()
                beverage.type = 'Beer'
                beverage.availability = 'On Tap'
                pieces = element.text.split('-')
                if len(pieces) == 2:
                    brewery = pieces[0].strip()
                    name = pieces[1].strip()
                else:
                    root_log.warn(
                        'Unable to parse brewery and name from on tap beverage. string={0}'.format(element.string))
                    name = pieces[0].strip()
                    brewery = None
                if type(name) is unicode:
                    name = unidecode(name)
                beverage.name = name
                beverage.brewery = brewery
            elif element.name == 'h3':
                # h3 is Location
                beverage.location = element.string.strip()
        if beverage:
            beverages.append(beverage)
        return beverages

    def scrape_bottles(self, parser):
        beverages = []
        container = parser.find(id='bottle_list_content')
        current_type = None
        for element in container:
            if element.name == 'h1':
                # h1 indicates the beverage type for all the following beverages
                if element.string == 'Bottled Beer':
                    current_type = 'Beer'
                elif element.string == 'Wine':
                    current_type = 'Wine'
                else:
                    current_type = None
                    root_log.warn('Unknown h1 in bottled beer list. string={0}'.format(element.string))
            elif element.name == 'p':
                # Screw everything except beer
                if current_type != 'Beer':
                    continue
                # Format is a CSV of "beer $cost, beer $cost"
                # TODO: May be better to use regex to separate based on [^,$]+ $[0-9]+ should catch ones with missing commas
                # TODO: May also be able to catch extras commas, $ is consistent commas are not
                bevs = element.string.split(',')
                for bev in bevs:
                    pieces = bev.strip().split(' $')
                    if len(pieces) == 2:
                        name = pieces[0]
                        if type(name) is unicode:
                            name = unidecode(name)
                        price = float(pieces[1].replace('$', ''))
                        beverage = Beverage()
                        beverage.name = name
                        beverage.price = price
                        beverage.type = current_type
                        beverage.availability = 'Bottle'
                        beverages.append(beverage)
                    else:
                        # Usually this happens because they forget a comma
                        root_log.warn('Unable to parse name and cost from bottled beverage. string={0}'.format(bev))

        return beverages


if __name__ == '__main__':
    # Command line arguments
    argparser = argparse.ArgumentParser(description='Scrape')
    argparser.add_argument('url', type=str, help='URL')
    argparser.add_argument('--debug', action='store_true', help='include debug output')
    argparser.add_argument('--pretty', action='store_true', help='pretty print JSON output')
    args = argparser.parse_args()

    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    if args.debug:
        sh.setLevel(logging.DEBUG)
    else:
        sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Run scraper
    scraper = Scraper()
    url = url_from_arg(args.url, locations)
    contents = urllib2.urlopen(url).read()
    beverages = scraper.scrape(contents)
    beverages_flat = flatten_beverages(beverages)

    # Output beverage data as JSON
    if args.pretty:
        print json.dumps(beverages_flat, indent=2)
    else:
        print json.dumps(beverages_flat)
