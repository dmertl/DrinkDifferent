import logging
import urllib2
import sys
import stout
import ball_and_chain
from datetime import datetime
from web.models import MenuScrape
from web import db

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
        menu_scrape.beverages = scraper.scrape(menu_html)
        db.session.add(menu_scrape)
        for beverage in menu_scrape.beverages:
            beverage.menu_scrape = menu_scrape
            db.session.add(beverage)
        db.session.commit()
    else:
        _log('Unable to retrieve menu from {0}'.format(location.url), logging.ERROR)


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
