import os
import urllib2
import dateutil.parser
from scraper.model import MenuScrape, Location, Beverage


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


def expand_beverages(data):
    """
    Expand flattened beverage list back into Beverage list.

    :param data: Flat beverage list.
    :type data: dict[]
    :return: Beverage list.
    :rtype: Beverage[]
    """
    expanded = []
    for flat in data:
        beverage = Beverage()
        for key in beverage.__dict__.keys():
            if flat.get(key):
                beverage.__setattr__(key, flat.get(key))
        expanded.append(beverage)
    return expanded


def flatten_menu_scrape(menu_scrape):
    """
    Convert a MenuScrape into a flat format that can easily be dumped to JSON.

    :param menu_scrape: MenuScrape
    :type menu_scrape: MenuScrape
    :return:
    :rtype: dict
    """
    return {
        'location': flatten_location(menu_scrape.location),
        'url': menu_scrape.url,
        'date': menu_scrape.date.isoformat() if menu_scrape.date else None,
        'beverages': flatten_beverages(menu_scrape.beverages)
    }


def expand_menu_scrape(data):
    """
    Expand a flattened menu scrape dict back into a MenuScrape.

    :param data: Menu scrape dict.
    :type data: dict
    :return: MenuScrape.
    :rtype: MenuScrape
    """
    menu_scrape = MenuScrape()
    menu_scrape.url = data['url']
    if data['date']:
        menu_scrape.date = dateutil.parser.parse(data['date'])
    if data['location']:
        menu_scrape.location = expand_location(data['location'])
    menu_scrape.beverages = expand_beverages(data['beverages'])


def flatten_location(location):
    """
    Flatten a Location into a dict that can be easily converted to JSON.

    :param location: Location.
    :type location: Location
    :return: Dict.
    :rtype: dict
    """
    return location.__dict__.copy()


def expand_location(data):
    """
    Expand flattened location dict back into a Location.

    :param data: Location dict.
    :type data: dict
    :return: Location.
    :rtype: Location
    """
    return Location(data['name'], data['url'], data['chain'])


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
