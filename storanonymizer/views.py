from storanonymizer import app, models, auth, db, lm
from flask import render_template, request, url_for, redirect, flash
from flask_login import login_required, logout_user, current_user

@app.route("/")
def index():
	stories = models.Story.query.all()

	return render_template("home.html", stories=stories)

@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		name = request.form["name"]
		pwd = request.form["password"]

		if auth.login(name, pwd):
			return redirect(url_for("index"))
		else:
			flash("Username and/or password are incorrect")
			return redirect(url_for("login"))

	return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
	if request.method == "POST":
		name = request.form["name"]
		pwd = request.form["password"]
		pwd_check = request.form["password_check"]

		# Perform a check on all form field values
		# to make sure nothing is blank, because that
		# would break the system
		if name == "":
			flash("Not all fields were filled in")
			return redirect(url_for("register"))
		if pwd == "":
			flash("Not all fields were filled in")
			return redirect(url_for("register"))
		if pwd_check == "":
			flash("Not all fields were filled in")
			return redirect(url_for("register"))

		# Password and password_check should contain
		# same string, to make sure the user entered
		# their desired password
		if pwd != pwd_check:
			flash("Passwords do not match")
			return redirect(url_for("register"))

		auth.register(name, pwd)
		auth.login(name, pwd)

		return redirect(url_for("index"))

	return render_template("register.html")

@app.route("/new/story", methods=["GET", "POST"])
@login_required
def new_story():
	if request.method == "POST":
		name = request.form["name"]

		if name == "":
			flash("Not all fields were filled in")
			return redirect(url_for("new_story"))
		else:
			story = models.Story(name)
			story.user_id = current_user.id
			
			db.session.add(story)
			db.session.commit()

			return redirect("/story/{}".format(story.id))

	return render_template("newstory.html")

@app.route("/my/stories")
@login_required
def my_stories():
	stories = current_user.stories

	return render_template("mystories.html", stories=stories)

@app.route("/story/<story_id>")
def story(story_id):
	story = models.Story.query.get(story_id)

	return render_template("story.html", story=story)

@app.route("/story/<story_id>/settings")
@login_required
def story_settings(story_id):
	story = models.Story.query.get(story_id)

	if current_user.id is not story.user.id:
		flash("You're not authorized to access the settings page!")
		return render_template("story.html", story=story)

	return render_template("storysettings.html", story=story)

@app.route("/story/<story_id>/toggle/publicauthors")
@login_required
def toggle_public_authors(story_id):
	story = models.Story.query.get(story_id)

	if current_user.id == story.user.id:
		if story.public_authors:
			story.public_authors = False
		else:
			story.public_authors = True

		db.session.add(story)
		db.session.commit()

		return redirect("/story/{}/settings".format(story_id))

	return redirect("/story/{}".format(story_id))

@app.route("/story/<story_id>/toggle/publiccontributions")
@login_required
def toggle_public_contributions(story_id):
	story = models.Story.query.get(story_id)

	if current_user.id == story.user.id:
		if story.public_contributions:
			story.public_contributions = False
		else:
			story.public_contributions = True

		db.session.add(story)
		db.session.commit()

		return redirect("/story/{}/settings".format(story_id))

	return redirect("/story/{}".format(story_id))