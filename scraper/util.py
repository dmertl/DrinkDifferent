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
        'date': menu_scrape.date.isoformat() if menu_scrape.date else None,
        'beverages': []
    }
    for beverage in menu_scrape.beverages:
        d['beverages'].append(
            dict((k, v) for k, v in beverage.__dict__.iteritems() if v)
        )
    return d


def flatten_beverages(beverages):
    """
    Convert a list of beverages into a flat format that can easily be dumped to JSON.

    :param beverages:
    :type beverages: Beverage[]
    :return:
    :rtype: dict[]
    """
    flat = []
    for beverage in beverages:
        flat.append(
            dict((k, v) for k, v in beverage.__dict__.iteritems() if v)
        )
    return flat
