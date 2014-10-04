import os
import json
import re
from datetime import datetime, timedelta
from scraper.util import flatten_menu_scrape

# Root cache directory
cache_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'menu_cache')


def cache_menu_scrape(menu_scrape):
    """
    Cache the scraped menu data on the filesystem.

    :param menu_scrape: Scraped menu.
    :type menu_scrape: MenuScrape
    :return: Path to the cached file.
    :rtype: str
    """
    # Name files menu_YYYY-MM-DD_location.json
    file_path = _build_cache_path(menu_scrape.location.chain, menu_scrape.location.name, time=menu_scrape.date)
    # Organize cache into directories by location/year/month
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Write file
    with open(file_path, 'w') as fh:
        fh.write(json.dumps(flatten_menu_scrape(menu_scrape)))
    return file_path


def get_cache_near(chain, location, time, lean='new'):
    """
    Get the cache file closest to the requested time. Will search for newer or older files depending on lean. If no file
    can be found will return the oldest or newest cache file.

    :param chain: Chain name.
    :type chain: str
    :param location: Location name.
    :type location: str
    :param time: Requested time of scraping.
    :type time: datetime
    :param lean: Which direction to check if exact match is not found, 'new'er or 'old'er.
    :type lean: str
    :return: Cache data.
    :rtype: dict
    """
    cache_path = _build_cache_path(chain, location, time=time)
    i = 0
    while not os.path.exists(cache_path):
        i += 1
        if lean == 'new':
            time = time + timedelta(days=1)
        else:
            time = time - timedelta(days=1)
        cache_path = _build_cache_path(chain, location, time=time)
        if i > 100:
            # Unable to find nearby cache, return oldest/newest
            return get_cache_extreme(chain, location, lean)
    return json.load(open(cache_path))


def get_cache_extreme(chain, location, extreme='new'):
    """
    Get the newest or oldest cache file for a location. Helpful when user requests cache file out of range. Instead,
    return the closest cache file we have.

    :param chain: Chain name.
    :type chain: str
    :param location: Location name.
    :type location: str
    :param extreme: Either 'new' or 'old'
    :type extreme: str
    :return: Cache data.
    :rtype: dict
    """
    chain = _safe_name(chain)
    location = _safe_name(location)
    year = min(os.listdir(cache_root))
    year_dir = os.path.join(cache_root, year)
    month = min(os.listdir(year_dir))
    month_dir = os.path.join(year_dir, month)
    regex = re.compile('.*[0-9]{4}-[0-9]{2}-([0-9]{2})_' + chain + '_' + location + '.json')
    days = []
    for menu_file in os.listdir(month_dir):
        matches = regex.match(menu_file)
        if matches:
            days.append(matches.group(1))
    if extreme == 'new':
        day = max(days)
    else:
        day = min(days)
    return get_cache(chain=chain, location=location, year=year, month=month, day=day)


def get_cache(name=None, chain=None, location=None, time=None, year=None, month=None, day=None):
    """
    Read data out of cache.

    The name parameter is the cache file name which can be parsed into the path. Otherwise the path is built out of the
    chain, location and date pieces (or datetime).

    :param name: Name of cache file, parsed into full path.
    :type name: str
    :param chain: Chain name.
    :type chain: str
    :param location: Location name.
    :type location: str
    :param time: Datetime scraping occurred.
    :type time: datetime
    :param year: Year scraping occurred.
    :type year: str
    :param month: Month scraping occurred.
    :type month: str
    :param day: Day scraping occurred
    :type day: str
    :return: Cached scraping data.
    :rtype: dict
    """
    if name:
        regex = re.compile('.*([0-9]{4})-([0-9]{2})-([0-9]{2})_([^_]*)_([^_]*)')
        matches = regex.match(name)
        cache_path = _build_cache_path(matches.group(4), matches.group(5), year=matches.group(1),
                                       month=matches.group(2),
                                       day=matches.group(3))
    else:
        if time:
            cache_path = _build_cache_path(chain=chain, location=location, time=time)
        else:
            cache_path = _build_cache_path(chain=chain, location=location, year=year, month=month, day=day)

    return json.load(open(cache_path))


def _build_cache_path(chain, location, year=None, month=None, day=None, time=None):
    """
    Build a file cache path out of menu scraping information. Either date pieces or time is required.

    :param chain: Chain name.
    :type chain: str
    :param location: Location name.
    :type location: str
    :param year: Year piece of scraping date.
    :type year: str
    :param month: Month piece of scraping date.
    :type month: str
    :param day: Day piece of scraping date.
    :type day: str
    :param time: Datetime of scraping.
    :type time: datetime
    :return: Path to cache file.
    :rtype: str
    """
    chain = _safe_name(chain)
    location = _safe_name(location)
    if time:
        _dir = os.path.join(time.strftime('%Y'), time.strftime('%m'))
        filename = '{}_{}_{}.json'.format(time.strftime('%Y-%m-%d'), chain, location)
    else:
        _dir = os.path.join(year, month)
        filename = '{}-{}-{}_{}_{}.json'.format(year, month, day, chain, location)
    return os.path.join(cache_root, _dir, filename)


def _safe_name(value):
    """
    Make filename parts filesystem safe and easier to parse.

    :param value: Value to make safe.
    :type value: str
    :return: Safe value.
    :rtype: str
    """
    return value.replace(' ', '-').lower()
