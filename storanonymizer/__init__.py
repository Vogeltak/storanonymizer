import os
from enum import Enum
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate

app = Flask(__name__)

# Set secret key for signing sessions etc.
# REMEMBER TO CHANGE THIS BEFORE DEPLOYING TO PRODUCTION
app.secret_key = b"\x8b\x19\x0ei\xe3\x87YC\x0b\xdf\x9a6\xdf\xbe\xdf\xd2\xce\xd0\x8f\xa3\xe5\xfen\xe0\xc3\x91U\xc6\xc1\x9f*\xfc |k\r\xac\xb9\xe8o\x97\x8bK\xf5\rf\x03\x04\xe40"

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
