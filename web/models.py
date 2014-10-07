from web import db
from datetime import datetime

menu_scrape_beverage_table = db.Table('menu_scrape_beverage', db.metadata,
                                      db.Column('menu_scrape_id', db.Integer, db.ForeignKey('menu_scrape.id')),
                                      db.Column('beverage_id', db.Integer, db.ForeignKey('beverage.id')))


class MenuScrape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)

    beverages = db.relationship('Beverage', secondary=menu_scrape_beverage_table)

    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    location = db.relationship('Location', backref=db.backref('menu_scrapes', lazy='dynamic'))

    def __init__(self, location=None, beverages=None, created=None):
        self.location = location
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
    location = db.relationship('Location', backref=db.backref('beverages', lazy='dynamic'))

    menu_scrapes = db.relationship('MenuScrape', secondary=menu_scrape_beverage_table)

    def __init__(self, name=None, brewery=None, type=None, created=None):
        self.name = name
        self.brewery = brewery
        self.type = type
        self.created = created or datetime.now()

    def __repr__(self):
        return '<Beverage {}>'.format(self.name)

        # def __eq__(self, other):
        # if self.untappd_id and other.untappd_id:
        #             return self.untappd_id == other.untappd_id
        #         else:
        #             return self.name == other.name
        #
        #     def __hash__(self):
        #         # TODO: This isn't really unique and may be problematic, but it makes intersection() work
        #         return hash(str(self.untappd_id) + str(self.name))


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    url = db.Column(db.String(128))
    untappd_id = db.Column(db.String(128))
    created = db.Column(db.DateTime)

    chain_id = db.Column(db.Integer, db.ForeignKey('chain.id'))
    chain = db.relationship('Chain', backref=db.backref('locations', lazy='dynamic'))

    def __init__(self, name=None, url=None, chain=None, created=None):
        self.name = name
        self.url = url
        self.chain = chain
        self.created = created or datetime.now()

    def __repr__(self):
        return '<Location {}>'.format(self.name)


class Chain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    created = db.Column(db.DateTime)

    def __init__(self, name=None, created=None):
        self.name = name
        self.created = created or datetime.now()

    def __repr__(self):
        return '<Chain {}>'.format(self.name)
