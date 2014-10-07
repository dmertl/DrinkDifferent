import argparse
import json
import logging
import re
import urllib2
import sys
from abc import abstractmethod
# TODO: Migrate to beautiful soup
from lxml.html import fromstring
from unidecode import unidecode
from scraper.model import Location, Beverage
from scraper.util import url_from_arg, flatten_beverages
import base

root_log = logging.getLogger()
root_log.setLevel(logging.WARN)

locations = [
    Location('Hollywood', 'http://www.stoutburgersandbeers.com/hollywood-beer-menu/', 'Stout'),
    Location('Studio City', 'http://www.stoutburgersandbeers.com/studio-city-beer-menu/', 'Stout'),
    Location('Santa Monica', 'http://www.stoutburgersandbeers.com/santa-monica-beer-menu/', 'Stout'),
]

# TODO: Move old code into Scraper
class Scraper(base.Scraper):
    def scrape(self, html):
        return parse_menu(html)


class ParsingException(Exception):
    pass


class ExtractionException(ParsingException):
    pass


def parse_menu(html):
    return parse_sections(html)


def parse_sections(html):
    """

    :param html: Stout menu web page HTML
    :type html: str
    :return:
    :rtype: dict
    """
    beverages = []
    # TODO: remove section shit
    parsed_sections = []

    tree = fromstring(html)

    # Find menu element
    beer_menu = tree.xpath('//div[@id="second-menu"]')
    if beer_menu:
        beer_menu = beer_menu[0]

        # Find all headers and sections in the menu
        menu_headers = beer_menu.xpath('.//header')
        menu_sections = beer_menu.xpath('.//section')

        _log('Found {0} headers and {1} sections in menu.'.format(len(menu_headers), len(menu_sections)), logging.INFO)

        if len(menu_headers) != len(menu_sections):
            _log('Number of headers {0} does not match number of sections {1}'
                 .format(len(menu_headers), len(menu_sections)), logging.WARN)

        section_count = 0
        # Header does not contain section, but they should match up sequentially
        for header_element, section_element in zip(menu_headers, menu_sections):
            section_count += 1
            try:
                section = _parse_section(header_element, section_element, section_count)
                if section:
                    beverages += section['beverages']
            except ParsingException as e:
                _log(str(e), logging.WARN)
    else:
        _log('Unable to find "div#second-menu" when parsing menu.', logging.ERROR)
        raise ParsingException('Unable to find "div#second-menu" when parsing menu.')

    return beverages


def _parse_section(header_element, section_element, section_count):
    """
    Parse a menu header and section element into a section dict.

    :param header_element:
    :type header_element: etree.Element
    :param section_element:
    :type section_element: etree.Element
    :param section_count:
    :type section_count: int
    :return:
    :rtype: dict
    """
    # H2 inside the header has the section name
    name = header_element.xpath('.//h2')
    if name:
        name = name[0].text_content().strip()
        if not 'Wine' in name:
            _log('Parsing section {0} "{1}".'.format(section_count, name))
            section = {
                'name': name,
                'type': 'wine' if 'Wine' in name else 'beer',
                'beverages': []
            }

            # Find all article elements inside the section
            beverage_elements = section_element.xpath('.//article')
            _log('Found {0} beverages.'.format(len(beverage_elements)))
            beverage_count = 0
            for beverage_element in beverage_elements:
                beverage_count += 1
                try:
                    beverage = _parse_beverage(beverage_element, section['type'] == 'wine', beverage_count, section_count)
                    _log('Parsed beverage {0} "{1}".'.format(beverage_count, beverage.name))
                    # _log('Parsed beverage {0} "{1}".'.format(beverage_count, beverage['name']))
                    section['beverages'].append(beverage)
                except ParsingException as e:
                    _log(str(e), logging.DEBUG)
            return section
        else:
            return None
    else:
        raise ParsingException('Unable to find "h2" in header {0}'.format(section_count))


def _parse_beverage(beverage_element, is_wine, beverage_count, section_count):
    """
    Parse a beverage element into an item.

    :param beverage_element:
    :type beverage_element: etree.Element
    :param beverage_count:
    :type beverage_count: int
    :param section_count:
    :type section_count: int
    :return:
    :rtype: Beverage
    """
    # .title element contains the beverage name
    name = beverage_element.xpath('.//p[@class="title"]')
    if name:
        name = name[0].text_content().strip()
        if name:
            try:
                parser = BeerParser()
                return parser.parse(name)
            except ParsingException as e:
                _log(str(e), logging.DEBUG)
        else:
            raise ParsingException('Empty beverage in section {0} item {1}'.format(section_count, beverage_count))
    else:
        raise ParsingException(
            'Unable to find "p.title" in section {0} item {1}.'.format(section_count, beverage_count))


