import logging
import argparse
import os
import sys
import urllib2
import json
from bs4 import BeautifulSoup

root_log = logging.getLogger()
root_log.setLevel(logging.DEBUG)


class Scraper(object):
    def __init__(self):
        pass

    def scrape(self, url):
        if os.path.exists(url):
            return self.scrape_file(url)
        else:
            return self.scrape_url(url)

    def scrape_file(self, file):
        contents = urllib2.urlopen('file:{0}'.format(urllib2.quote(os.path.abspath(file)))).read()
        return self.scrape_html(contents)

    def scrape_url(self, url):
        contents = urllib2.urlopen(url).read()
        return self.scrape_html(contents)

    def scrape_html(self, html):
        beverages = []
        # Do a little cleanup to help BeautifulSoup parse correctly
        html = html.replace('</br />', '<br />')
        html = html.replace('<img src="images/chain.png" class="chain_rule">', '<img src="images/chain.png" class="chain_rule" />')
        parser = BeautifulSoup(html)
        beverages += self.scrape_on_tap(parser)
        beverages += self.scrape_bottles(parser)
        # TODO: Scrape wine list
        return beverages

    def scrape_on_tap(self, parser):
        beverages = []
        container = parser.find(id='on_tap_content')
        beverage = None
        for element in container:
            if element.name == 'h2':
                # Brewery - Name
                if beverage:
                    beverages.append(beverage)
                beverage = Beverage()
                beverage.type = 'Beer'
                beverage.availability = 'On Tap'
                pieces = element.string.split('-')
                if len(pieces) == 2:
                    company = pieces[0].strip()
                    name = pieces[1].strip()
                else:
                    root_log.warn('Unable to parse company and name from on tap beverage. string={0}'.format(element.string))
                    name = pieces[0].strip()
                    company = None
                beverage.name = name
                beverage.company = company
            elif element.name == 'h3':
                # Location
                beverage.location = element.string.strip()
            #TODO: <p> tag contains a description and the ABV if we can parse it
        if beverage:
            beverages.append(beverage)
        return beverages

    def scrape_bottles(self, parser):
        beverages = []
        container = parser.find(id='bottle_list_content')
        current_type = None
        for element in container:
            # Change beverage type based on h1 (everything below is of that type)
            if element.name == 'h1':
                if element.string == 'Bottled Beer':
                    current_type = 'Beer'
                elif element.string == 'Wine':
                    current_type = 'Wine'
                else:
                    current_type = None
                    root_log.warn('Unknown h1 in bottled beer list. string={0}'.format(element.string))
            elif element.name == 'p':
                # Basically a CSV of beer $cost
                #TODO: Why does this happen?
                if not element.string:
                    root_log.error('No string in {0}'.format(element))
                bevs = element.string.split(',')
                for bev in bevs:
                    pieces = bev.strip().split(' $')
                    if len(pieces) == 2:
                        name = pieces[0]
                        price = pieces[1].replace('$', '')
                        beverage = Beverage()
                        beverage.name = name
                        beverage.price = price
                        beverage.type = current_type
                        beverages.append(beverage)
                    else:
                        root_log.warn('Unable to parse name and cost from bottled beverage. string={0}'.format(bev))

        return beverages


class Beverage(object):
    def __init__(self):
        # Beverage name
        self.name = None
        # Brewery/Winery name
        self.company = None
        # Beer or Wine
        self.type = None
        # Beer style, IPA, Lager, etc.
        self.style = None
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


if __name__ == '__main__':
    # Command line arguments
    parser = argparse.ArgumentParser(description='Scrape')
    parser.add_argument('url', type=str, help='URL')
    parser.add_argument('--debug', action='store_true', help='include debug output')
    parser.add_argument('--pretty', action='store_true', help='pretty print JSON output')
    args = parser.parse_args()

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
    beverages = scraper.scrape(args.url)

    # Output beverage data as JSON
    beverages_dict = []
    for beverage in beverages:
        beverages_dict.append(beverage.__dict__)
    if args.pretty:
        print json.dumps(beverages_dict, indent=2)
    else:
        print json.dumps(beverages_dict)
