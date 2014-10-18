from web import db
from datetime import datetime


class MenuScrape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(128))
    created = db.Column(db.DateTime)

    beverage_scrapes = db.relationship('BeverageScrape', backref='menu_scrape')

    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))

    def __init__(self, location=None, url=None, beverages=None, created=None):
        if location:
            self.location = location
        self.url = url
        if beverages:
            self.beverages = beverages
        self.created = created or datetime.now()

    def __repr__(self):
        return '<MenuScrape {}-{}>'.format(self.location_id, self.created)

    def flatten(self):
        return {
            'id': self.id,
            'url': self.url,
            'created': self.created.isoformat(),
            'location_id': self.location_id
        }


class BeverageScrape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scraped_value = db.Column(db.String(128))
    created = db.Column(db.DateTime)

    beverage_id = db.Column(db.Integer, db.ForeignKey('beverage.id'))

    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))

    menu_scrape_id = db.Column(db.Integer, db.ForeignKey('menu_scrape.id'))

    def __init__(self, beverage=None, location=None, menu_scrape=None, scraped_value=None, created=None):
        if beverage:
            self.beverage = beverage
        if location:
            self.location = location
        if menu_scrape:
            self.menu_scrape = menu_scrape
        self.scraped_value = scraped_value
        self.created = created or datetime.now()

    def __repr__(self):
        return '<BeverageScrape {}>'.format(self.scraped_value)

    def flatten(self):
        return {
            'id': self.id,
            'beverage_id': self.beverage_id,
            'location_id': self.location_id,
            'menu_scrape_id': self.menu_scrape_id,
            'scraped_value': self.scraped_value,
            'created': self.created.isoformat(),
        }


class Beverage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
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
    created = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean)

    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    brewery_id = db.Column(db.Integer, db.ForeignKey('brewery.id'))

    beverage_scrapes = db.relationship('BeverageScrape', backref='beverage')
    distinct_beers = db.relationship('DistinctBeer', backref='beverage')

    def __init__(self, name=None, brewery=None, type='Beer', style=None, abv=None, year=None, description=None,
                 availability=None, price=None, volume=None, volume_units=None, untappd_id=None, created=None,
                 is_active=True, location=None, beverage_scrapes=None, distinct_beers=None):
        self.name = name
        if brewery:
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
        self.created = created or datetime.now()
        self.is_active = is_active
        if location:
            self.location = location
        self.beverage_scrapes = beverage_scrapes or []
        self.distinct_beers = distinct_beers or []

    def __repr__(self):
        return '<Beverage {}>'.format(self.name)

    def flatten(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'style': self.style,
            'abv': self.abv,
            'description': self.description,
            'availability': self.availability,
            'price': self.price,
            'volume': self.volume,
            'volume_units': self.volume_units,
            'untappd_id': self.untappd_id,
            'created': self.created.isoformat(),
            'is_active': self.is_active,
            'location_id': self.location_id,
            'brewery_id': self.brewery_id,
        }


class Brewery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    location = db.Column(db.String(128))
    untappd_id = db.Column(db.String(128))

    beverages = db.relationship('Beverage', backref='brewery')

    def __init__(self, name=None, location=None, untappd_id=None):
        self.name = name
        self.location = location
        self.untappd_id = untappd_id

    def __repr__(self):
        return '<Brewery {}>'.format(self.name)

    def flatten(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'untappd_id': self.untappd_id
        }


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    url = db.Column(db.String(128))
    untappd_id = db.Column(db.String(128))
    created = db.Column(db.DateTime)

    chain_id = db.Column(db.Integer, db.ForeignKey('chain.id'))

    beverages = db.relationship('Beverage', backref='location')

    beverage_scrapes = db.relationship('BeverageScrape', backref='location')

    menu_scrapes = db.relationship('MenuScrape', backref='location')

    def __init__(self, name=None, url=None, chain=None, untappd_id=None, created=None):
        self.name = name
        self.url = url
        self.chain = chain
        self.untappd_id = untappd_id
        self.created = created or datetime.now()

    def __repr__(self):
        return '<Location {}>'.format(self.name)

    def flatten(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'untappd_id': self.untappd_id,
            'created': self.created.isoformat()
        }


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

    def flatten(self):
        return {
            'id': self.id,
            'name': self.name,
            'created': self.created.isoformat()
        }


class User(db.Model):
    """ App user, someday link to untappd """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    untappd_id = db.Column(db.String(128))
    created = db.Column(db.DateTime)

    distinct_beers = db.relationship('DistinctBeer', backref='user')

    def __init__(self, username=None, untappd_id=None, created=None):
        self.username = username
        self.untappd_id = untappd_id
        self.created = created or datetime.now()

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def flatten(self):
        return {
            'id': self.id,
            'username': self.username,
            'untappd_id': self.untappd_id,
            'created': self.created.isoformat()
        }


class DistinctBeer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    untappd_bid = db.Column(db.Integer)
    untappd_username = db.Column(db.String(128))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    beverage_id = db.Column(db.Integer, db.ForeignKey('beverage.id'))

    def __init__(self, untappd_bid=None, untappd_username=None, user=None, beverage=None):
        self.untappd_bid = untappd_bid
        self.untappd_username = untappd_username
        if user:
            self.user = user
        if beverage:
            self.beverage = beverage
