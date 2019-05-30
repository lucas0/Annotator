import os

cwd = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	FLASK_DEBUG=1,
	SECRET_KEY = '4ZuS2a\BH=44sk!$'
	SQLALCHEMY_DATABASE_URI = "sqlite:///"+os.path.join(cwd,"app.db")
	SQLALCHEMY_TRACK_MODIFICATIONS = False
