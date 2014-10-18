"""
Split Beverage table into Beverage and BeverageScrape. Separates the scraping (temporal) from the actual beverage.
Beverage table will be renamed to BeverageScrape. Beverage table created with similar columns. Move all unique
BeverageScrapes to Beverages table. Then drop unnecessary columns from BeverageScrape.
"""

import argparse
import logging
import sys
import dateutil.parser
from web.models import MenuScrape, Beverage, Location, BeverageScrape, Brewery, DistinctBeer
from web import db

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)


def link():
    distinct = DistinctBeer.query.all()
    for d in distinct:
        # Technically could have multiple, but pick the first
        beverage = Beverage.query.filter_by(untappd_id=d.untappd_bid).first()
        if beverage:
            d.beverage_id = beverage.id
            db.session.add(d)
    db.session.commit()

if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Command line arguments
    parser = argparse.ArgumentParser(description='Split beverage into scrapes, beverages, and brewery.')

    link()
