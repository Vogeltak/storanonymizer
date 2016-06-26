from storanonymizer import app, models, auth, utils, db, lm
from flask import render_template, request, url_for, redirect, flash
from flask_login import login_required, logout_user, current_user
from random import shuffle

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
			code = ""

			while True:
				code = utils.gen_hex(8)
				if models.Story.query.filter_by(code=code).first() is None:
					break

			story = models.Story(name, code, current_user.id)
			
			db.session.add(story)
			db.session.commit()

			return redirect(url_for("story", story_code=story.code))

	return render_template("newstory.html")

@app.route("/my/stories")
@login_required
def my_stories():
	stories = current_user.stories

	return render_template("mystories.html", stories=stories)

@app.route("/story/<story_code>")
def story(story_code):
	story = models.Story.query.filter_by(code=story_code).first()
	contributions = story.contributions
	shuffle(contributions)

	return render_template("story.html", story=story, contributions=contributions)

@app.route("/story/<story_code>/settings")
@login_required
def story_settings(story_code):
	story = models.Story.query.filter_by(code=story_code).first()

	if current_user.id is not story.user.id:
		flash("You're not authorized to access the settings page!")
		return redirect("/story/{}".format(story_code))

	return render_template("storysettings.html", story=story)

@app.route("/story/<story_code>/toggle/publicauthors")
@login_required
def toggle_public_authors(story_code):
	story = models.Story.query.filter_by(code=story_code).first()

	if current_user.id == story.user.id:
		if story.public_authors:
			story.public_authors = False
		else:
			story.public_authors = True

		db.session.add(story)
		db.session.commit()

		return redirect("/story/{}/settings".format(story_code))

	return redirect("/story/{}".format(story_code))

@app.route("/story/<story_code>/toggle/publiccontributions")
@login_required
def toggle_public_contributions(story_code):
	story = models.Story.query.filter_by(code=story_code).first()

	if current_user.id == story.user.id:
		if story.public_contributions:
			story.public_contributions = False
		else:
			story.public_contributions = True

		db.session.add(story)
		db.session.commit()

		return redirect("/story/{}/settings".format(story_code))

	return redirect("/story/{}".format(story_code))

@app.route("/story/<story_code>/delete")
@login_required
def delete_story(story_code):
	story = models.Story.query.filter_by(code=story_code).first()

	if current_user.id == story.user.id:
		for c in story.contributions:
			db.session.delete(c)

		db.session.delete(story)
		db.session.commit()
	else:
		return redirect(url_for("story", story_code=story.code))

	return redirect(url_for("index"))

@app.route("/story/<story_code>/new/contribution", methods=["GET", "POST"])
@login_required
def new_contribution(story_code):
	story = models.Story.query.filter_by(code=story_code).first()

	if request.method == "POST":
		text = request.form["text"].replace("\r\n", "<br>")
		code = ""

		while True:
			code = utils.gen_hex(8)
			if models.Contribution.query.filter_by(code=code).first() is None:
				break

		contribution = models.Contribution(text, code, current_user.id, story.id)

		db.session.add(contribution)
		db.session.commit()

		return redirect(url_for("contribution", contribution_code=contribution.code))

	return render_template("newcontribution.html", story=story)

@app.route("/my/contributions")
@login_required
def my_contributions():
	contributions = current_user.contributions

	return render_template("mycontributions.html", contributions=contributions)

@app.route("/contribution/<contribution_code>")
def contribution(contribution_code):
	contribution = models.Contribution.query.filter_by(code=contribution_code).first()

	return render_template("contribution.html", contribution=contribution)

@app.route("/contribution/<contribution_code>/delete")
def delete_contribution(contribution_code):
	contribution = models.Contribution.query.filter_by(code=contribution_code).first()

	if current_user.id == contribution.author.id:
		db.session.delete(contribution)
		db.session.commit()

		return redirect(url_for("index"))

	return redirect(url_for("contribution", contribution_code=contribution.code))
