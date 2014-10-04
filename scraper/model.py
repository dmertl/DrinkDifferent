__author__ = 'dmertl'


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


class Location(object):
    def __init__(self, name=None, url=None, chain=None):
        # Location name
        self.name = name
        # Beverage menu URL
        self.url = None
        # Chain name
        self.chain = None
