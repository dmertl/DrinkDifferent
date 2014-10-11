import unittest
import os
import json
from scraper.stout import BeerParser, Scraper
from web.models import Beverage
import logging

root_log = logging.getLogger()
root_log.setLevel(logging.WARN)
root_log.addHandler(logging.NullHandler())


class TestMenuParsing(unittest.TestCase):
    def test_parse(self):
        """ Test full menu parse """
        html_fixture = os.path.join('fixtures', 'stout_menu', 'hollywood_2014-08-25.html')
        with file(html_fixture) as f:
            html = f.read()
        scraper = Scraper()
        actual = scraper.scrape(html)
        expected_fixture = os.path.join('fixtures', 'stout_menu', 'hollywood_2014-08-25.json')
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


class TestBeerParser(unittest.TestCase):
    def test_basic_parse(self):
        """ Test basic parsing. """
        parser = BeerParser()
        string = 'Saison Dupont Cuvee Dry Hop - Dupont / Belg / Saison / 22oz / 6.5% / $10'
        actual = parser.parse(string)
        expected = Beverage()
        expected.scraped_value = string
        expected.name = 'Saison Dupont Cuvee Dry Hop'
        expected.brewery = 'Dupont'
        expected.brewery_location = 'Belg'
        expected.style = 'Saison'
        expected.volume = 22.0
        expected.volume_units = 'oz'
        expected.abv = 6.5
        expected.price = 10.0
        expected.type = 'Beer'
        expected.availability = 'Bottle'
        expected.created = actual.created
        self.assertEqual(expected.flatten(), actual.flatten())

    def test_location_style_parsed_with_extras(self):
        """ Test that location and style are parsed correctly even if there's trailing content """
        parser = BeerParser()
        actual = parser.parse('Old Speckled Hen - Green King / UK / Cream Ale / Nitro / 5.2%')
        self.assertEqual('UK', actual.brewery_location)
        self.assertEqual('Cream Ale', actual.style)

    def test_weihenstephaner_exception(self):
        """ Test that exception for Weihenstephaner is handled. """
        parser = BeerParser()
        actual = parser.parse('Weihenstephaner Original - Germ / Helles Lager / 5.1%')
        self.assertEqual('Weihenstephaner Original', actual.name)
        self.assertEqual('Weihenstephan', actual.brewery)
        self.assertEqual('Germ', actual.brewery_location)
        self.assertEqual('Helles Lager', actual.style)
        self.assertEqual(5.1, actual.abv)

    def test_volume_switches_availability(self):
        """ Test that volume switches between On Tap and Bottle availability. """
        parser = BeerParser()
        actual = parser.parse('Saison Dupont Cuvee Dry Hop - Dupont / Belg / Saison / 5.2%')
        self.assertEqual('On Tap', actual.availability)
        actual = parser.parse('Saison Dupont Cuvee Dry Hop - Dupont / Belg / Saison / 22oz')
        self.assertEqual('Bottle', actual.availability)

    def test_string_unidecoded(self):
        parser = BeerParser()
        actual = parser.parse(u'Saison Dupont Cuvee Dry Hop \u2013 Dupont / Belg / Saison / 6.5% / $10')
        self.assertEqual('Saison Dupont Cuvee Dry Hop', actual.name)
        self.assertEqual('Dupont', actual.brewery)


if __name__ == '__main__':
    unittest.main()
