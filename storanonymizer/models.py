from storanonymizer import db

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=True)
	password_hash = db.Column(db.String(1024))

	stories = db.relationship("Story", backref="user", lazy="select")
	contributions = db.relationship("Contribution", backref="auhor", lazy="select")

	# These methods are required by
	# Flask-Login
	# They all return True or False so the flask-login module
	# knows that the user exists.
	# E.g. a user object is stored in a session,
	# when flask-login tries to execute these function
	# it knows that the user is still in a valid session.
	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return str(self.id)

	def __init__(self, name, password_hash):
		self.name = name
		self.password_hash = password_hash

	def __repr__(self):
		return "<User {}>".format(self.id)

class Story(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String())
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	contributions = db.relationship("Contribution", backref="story", lazy="select")
	public_authors = db.Column(db.Boolean(), default=False)
	public_contributions = db.Column(db.Boolean(), default=False)

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return "<Story {}>".format(self.id)


class Contribution(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.Text())

	author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	story_id = db.Column(db.Integer, db.ForeignKey("story.id"))

	def __init__(self, text, author, story_id):
		self.text = text
		self.author = author
		self.story_id = story_id

	def __repr__(self):
		return "<Contribution {}>".format(self.id)