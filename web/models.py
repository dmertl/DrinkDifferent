from web import db
from datetime import datetime

menu_scrape_beverage_table = db.Table('menu_scrape_beverage', db.metadata,
                                      db.Column('menu_scrape_id', db.Integer, db.ForeignKey('menu_scrape.id')),
                                      db.Column('beverage_id', db.Integer, db.ForeignKey('beverage.id')))


class MenuScrape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(128))
    created = db.Column(db.DateTime)

    beverages = db.relationship('Beverage', secondary=menu_scrape_beverage_table, backref='menu_scrapes')

    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))

    def __init__(self, location=None, url=None, beverages=None, created=None):
        self.location = location
        self.url = url
        if beverages:
            self.beverages = beverages
        self.created = created or datetime.now()

    def __repr__(self):
        return '<MenuScrape {}-{}>'.format(self.location_id, self.created)


class Beverage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    brewery = db.Column(db.String(128))
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

    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))

    def __init__(self, name=None, brewery=None, type='Beer', style=None, abv=None, year=None, description=None,
                 availability=None, price=None, volume=None, volume_units=None, untappd_id=None,
                 untappd_brewery_id=None, scraped_value=None, created=None, is_active=True):
        self.name = name
        self.brewery = brewery
        self.type = type
        self.style = style
        self.abv = abv
        self.year = year
        self.description = description
        self.availability = availability
        self.price = price
        self.volume = volume
        self.volume_units = volume_units
        self.untappd_id = untappd_id
        self.untappd_brewery_id = untappd_brewery_id
        self.scraped_value = scraped_value
        self.created = created or datetime.now()
        self.is_active = is_active

    def __repr__(self):
        return '<Beverage {}>'.format(self.name)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    url = db.Column(db.String(128))
    untappd_id = db.Column(db.String(128))
    created = db.Column(db.DateTime)

    chain_id = db.Column(db.Integer, db.ForeignKey('chain.id'))

    beverages = db.relationship('Beverage', backref='location')

    menu_scrapes = db.relationship('MenuScrape', backref='location')

    def __init__(self, name=None, url=None, chain=None, untappd_id=None, created=None):
        self.name = name
        self.url = url
        self.chain = chain
        self.untappd_id = untappd_id
        self.created = created or datetime.now()

    def __repr__(self):
        return '<Location {}>'.format(self.name)


class Chain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    created = db.Column(db.DateTime)

    locations = db.relationship('Location', backref='chain')

    def __init__(self, name=None, created=None):
        self.name = name
        self.created = created or datetime.now()

    def __repr__(self):
        return '<Chain {}>'.format(self.name)
