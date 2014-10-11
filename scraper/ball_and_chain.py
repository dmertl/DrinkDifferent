import logging
import argparse
import sys
import urllib2
import json
import base
import re
from bs4 import BeautifulSoup
from scraper.util import flatten_beverages, url_from_arg
from unidecode import unidecode
from web.models import Chain, Beverage

root_log = logging.getLogger()
root_log.setLevel(logging.DEBUG)

# Ball and Chain locations
chain = Chain.query.filter_by(name='Ball and Chain').first()
locations = chain.locations


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
                beverage = Beverage(type='Beer', availability='On Tap', is_active=True)
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
                # Format is a CSV of "beer $cost, beer $cost" but sometimes they mess up their commas
                bevs = re.findall('([^,$]+),?\s*\$+([0-9.]+)', element.string)
                for bev in bevs:
                    if len(bev) == 2:
                        name = bev[0].strip()
                        if type(name) is unicode:
                            name = unidecode(name)
                        try:
                            price = float(bev[1])
                        except ValueError:
                            root_log.warn('Unable to convert price into float. price={}'.format(bev[1]))
                            price = None
                        beverage = Beverage(name=name, price=price, type=current_type, availability='Bottle',
                                            is_active=True)
                        beverages.append(beverage)
                    else:
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
