from abc import abstractmethod
from datetime import datetime


class Scraper(object):
    @abstractmethod
    def scrape(self, html):
        """
        Scrape all beverages from web page HTML.

        :param html: HTML of web page.
        :type html: str
        :return: Beverages scraped.
        :rtype: Beverage[]
        """


class ScrapedBeverage(object):
    """
    Beverage scrape data, removing complex model relationships from web/models
    """

    def __init__(self, name=None, brewery=None, brewery_location=None, type='Beer', style=None, abv=None, year=None,
                 description=None, availability=None, price=None, volume=None, volume_units=None, scraped_value=None,
                 created=None):
        self.name = name
        self.brewery = brewery
        self.brewery_location = brewery_location
        self.type = type
        self.style = style
        self.abv = abv
        self.year = year
        self.description = description
        self.availability = availability
        self.price = price
        self.volume = volume
        self.volume_units = volume_units
        self.scraped_value = scraped_value
        self.created = created or datetime.now()

    def flatten(self):
        return {
            'name': self.name,
            'type': self.type,
            'brewery': self.brewery,
            'brewery_location': self.brewery_location,
            'style': self.style,
            'abv': self.abv,
            'description': self.description,
            'availability': self.availability,
            'price': self.price,
            'volume': self.volume,
            'volume_units': self.volume_units,
            'created': self.created.isoformat(),
        }
