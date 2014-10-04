from abc import abstractmethod


class Scraper(object):
    @abstractmethod
    def scrape(self, html):
        """
        Scrape all beverages from web page HTML.

        :param html: HTML of web page.
        :type html: str
        :return: Beverages scraped.
        :rtype: Beverage[]
        """
