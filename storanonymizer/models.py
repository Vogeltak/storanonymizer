from storanonymizer import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(1024))

    stories = db.relationship("Story", backref="user", lazy="select")
    contributions = db.relationship("Contribution", backref="author", lazy="select")
    votes = db.relationship("Vote", backref="user", lazy="select")

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
    code = db.Column(db.String(), unique=True)
    name = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    rounds = db.relationship("Round", backref="story", lazy="select")

    def __init__(self, name, code, user_id):
        self.name = name
        self.code = code
        self.user_id = user_id

    def __repr__(self):
        return "<Story {}>".format(self.id)

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    code = db.Column(db.String(), unique=True)

    contributions = db.relationship("Contribution", backref="round", lazy="select")
    votes = db.relationship("Vote", backref="round", lazy="select")

    # ID of the contribution that won the round
    winning_contribution_id = db.Column(db.String())

    story_id = db.Column(db.Integer, db.ForeignKey("story.id"))

    public_authors = db.Column(db.Boolean(), default=False)
    public_contributions = db.Column(db.Boolean(), default=False)
    voting = db.Column(db.Boolean(), default=False)
    public_votes = db.Column(db.Boolean(), default=False)

    def __init__(self, name, code, story_id):
        self.name = name
        self.code = code
        self.story_id = story_id

    def __repr__(self):
        return "<Round {}>".format(self.id)

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(), unique=True)
    text = db.Column(db.Text())

    votes = db.relationship("Vote", backref="contribution", lazy="select")

    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    round_id = db.Column(db.Integer, db.ForeignKey("round.id"))

    def __init__(self, text, code, author_id, round_id):
        self.text = text
        self.code = code
        self.author_id = author_id
        self.round_id = round_id

    def __repr__(self):
        return "<Contribution {}>".format(self.id)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)
    contribution_id = db.Column(db.Integer, db.ForeignKey("contribution.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    round_id = db.Column(db.Integer, db.ForeignKey("round.id"))

    def __repr__(self):
        return "<Vote {}>".format(self.id)
