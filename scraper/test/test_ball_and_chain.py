import unittest
import os
import json
from scraper.ball_and_chain import Scraper
from scraper.util import flatten_beverages
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
        self.assertEqual(len(expected), len(actual),
                         'Beverage length does not match. expected={}, actual={}'.format(len(expected),
                                                                                         len(actual)))
        for i in range(0, len(expected)):
            actual_flat = actual[i].flatten()
            # Ignore timestamps
            del expected[i]['created']
            del actual_flat['created']
            self.assertEqual(expected[i], actual_flat)


if __name__ == '__main__':
    unittest.main()
