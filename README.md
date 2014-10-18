DrinkDifferent
==============

Find new beers to drink.

Setup
-----

Create database with model schema.
    python -m scripts.create_schema
Populate database with scrapable locations.
    python -m scripts.db_init_locations

TODO
----

- Run bev_scrape_split.py on production (backup db first)
- Cleanup stout
- Config

Scrapers
--------

- Gather beverage data from various bar websites.
- Standardized scraping process.
- Separate scraper class per chain.
- Returns a list of standardized Beverage objects.
- Beverages are saved to database.
- Scraping brewery and name are the important parts, every else isn't important
- All scrapes should be executable scripts and python modules
 - Executing from command line should allow for scraping file or url and output JSON

### Ideas

- Use checkin data from untappd to get beer list? Have to deal with stale data, how far back do we go for "current" beer?

Menu Diff
---------

- View the changes in beverage offerings at location between two dates.

### Ideas
- Store cookie and show diff since last viewing.
- Allow simple login and show diff since last viewing.
- Allow user to save a date in a cookie.
- Integrate with Foursquare to get last check-in date.
- Compare beer selection across locations or chains

Beer Checklist
--------------

- Allow users to check off beverages they drank at a location.

### Ideas
- Allow users to remove beverages without saying they drank it (bad parsing, no longer available, not interested etc.)
- Progress bars for locations (simply having tried every beer at a location is fine, no need to actually have it at that bar).
- Integrate with Untappd for list of beverages user has had.

Notifications
-------------

- Get a notification when new beer is available at your favorite bars.

### Ideas
- Allow user to select their favorite bars.
- Option to notify when any new beers appear, or only new beers the have not had before.

Beer DB
-------

- Use Untappd to get a unique ID for beers that can be compared across locations.

### Ideas

- Will help with Untappd integration for Beer Checklist
- Allows comparing beverage data across locations (which may have different naming conventions)
- Probably have to use human interaction to find right beverage, but can speed up by linking to search for name + brewery
- Cache search term => resulting ID for future lookup (could potentially create false positives for overly generic scraped names)

Old Notes From Stout Beer Notifier
----------------------------------

stout-beer-notifier
===================

Get a notification when stout updates their beer list.

TODO
====

- Config
- Sanity check beer piece parsing, check size/price/alcohol percentage are numbers
- Layout
- Style
- Parse location from menu (maybe not necessary)
- Remove duplicates (they exist in the menu HTML)
- Notifications
- Unit tests
- Configurable logging

Future Features
---------------

- Check for modified beverages in addition to added and removed. Same name, but different alcohol % or brewery, etc.
- Some kind of user login to view differences since you last visited the site.

Known Issues
------------

- Need a better way of identifying location vs. brewery vs. style. Currently have to use position which is not always consistent.
- Some beers have location swapped with brewery "St Louis Framboise – Belgium / Lambic-Fruit / 375ml / 4.5% / $15"

System
======

Menu Parsing
-------------
parse_menu.py takes stoutburgersandbeers.com menu HTML and parses it into JSON.

Menu Diff
---------
menu_diff.py takes two JSON menu generated by parse_menu.py and computes the difference.

Automation
----------

- Run parse_menu.py daily for each location.
- Save file with day timestamp.

Viewing Diff
------------

- Prompt for a location, start day and end day.
- Retrieve cached menu files for location on start and end day (or nearest available).
- Calculate diff of menu files.
- Display diff.
-- Display two lists, added and removed
-- Display beer name only, hover for tooltip with full details

Notifications
-------------

TBD

Specify frequency, daily/weekly, etc.
Specify location
Specify categories of interest beer, on tap, wine, etc.

Testing
=======

Sample Testing
--------------

_View menu parsing_
python parse_menu.py sample/old.html --pretty
python parse_menu.py sample/new.html --pretty

_View menu diff_
python menu_diff.py sample/old.json sample/new.json --pretty

_Test menu parsing (diff should be empty)_
diff <(python parse_menu.py sample/old.html --pretty) sample/old.json
diff <(python parse_menu.py sample/2014-08-25.html --pretty) sample/2014-08-25.json

_Review parsed menu in table for easy scanning_
python table_view.py sample/2014-08-25.json > table.html

Unit Tests
----------

Someday
