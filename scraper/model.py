__author__ = 'dmertl'

from datetime import datetime

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
        # TODO: This isn't really unique and may be problematic, but it makes intersection() work
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
