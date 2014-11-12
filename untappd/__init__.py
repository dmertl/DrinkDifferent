""" Structure shamelessly copied from https://github.com/mLewisLogic/foursquare """
import logging

log = logging.getLogger(__name__)

import inspect
import urllib
import time
import sys
# 3rd party libraries that might not be present during initial install
# but we need to import for the version #
# try:
import requests
# except ImportError:
# pass

# Helpful for debugging what goes in and out
NETWORK_DEBUG = True
if NETWORK_DEBUG:
    # These two lines enable debugging at httplib level (requests->urllib3->httplib)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
    import httplib

    httplib.HTTPConnection.debuglevel = 1
    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

# API endpoints
AUTH_ENDPOINT = 'https://untappd.com/oauth/authenticate'
TOKEN_ENDPOINT = 'https://untappd.com/oauth/authorize'
API_ENDPOINT = 'https://api.untappd.com/v4'

# Number of times to retry http requests
NUM_REQUEST_RETRIES = 3

# Max number of sub-requests per multi request
MAX_MULTI_REQUESTS = 5

# Change this if your Python distribution has issues with Untappd's SSL cert
VERIFY_SSL = True


class UntappdException(Exception): pass
# Specific exceptions
class InvalidParam(UntappdException): pass

#TODO: Add more error types
error_types = {
    'invalid_param': InvalidParam,
}


class Untappd(object):
    def __init__(self, client_id=None, client_secret=None, access_token=None, redirect_uri=None):
        self.oauth = self.OAuth(client_id, client_secret, redirect_uri)
        self.base_requester = self.Requester(client_id, client_secret, access_token)
        self._attach_endpoints()

    def _attach_endpoints(self):
        for name, endpoint in inspect.getmembers(self):
            if inspect.isclass(endpoint) and issubclass(endpoint, self._Endpoint) and (endpoint is not self._Endpoint):
                endpoint_instance = endpoint(self.base_requester)
                setattr(self, endpoint_instance.endpoint, endpoint_instance)

    def set_access_token(self, access_token):
        """Update the access token to use"""
        self.base_requester.set_token(access_token)

    @property
    def rate_limit(self):
        """Returns the maximum rate limit for the last API call i.e. X-RateLimit-Limit"""
        return self.base_requester.rate_limit

    @property
    def rate_remaining(self):
        """Returns the remaining rate limit for the last API call i.e. X-RateLimit-Remaining"""
        return self.base_requester.rate_remaining

    class OAuth(object):
        """Handles OAuth authentication procedures and helps retrieve tokens"""

        def __init__(self, client_id, client_secret, redirect_uri):
            self.client_id = client_id
            self.client_secret = client_secret
            self.redirect_uri = redirect_uri

        def auth_url(self):
            """Gets the url a user needs to access to give up a user token"""
            params = {
                'client_id': self.client_id,
                'response_type': u'code',
                # Untappd API uses the non-standard param name "request_url" instead of "request_uri"
                'redirect_url': self.redirect_uri,
            }
            return '{AUTH_ENDPOINT}?{params}'.format(
                AUTH_ENDPOINT=AUTH_ENDPOINT,
                params=urllib.urlencode(params))

        def get_token(self, code):
            """Gets the auth token from a user's response"""
            if not code:
                log.error(u'Code not provided')
                return None
            params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': u'authorization_code',
                # Untappd API uses the non-standard param name "request_url" instead of "request_uri"
                'redirect_url': self.redirect_uri,
                'code': unicode(code),
            }
            # Get the response from the token uri and attempt to parse
            return _get(TOKEN_ENDPOINT, params=params)['data']['response']['access_token']

    class Requester(object):
        """Api requesting object"""

        def __init__(self, client_id=None, client_secret=None, access_token=None):
            """Sets up the api object"""
            self.client_id = client_id
            self.client_secret = client_secret
            self.set_token(access_token)
            self.rate_limit = None
            self.rate_remaining = None

        def set_token(self, access_token):
            """Set the OAuth token for this requester"""
            self.access_token = access_token
            self.userless = not bool(access_token)  # Userless if no access_token

        def GET(self, path, params={}, **kwargs):
            """GET request that returns processed data"""
            params = params.copy()
            # Continue processing normal requests
            headers = self._create_headers()
            params = self._enrich_params(params)
            url = '{API_ENDPOINT}{path}'.format(
                API_ENDPOINT=API_ENDPOINT,
                path=path
            )
            result = _get(url, headers=headers, params=params)
            self.rate_limit = result['headers']['X-RateLimit-Limit']
            self.rate_remaining = result['headers']['X-RateLimit-Remaining']
            return result['data']['response']

        def POST(self, path, data={}, files=None):
            """POST request that returns processed data"""
            if data is not None:
                data = data.copy()
            if files is not None:
                files = files.copy()
            headers = self._create_headers()
            data = self._enrich_params(data)
            url = '{API_ENDPOINT}{path}'.format(
                API_ENDPOINT=API_ENDPOINT,
                path=path
            )
            result = _post(url, headers=headers, data=data, files=files)
            self.rate_limit = result['headers']['X-RateLimit-Limit']
            self.rate_remaining = result['headers']['X-RateLimit-Remaining']
            return result['data']['response']

        def _enrich_params(self, params):
            """Enrich the params dict"""
            if self.userless:
                params['client_id'] = self.client_id
                params['client_secret'] = self.client_secret
            else:
                params['access_token'] = self.access_token
            return params

        def _create_headers(self):
            """Get the headers we need"""
            headers = {}
            # Currently no headers, 4sq uses language header
            #TODO: remove me?
            return headers

    class _Endpoint(object):
        """Generic endpoint class"""

        def __init__(self, requester):
            """Stores the request function for retrieving data"""
            self.requester = requester

        def _expanded_path(self, path=None):
            """Gets the expanded path, given this endpoint"""
            return '/{expanded_path}'.format(
                expanded_path='/'.join(p for p in (self.endpoint, path) if p)
            )

        def GET(self, path=None, *args, **kwargs):
            """Use the requester to get the data"""
            return self.requester.GET(self._expanded_path(path), *args, **kwargs)

        def POST(self, path=None, *args, **kwargs):
            """Use the requester to post the data"""
            return self.requester.POST(self._expanded_path(path), *args, **kwargs)

    class User(_Endpoint):
        """User endpoint"""
        endpoint = 'user'

        def info(self, USERNAME='', params={}):
            """/v4/user/info/USERNAME"""
            return self.GET('info/{USERNAME}'.format(USERNAME=USERNAME), params)

        def badges(self, USERNAME='', params={}):
            """/v4/user/badges/USERNAME"""
            return self.GET('badges/{USERNAME}'.format(USERNAME=USERNAME), params)

        def friends(self, USERNAME='', params={}):
            """/v4/user/friends/USERNAME"""
            return self.GET('friends/{USERNAME}'.format(USERNAME=USERNAME), params)

        def wishlist(self, USERNAME='', params={}):
            """/v4/user/wishlist/USERNAME"""
            return self.GET('wishlist/{USERNAME}'.format(USERNAME=USERNAME), params)

        def beers(self, USERNAME='', params={}):
            """/v4/user/beers/USERNAME"""
            return self.GET('beers/{USERNAME}'.format(USERNAME=USERNAME), params)

    class Venue(_Endpoint):
        """Venue endpoint"""
        endpoint = 'venue'

        def info(self, VENUE_ID, params={}):
            """/v4/venue/info/VENUE_ID"""
            return self.GET('info/{VENUE_ID}'.format(VENUE_ID=VENUE_ID), params)

        def checkins(self, VENUE_ID, params={}):
            """/v4/venue/checkins/VENUE_ID"""
            return self.GET('checkins/{VENUE_ID}'.format(VENUE_ID=VENUE_ID), params)

    class Brewery(_Endpoint):
        """Brewery endpoint"""
        endpoint = 'brewery'

        def info(self, BREWERY_ID, params={}):
            """/v4/brewery/info/BREWERY_ID"""
            return self.GET('info/{BREWERY_ID}'.format(BREWERY_ID=BREWERY_ID), params)

    class Beer(_Endpoint):
        """Beer endpoint"""
        endpoint = 'beer'

        def info(self, BID, params={}):
            """/v4/beer/info/BID"""
            return self.GET('info/{BID}'.format(BID=BID), params)

    class Checkin(_Endpoint):
        """Checkin endpoint"""
        endpoint = 'checkin'

        def info(self, CHECKIN_ID, params={}):
            """/v4/checkin/info/CHECKIN_ID"""
            return self.GET('view/{CHECKIN_ID}'.format(CHECKIN_ID=CHECKIN_ID), params)


