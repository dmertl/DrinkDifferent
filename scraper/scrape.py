import logging
import urllib2
import sys
import stout
import ball_and_chain
from datetime import datetime
from web.models import MenuScrape, Location, BeverageScrape, Beverage, Brewery
from web import db
from base import ScrapedBeverage

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)


def scrape_location(location, scraper):
    """
    Scrape all beverages from a location.

    :param location: Location to scrape
    :type location: Location
    :param scraper: Scraper to use
    :type scraper: base.Scraper
    :return:
    :rtype:
    """
    _log('Scraping {} {} - {}'.format(location.chain.name, location.name, location.url), logging.INFO)
    menu_scrape = MenuScrape(location=location, url=location.url, created=datetime.now())
    menu_html = urllib2.urlopen(location.url).read()
    if menu_html:
        _log('Read {0} bytes'.format(len(menu_html)), logging.INFO)
        # Flag all existing beverages as inactive
        db.engine.execute('UPDATE beverage SET is_active = 0 WHERE location_id = :location_id', location_id=location.id)
        update_menu_scrape(menu_scrape, scraper.scrape(menu_html))
    else:
        _log('Unable to retrieve menu from {0}'.format(location.url), logging.ERROR)


def update_menu_scrape(menu_scrape, scraped_beverages):
    """

    :param menu_scrape:
    :type menu_scrape: MenuScrape
    :param scraped_beverages:
    :type scraped_beverages: ScrapedBeverage[]
    :return:
    :rtype:
    """
    for scraped_beverage in scraped_beverages:
        brewery = Brewery.query.filter_by(name=scraped_beverage.brewery).first()
        if not brewery:
            brewery = Brewery(name=scraped_beverage.brewery, location=scraped_beverage.brewery_location)
        beverage = Beverage.query.filter_by(name=scraped_beverage.name, brewery=brewery).first()
        if beverage:
            beverage = update_beverage(beverage, scraped_beverage)
            db.session.add(beverage)
        beverage_scrape = BeverageScrape(beverage=beverage, location=menu_scrape.location, menu_scrape=menu_scrape,
                                         scraped_value=scraped_beverage.scraped_value)
        db.session.add(beverage_scrape)
    db.session.add(menu_scrape)
    db.session.commit()


def update_beverage(beverage, scraped_beverage):
    """
    Update Beverage with ScrapedBeverage data.

    :param beverage:
    :type beverage: Beverage
    :param scraped_beverage:
    :type scraped_beverage: ScrapedBeverage
    :return:
    :rtype:
    """
    whitelist = ['name', 'type', 'style', 'abv', 'year', 'description', 'availability', 'price', 'volume',
                 'volume_units']
    for field in whitelist:
        if scraped_beverage.__getattribute__(field):
            beverage.__setattr__(field, scraped_beverage.__getattribute__(field))
    beverage.is_active = True
    return beverage


def _log(message, level=logging.INFO):
    root_log.log(level, message)


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Stout
    for loc in stout.locations:
        scrape_location(loc, stout.Scraper())

    # Ball and Chain
    for loc in ball_and_chain.locations:
        scrape_location(loc, ball_and_chain.Scraper())
