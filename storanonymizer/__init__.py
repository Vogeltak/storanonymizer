import os
from enum import Enum
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate

app = Flask(__name__)

# Set secret key for signing sessions etc.
app.secret_key = os.environ["STORANONYMIZER_KEY"]

# Set app configs
basedir = "/data"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "escape.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create SQLAlchemy database instance
db = SQLAlchemy(app)

# Create Migrate instance
migrate = Migrate(app, db)

# Create LoginManager instance
lm = LoginManager()
lm.init_app(app)
lm.login_view = "login"

# Create Bcrypt instance
bcrypt = Bcrypt(app)

# Set up Bonus enum type to distinguish votes
Bonus = Enum("Bonus", "NONE ORIGINALITY STYLE")

from storanonymizer import views, models, auth, utils
