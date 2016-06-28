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
	story = models.Story.query.filter_by(code=story_code).first_or_404()
	contributions = models.Contribution.query.filter_by(story_id=story.id).order_by(models.Contribution.code).all()
	userHasContributed = False

	if models.Contribution.query.filter_by(story_id=story.id, author_id=current_user.id).first():
		userHasContributed = True

	return render_template("story.html", story=story, contributions=contributions, userHasContributed=userHasContributed)

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
		if models.Contribution.query.filter_by(story_id=story.id, author_id=current_user.id).first():
			flash("You have already contributed to this story!")
			return redirect(url_for('story', story_code=story.code))

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
	contribution = models.Contribution.query.filter_by(code=contribution_code).first_or_404()
	
	if current_user.is_authenticated and contribution.story.voting:
		user_vote = models.Vote.query.filter_by(user_id=current_user.id, contribution_id=contribution.id).first()

		if user_vote is not None:
			return render_template("contribution.html", contribution=contribution, user_vote=user_vote.value)

	return render_template("contribution.html", contribution=contribution, user_vote=None)

@app.route("/contribution/<contribution_code>/delete")
def delete_contribution(contribution_code):
	contribution = models.Contribution.query.filter_by(code=contribution_code).first()

	if current_user.id == contribution.author.id:
		for v in contribution.votes:
			db.session.delete(v)

		db.session.delete(contribution)
		db.session.commit()

		return redirect(url_for("index"))

	return redirect(url_for("contribution", contribution_code=contribution.code))

@app.route("/story/<story_code>/votes")
def votes(story_code):
	story = models.Story.query.filter_by(code=story_code).first()
	contributions = story.contributions
	all_votes = None
	user_votes = None
	
	for c in contributions:
		c.total_score = sum([vote.value for vote in c.votes])

	if current_user.is_authenticated:
		user_votes = models.Vote.query.filter_by(story_id=story.id, user_id=current_user.id).order_by(models.Vote.value.desc())
	
	if story.public_votes:
		all_votes = models.Vote.query.filter_by(story_id=story.id).all()

	return render_template("votes.html", story=story, user_votes=user_votes, ranking=contributions, all_votes=all_votes)

@app.route("/story/<story_code>/toggle/voting")
@login_required
def toggle_voting(story_code):
	story = models.Story.query.filter_by(code=story_code).first()

	if current_user.id == story.user.id:
		if story.voting:
			story.voting = False
		else:
			story.voting = True

		db.session.add(story)
		db.session.commit()

		return redirect("/story/{}/settings".format(story_code))

	return redirect("/story/{}".format(story_code))

@app.route("/story/<story_code>/toggle/publicvotes")
@login_required
def toggle_public_votes(story_code):
	story = models.Story.query.filter_by(code=story_code).first()

	if current_user.id == story.user.id:
		if story.public_votes:
			story.public_votes = False
		else:
			story.public_votes = True

		db.session.add(story)
		db.session.commit()

		return redirect("/story/{}/settings".format(story_code))

	return redirect("/story/{}".format(story_code))

@app.route("/vote/<contribution_code>/<value>")
@login_required
def vote(contribution_code, value):
	contribution = models.Contribution.query.filter_by(code=contribution_code).first()

	if contribution.story.voting and str(value) in "0123" and not contribution.author.id == current_user.id:
		vote = models.Vote.query.filter_by(user_id=current_user.id, contribution_id=contribution.id).first()

		if value == 0:
			db.session.delete(vote)
		else:
			if vote is None:
				vote = models.Vote()
				vote.contribution_id = contribution.id
				vote.user_id = current_user.id
				vote.story_id = contribution.story.id

			same_valued_vote = models.Vote.query.filter_by(user_id=current_user.id, story_id=contribution.story.id, value=value).first()

			if same_valued_vote is not None:
				db.session.delete(same_valued_vote)

			vote.value = value
			db.session.add(vote)

		db.session.commit()

	return redirect(url_for("contribution", contribution_code=contribution.code))