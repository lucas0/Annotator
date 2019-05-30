from app import db

#login and persistence mgmt with flask_sqlalchemy
class User(db.Model):
	""" Create user table"""
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True)
	password = db.Column(db.String(80))

	def __repr__(self):
		return '<User {}>'.format(self.username)