def _log_and_raise_exception(msg, data, cls=UntappdException):
    """Calls log.error() then raises an exception of class cls"""
    data = u'{0}'.format(data)
    # We put data as a argument for log.error() so error tracking systems such
    # as Sentry will properly group errors together by msg only
    log.error(u'{0}: %s'.format(msg), data)
    raise cls(u'{0}: {1}'.format(msg, data))


"""
Network helper functions
"""
#def _request_with_retry(url, headers={}, data=None):
def _get(url, headers={}, params=None):
    """Tries to GET data from an endpoint using retries"""
    #TODO: make sure we don't need silly foursquare urlencoding
    # param_string = _foursquare_urlencode(params)
    param_string = urllib.urlencode(params)
    for i in xrange(NUM_REQUEST_RETRIES):
        try:
            try:
                response = requests.get(url, headers=headers, params=param_string, verify=VERIFY_SSL)
                return _process_response(response)
            except requests.exceptions.RequestException, e:
                _log_and_raise_exception('Error connecting with foursquare API', e)
        except UntappdException, e:
            # Some errors don't bear repeating
            if e.__class__ in [InvalidParam]: raise
            # if e.__class__ in [InvalidAuth, ParamError, EndpointError, NotAuthorized, Deprecated]: raise
            # If we've reached our last try, re-raise
            if ((i + 1) == NUM_REQUEST_RETRIES): raise
        time.sleep(1)


def _post(url, headers={}, data=None, files=None):
    """Tries to POST data to an endpoint"""
    try:
        response = requests.post(url, headers=headers, data=data, files=files, verify=VERIFY_SSL)
        return _process_response(response)
    except requests.exceptions.RequestException, e:
        _log_and_raise_exception('Error connecting with foursquare API', e)


def _process_response(response):
    """Make the request and handle exception processing"""
    # Read the response as JSON
    try:
        data = response.json()
    except ValueError:
        _log_and_raise_exception('Invalid response', response.text)

    # Default case, Got proper response
    if response.status_code == 200:
        return {'headers': response.headers, 'data': data}
    return _raise_error_from_response(data)


def _raise_error_from_response(data):
    """Processes the response data"""
    # Check the meta-data for why this request failed
    meta = data.get('meta')
    if meta:
        # Account for foursquare conflicts
        # see: https://developer.foursquare.com/overview/responses
        if meta.get('code') in (200, 409): return data
        #TODO: not detection error types correctly, meta: {u'error_type': u'invalid_param',
        exc = error_types.get(meta.get('errorType'))
        if exc:
            raise exc(meta.get('errorDetail'))
        else:
            _log_and_raise_exception('Unknown error. meta', meta)
    else:
        _log_and_raise_exception('Response format invalid, missing meta property. data', data)
