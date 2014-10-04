__author__ = 'dmertl'


def scrape_to_dict(menu_scrape):
    """
    Convert a MenuScrape to dict that can be easily dumped to JSON.

    :param menu_scrape:
    :type menu_scrape: MenuScrape
    :return:
    :rtype: dict
    """
    d = {
        'location': menu_scrape.location.__dict__.copy(),
        'url': menu_scrape.url,
        'date': menu_scrape.date.isoformat(),
        'beverages': []
    }
    for beverage in menu_scrape.beverages:
        d['beverages'].append(
            dict((k, v) for k, v in beverage.__dict__.iteritems() if v)
        )
    return d
