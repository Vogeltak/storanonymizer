from storanonymizer import db, lm, bcrypt, models
from flask_login import login_user, logout_user

@lm.user_loader
def load_user(user_id):
	return models.User.query.get(int(user_id))

def login(name, pwd):
	user = models.User.query.filter_by(name=name).first()

	if user is None:
		return False

	if bcrypt.check_password_hash(user.password_hash, pwd):
		login_user(user)
		return True
	else:
		return False

def register(name, pwd):
	pwd_hash = bcrypt.generate_password_hash(pwd)

	user = models.User(name, pwd_hash)

	db.session.add(user)
	db.session.commit()

def reset_password(id, pwd):
	user = load_user(id)
	user.password_hash = bcrypt.generate_password_hash(pwd)
	db.session.commit()
