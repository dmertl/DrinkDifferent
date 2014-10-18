"""
Split Beverage table into Beverage and BeverageScrape. Separates the scraping (temporal) from the actual beverage.
Beverage table will be renamed to BeverageScrape. Beverage table created with similar columns. Move all unique
BeverageScrapes to Beverages table. Then drop unnecessary columns from BeverageScrape.
"""

import argparse
import logging
import sys
import dateutil.parser
from web.models import MenuScrape, Beverage, Location, BeverageScrape, Brewery
from web import db

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)


class OldBeverage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    brewery = db.Column(db.String(128))
    brewery_location = db.Column(db.String(128))
    type = db.Column(db.String(32))
    style = db.Column(db.String(128))
    abv = db.Column(db.Numeric(5, 2))
    year = db.Column(db.Integer)
    description = db.Column(db.String(255))
    availability = db.Column(db.String(32))
    price = db.Column(db.Numeric(5, 2))
    volume = db.Column(db.Numeric(5, 2))
    volume_units = db.Column(db.String(32))
    untappd_id = db.Column(db.String(128))
    untappd_brewery_id = db.Column(db.String(128))
    scraped_value = db.Column(db.String(128))
    created = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean)
    location_id = db.Column(db.Integer)
    menu_scrape_id = db.Column(db.Integer)

    def flatten(self):
        return {
            'id': self.id,
            'name': self.name,
            'brewery': self.brewery,
            'brewery_location': self.brewery_location,
            'type': self.type,
            'style': self.style,
            'abv': self.abv,
            'year': self.year,
            'description': self.description,
            'availability': self.availability,
            'price': self.price,
            'volume': self.volume,
            'volume_units': self.volume_units,
            'untappd_id': self.untappd_id,
            'untappd_brewery_id': self.untappd_brewery_id,
            'scraped_value': self.scraped_value,
            'created': self.created.isoformat(),
            'is_active': self.is_active,
            'location_id': self.location_id,
            'menu_scrape_id': self.menu_scrape_id,
        }


def split():
    # Save copy of old scraped beverage data
    db.engine.execute('ALTER TABLE beverage RENAME TO old_beverage')
    # Create tables for new models
    db.create_all()
    # Cache
    locations = {}
    menu_scrapes = {}
    breweries = {}
    beverages = {}
    # Convert old scraped beverage data to new style
    old_scrapes = OldBeverage.query.all()
    cnt = 0
    for scrape in old_scrapes:
        scrape = scrape.flatten()
        location = locations.get(scrape['location_id'])
        if not location:
            location = Location.query.get(scrape['location_id'])
            locations[location.id] = location
        menu_scrape = menu_scrapes.get(scrape['menu_scrape_id'])
        if not menu_scrape:
            menu_scrape = MenuScrape.query.get(scrape['menu_scrape_id'])
            menu_scrapes[menu_scrape.id] = menu_scrape
        brewery = breweries.get(scrape['brewery'])
        if not brewery:
            brewery = Brewery(name=scrape['brewery'], location=scrape['brewery_location'],
                              untappd_id=scrape['untappd_id'])
            breweries[brewery.name] = brewery
            db.session.add(brewery)
        beverage = beverages.get('{}{}'.format(scrape['name'], scrape['brewery']))
        if not beverage:
            beverage = Beverage.query.filter_by(name=scrape['name'], brewery=brewery).first()
            beverages['{}{}'.format(scrape['name'], scrape['brewery'])] = beverage
        if not beverage:
            beverage = Beverage(name=scrape['name'], brewery=brewery, type=scrape['type'], style=scrape['style'],
                                abv=scrape['abv'], year=scrape['year'], description=scrape['description'],
                                availability=scrape['availability'], price=scrape['price'], volume=scrape['volume'],
                                volume_units=scrape['volume_units'], untappd_id=scrape['untappd_id'],
                                created=dateutil.parser.parse(scrape['created']), is_active=False, location=location,
                                beverage_scrapes=[])
            db.session.add(beverage)
        beverage_scrape = BeverageScrape(beverage=beverage, location=location, menu_scrape=menu_scrape,
                                         scraped_value=scrape['scraped_value'],
                                         created=dateutil.parser.parse(scrape['created']))
        db.session.add(beverage_scrape)
        cnt += 1
        if cnt % 100 == 0:
            db.session.commit()
    db.session.commit()
    db.engine.execute('DROP TABLE old_beverage')


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Command line arguments
    parser = argparse.ArgumentParser(description='Split beverage into scrapes, beverages, and brewery.')

    split()
