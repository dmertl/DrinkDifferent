from setuptools import setup

setup(name='DrinkDifferent',
      version='1.0',
      install_requires=[
          'lxml',
          'unidecode',
          'Flask',
          'beautifulsoup4',
          'Flask-SQLAlchemy',
          'python-dateutil',
          'requests', # Required until we separate untappd into its own project
          'flask-debugtoolbar',
      ])
