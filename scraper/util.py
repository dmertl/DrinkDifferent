import os
import urllib2


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


def flatten_menu_scrape(menu_scrape):
    """
    Convert a MenuScrape into a flat format that can easily be dumped to JSON.

    :param menu_scrape: MenuScrape
    :type menu_scrape: MenuScrape
    :return:
    :rtype: dict
    """
    return {
        'location': menu_scrape.location.__dict__.copy(),
        'url': menu_scrape.url,
        'date': menu_scrape.date.isoformat() if menu_scrape.date else None,
        'beverages': flatten_beverages(menu_scrape.beverages)
    }


def url_from_arg(arg, locations):
    """
    Determine actual URL from scrape request argument.

    Checks if argument is location name or file on local filesystem. Otherwise assumes HTTP URL. Standard process for
    running scraper from the command line.

    :param arg:
    :type arg: str
    :param locations:
    :type locations: Location[]
    :return:
    :rtype: str
    """
    location = [x for x in locations if x.name == arg]
    if location:
        return location[0].url
    else:
        if os.path.exists(arg):
            return 'file:{0}'.format(urllib2.quote(os.path.abspath(arg)))
        else:
            return arg
