import unittest
import urllib2
import os
import json
from scraper.ball_and_chain import Scraper
from scraper.model import Beverage
from scraper.util import flatten_beverages, flatten_menu_scrape
import logging

root_log = logging.getLogger()
root_log.setLevel(logging.WARN)
root_log.addHandler(logging.NullHandler())


class TestScraper(unittest.TestCase):
    def test_parse(self):
        """ Test a full menu scrape """
        html_fixture = os.path.join('fixtures', 'ball_and_chain_menu', 'hollywood_2014-10-1.html')
        with file(html_fixture) as f:
            html = f.read()
        scraper = Scraper()
        actual = scraper.scrape(html)
        expected_fixture = os.path.join('fixtures', 'ball_and_chain_menu', 'hollywood_2014-10-1.json')
        with file(expected_fixture) as f:
            expected = json.load(f)
        self.assertEqual(expected.get('beverages'), flatten_beverages(actual))
        pass


if __name__ == '__main__':
    unittest.main()