class BeerParser(object):
    def __init__(self):
        self.extractors = [
            VolumeExtractor(),
            AbvExtractor(),
            PriceExtractor(),
            NameBreweryExtractor(),
            LocationStyleExtractor()
        ]

    def parse(self, value):
        """
        Parse a beverage string into a Beverage.

        TODO: Support conditional extractors. If extract X fails, run extractor Y.
        :param value:
        :type value: str|unicode
        :return:
        :rtype: Beverage
        """
        beverage = Beverage()
        beverage.type = 'Beer'
        beverage.scraped_value = value
        value = self.prep(value)
        for extractor in self.extractors:
            try:
                data = extractor.extract(self.clean(value))
                value = data.get('__value')
                del data['__value']
                for k, v in data.iteritems():
                    beverage.__setattr__(k, v)
            except ExtractionException as e:
                _log(str(e), logging.DEBUG)
                pass
        if beverage.name:
            beverage.availability = 'Bottle' if beverage.volume else 'On Tap'
            return beverage
        else:
            raise ParsingException()

    def clean(self, value):
        """
        Remove any extraction artifacts.

        :param value:
        :type value: str
        :return:
        :rtype: str
        """
        return re.sub('/[\s/]+/', '/', value)

    def prep(self, value):
        """
        Prepare beverage string before any extraction is done. Helps with edge cases.

        :param value:
        :type value: str
        :return:
        :rtype: str
        """
        # Convert any fancy unicode characters to more common ascii equivalents
        if type(value) is unicode:
            value = unidecode(value)
        # Handle some troublesome strings
        return value.replace('w/', 'with ')\
            .replace('IPAw / ', 'IPA with ')\
            .replace('Weihenstephaner Original - Germ', 'Weihenstephaner Original - Weihenstephan / Germ')


class Extractor(object):
    @abstractmethod
    def extract(self, value):
        """
        Extract beverage data from a string. Returned dictionary has keys corresponding to Beverage variables. Includes
        an extra '__value' key that holds the value after the extracted data is removed. Helpful when leaving data
        could confuse further parsing.

        :param value: Beverage string.
        :type value: str
        :return: Extracted beverage data.
        :rtype: dict
        """
        pass


class VolumeExtractor(Extractor):
    def extract(self, value):
        """
        Extract volume by searching for "<number><units>".
        """
        search = re.search('(([0-9\.]+)(oz|ml))', value)
        if search and len(search.groups()) == 3:
            try:
                return {
                    '__value': value.replace(search.group(1), ''),
                    'volume': float(search.group(2)),
                    'volume_units': search.group(3)
                }
            except ValueError:
                raise ExtractionException(
                    'Unable to convert volume to float. volume={}, value={}'.format(search.group(2), value))
        raise ExtractionException('Unable to extract volume. value={}'.format(value))


class AbvExtractor(Extractor):
    def extract(self, value):
        """
        Extract ABV by searching for "<number>%".
        """
        search = re.search('(([0-9\.]+)%)', value)
        if search and len(search.groups()) == 2:
            try:
                return {
                    '__value': value.replace(search.group(1), ''),
                    'abv': float(search.group(2))
                }
            except ValueError:
                raise ExtractionException(
                    'Unable to convert abv to float. volume={}, value={}'.format(search.group(2), value))
        raise ExtractionException('Unable to extract abv. value={}'.format(value))


class PriceExtractor(Extractor):
    def extract(self, value):
        """
        Extract price by searching for "$<number>".
        """
        search = re.search('(\$([0-9\.]+))', value)
        if search and len(search.groups()) == 2:
            try:
                return {
                    '__value': value.replace(search.group(1), ''),
                    'price': float(search.group(2))
                }
            except ValueError:
                raise ExtractionException(
                    'Unable to convert price to float. volume={}, value={}'.format(search.group(2), value))
        raise ExtractionException('Unable to extract price. value={}'.format(value))


class NameBreweryExtractor(Extractor):
    def extract(self, value):
        """
        Extract name and brewery by searching the start of the string for "<name> - <brewery>".
        """
        search = re.search('(^([^-]+)-([^/]+)/)', value)
        if search and len(search.groups()) == 3:
            return {
                '__value': value.replace(search.group(1), ''),
                'name': search.group(2).strip(),
                'brewery': search.group(3).strip()
            }
        else:
            search = re.search('(^([^/]+)/)', value)
            if search and len(search.groups()) == 2:
                return {
                    '__value': value.replace(search.group(1), ''),
                    'name': search.group(2).strip()
                }
        raise ExtractionException('Unable to extract name or brewery. value={}'.format(value))


class LocationStyleExtractor(Extractor):
    def extract(self, value):
        """
        Extract location and style by searching the start of the string for "<location> / <style>". Requires that other
        data has been removed as location and style are not easily parsable.
        """
        search = re.search('(^([^/]+)/([^/]+))', value)
        if search and len(search.groups()) == 3:
            return {
                '__value': value.replace(search.group(1), ''),
                'location': search.group(2).strip(),
                'style': search.group(3).strip()
            }
        raise ExtractionException('Unable to extract location or style. value={}'.format(value))


def _log(message, level=logging.INFO):
    root_log.log(level, message)


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Command line arguments
    parser = argparse.ArgumentParser(description='Parse http://www.stoutburgersandbeers.com/ beer menu into JSON.')
    parser.add_argument('filename', type=str, help='file path or URL to beverage menu')
    parser.add_argument('--pretty', action='store_true', help='pretty print JSON output')
    args = parser.parse_args()

    # Run scraper
    url = url_from_arg(args.filename, locations)
    contents = urllib2.urlopen(url).read()
    beverages = parse_menu(contents)
    beverages_flat = flatten_beverages(beverages)

    # Output beverage data as JSON
    if args.pretty:
        print json.dumps(beverages_flat, indent=2)
    else:
        print json.dumps(beverages_flat)
