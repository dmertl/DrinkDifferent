from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'lkadfsnr12h7fnadvwnaseb80b0^*)g0v680v680b780bS*DFB7sdgf'
#TODO Move db file to better place
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///drink_different.db'
db = SQLAlchemy(app)

toolbar = DebugToolbarExtension(app)

import views
