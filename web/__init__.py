from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
#TODO Move db file to better place
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

import views
