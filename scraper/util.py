import os
import urllib2


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
