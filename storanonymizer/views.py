from storanonymizer import app, models, auth, utils, db, lm
from flask import render_template, request, url_for, redirect, flash
from flask_login import login_required, logout_user, current_user
from random import choice
from operator import attrgetter
from itertools import groupby
from datetime import datetime

@app.route("/")
def index():
    stories = models.Story.query.all()
    stories.reverse()

    # calculate the number of unique contributors to a story
    for s in stories:
        contributors = []
        for r in s.rounds:
            for c in r.contributions:
                if c.author_id not in contributors:
                    contributors.append(c.author_id)
        s.contributors = contributors

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

        # Perform a uniqueness check on the username
        user = models.User.query.filter_by(name=name).first()
        if user is not None:
            flash("This user already exists")
            return redirect(url_for("register"))

        auth.register(name, pwd)
        auth.login(name, pwd)

        return redirect(url_for("index"))

    return render_template("register.html")

# One should add POST method to make this work
@app.route("/reset/bob", methods=["GET"])
def reset():
    if request.method == "POST":
        pwd = request.form["password"]
        pwd_check = request.form["password_check"]

        if pwd != pwd_check:
            flash("Passwords do not match")
            return redirect(url_for("reset"))

        auth.reset_password(14, pwd)

        return redirect(url_for("login"))

    return render_template("reset.html")

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

    # calculate the number of unique contributors to a story
    for s in stories:
        contributors = []
        for r in s.rounds:
            for c in r.contributions:
                if c.author_id not in contributors:
                    contributors.append(c.author_id)
        s.contributors = contributors

    return render_template("mystories.html", stories=stories)

@app.route("/story/<story_code>")
def story(story_code):
    story = models.Story.query.filter_by(code=story_code).first_or_404()
    rounds = models.Round.query.filter_by(story_id=story.id).all()

    return render_template("story.html", story=story, rounds=rounds)

@app.route("/story/<story_code>/ongoing")
def full_story(story_code):
    story = models.Story.query.filter_by(code=story_code).first_or_404()

    winning_contributions = []

    for round in story.rounds:
        if round.winning_contribution_id:
            c = models.Contribution.query.get(int(round.winning_contribution_id))
            winning_contributions.append(c)

    return render_template("fullstory.html", story=story, contributions=winning_contributions)

@app.route("/story/<story_code>/scoreboard")
def story_scoreboard(story_code):
    story = models.Story.query.filter_by(code=story_code).first_or_404();
    rounds = story.rounds
    contributions = []

    for r in rounds:
        if r.public_votes:
            for c in r.contributions:
                c.total_score = sum([vote.value for vote in c.votes])
                contributions.append(c)

    ranking = []

    for author_name, author_contributions in groupby(sorted(contributions, key=attrgetter("author.name")), key=attrgetter("author.name")):
        #groups.append({group: data})
        contrib_list = list(author_contributions)
        ranking.append({"author": author_name, "score": sum([c.total_score for c in contrib_list]), "avg": sum([c.total_score for c in contrib_list]) / len(contrib_list)})

    # Sort ranking in descending order
    # So the author with the highest score appears at the first index
    ranking.sort(key=lambda x: x['score'], reverse=True)

    return render_template("scoreboard.html", story=story, ranking=ranking)

@app.route("/story/<story_code>/delete")
@login_required
def delete_story(story_code):
    story = models.Story.query.filter_by(code=story_code).first()

    if current_user.id == story.user.id:
        for r in story.rounds:
            for c in r.contributions:
                delete_contribution(c.code)
            db.session.delete(r)

        db.session.delete(story)
        db.session.commit()
    else:
        return redirect(url_for("story", story_code=story.code))

    return redirect(url_for("index"))

@app.route("/story/<story_code>/delete/prompt")
@login_required
def prompt_delete_story(story_code):
    story = models.Story.query.filter_by(code=story_code).first()

    return render_template("promptdeletestory.html", story=story)

@app.route("/round/<round_code>")
def round(round_code):
    round = models.Round.query.filter_by(code=round_code).first_or_404()
    contributions = models.Contribution.query.filter_by(round_id=round.id).order_by(models.Contribution.code).all()
    userHasContributed = False

    if current_user.is_authenticated:
        if models.Contribution.query.filter_by(round_id=round.id, author_id=current_user.id).first():
            userHasContributed = True

    chance = 0

    if round.public_votes:
        winning_score = -1

        for c in contributions:
            c.total_score = sum([vote.value for vote in c.votes])

            if c.id == int(round.winning_contribution_id):
                winning_score = c.total_score

        total_score = sum([c.total_score for c in contributions])
        chance = int((winning_score / total_score) * 100)
        print(f"{winning_score} / {total_score} = {chance}%")

    return render_template("round.html", round=round, contributions=contributions, userHasContributed=userHasContributed, chance=chance)

@app.route("/story/<story_code>/settings")
@login_required
def story_settings(story_code):
    story = models.Story.query.filter_by(code=story_code).first()

    if current_user.id is not story.user.id:
        flash("You're not authorized to access the settings page!")
        return redirect("/story/{}".format(story.code))

    return render_template("storysettings.html", story=story)

@app.route("/story/<story_code>/new/round", methods=["GET", "POST"])
@login_required
def new_round(story_code):
    story = models.Story.query.filter_by(code=story_code).first()

    if request.method == "POST" and current_user.id == story.user.id:
        name = request.form["name"]

        if name == "":
            flash("Not all fields were filled in")
            return redirect(url_for("new_round", story_code=story.code))
        else:
            code = ""

            while True:
                code = utils.gen_hex(8)
                if models.Round.query.filter_by(code=code).first() is None:
                    break

            round = models.Round(name, code, story.id)

            db.session.add(round)
            db.session.commit()

            return redirect(url_for("round", round_code=round.code))

    return render_template("newround.html", story=story)

@app.route("/round/<round_code>/statistics")
def round_statistics(round_code):
    round = models.Round.query.filter_by(code=round_code).first()

    return render_template("roundstatistics.html", round=round)

@app.route("/round/<round_code>/settings")
@login_required
def round_settings(round_code):
    round = models.Round.query.filter_by(code=round_code).first()

    if current_user.id is not round.story.user.id:
        flash("You're not authorized to access the settings page!")
        return redirect("/round/{}".format(round_code))

    return render_template("roundsettings.html", round=round)

@app.route("/round/<round_code>/delete")
@login_required
def delete_round(round_code):
    round = models.Round.query.filter_by(code=round_code).first()

    if current_user.id == round.story.user.id:
        for c in round.contributions:
            delete_contribution(c.code)

        db.session.delete(round)
        db.session.commit()
    else:
        return redirect(url_for("round", round_code=round.code))

    return redirect(url_for("story", story_code=round.story.code))

@app.route("/round/<round_code>/new/contribution", methods=["GET", "POST"])
@login_required
def new_contribution(round_code):
    round = models.Round.query.filter_by(code=round_code).first()

    if request.method == "POST":
        if models.Contribution.query.filter_by(round_id=round.id, author_id=current_user.id).first():
            flash("You have already contributed to this round!")
            return redirect(url_for('round', round_code=round.code))

        text = request.form["text"].replace("\r\n", "<br>").replace("\t", "&emsp;&emsp;")
        code = ""

        while True:
            code = utils.gen_hex(8)
            if models.Contribution.query.filter_by(code=code).first() is None:
                break

        contribution = models.Contribution(text, code, current_user.id, round.id)

        db.session.add(contribution)
        db.session.commit()

        return redirect(url_for("contribution", contribution_code=contribution.code))

    return render_template("newcontribution.html", round=round)

@app.route("/my/contributions")
@login_required
def my_contributions():
    contributions = current_user.contributions

    return render_template("mycontributions.html", contributions=contributions)

@app.route("/contribution/<contribution_code>")
def contribution(contribution_code):
    contribution = models.Contribution.query.filter_by(code=contribution_code).first_or_404()

    if current_user.is_authenticated and contribution.round.voting:
        user_vote = models.Vote.query.filter_by(user_id=current_user.id, contribution_id=contribution.id).first()

        if user_vote is not None:
            return render_template("contribution.html", contribution=contribution, user_vote=user_vote.value)

    return render_template("contribution.html", contribution=contribution, user_vote=None)

@app.route("/contribution/<contribution_code>/delete")
def delete_contribution(contribution_code):
    contribution = models.Contribution.query.filter_by(code=contribution_code).first()

    if contribution.round.public_contributions:
        flash("You are not allowed to remove this contribution")
        return redirect(url_for("my_contributions"))

    if current_user.id == contribution.author.id:
        for v in contribution.votes:
            db.session.delete(v)

        db.session.delete(contribution)
        db.session.commit()

        return redirect(url_for("index"))

    return redirect(url_for("contribution", contribution_code=contribution.code))

@app.route("/round/<round_code>/votes")
def votes(round_code):
    round = models.Round.query.filter_by(code=round_code).first()
    contributions = round.contributions
    all_votes = None
    user_votes = None
    winning_score = -1

    for c in contributions:
        c.total_score = sum([vote.value for vote in c.votes])

        if c.id == int(round.winning_contribution_id):
            winning_score = c.total_score

    total_score = sum([c.total_score for c in contributions])
    chance = int((winning_score / total_score) * 100)
    print(f"{winning_score} / {total_score} = {chance}%")

    if current_user.is_authenticated:
        user_votes = models.Vote.query.filter_by(round_id=round.id, user_id=current_user.id).order_by(models.Vote.value.desc())

    if round.public_votes:
        all_votes = models.Vote.query.filter_by(round_id=round.id).all()

    return render_template("votes.html", round=round, user_votes=user_votes, ranking=contributions, all_votes=all_votes, chance=chance)

@app.route("/round/<round_code>/toggle/voting")
@login_required
def toggle_voting(round_code):
    round = models.Round.query.filter_by(code=round_code).first()

    if current_user.id == round.story.user.id:
        if round.voting:
            round.voting = False
        else:
            round.voting = True

        db.session.add(round)
        db.session.commit()

        return redirect("/round/{}/settings".format(round_code))

    return redirect("/round/{}".format(round_code))

@app.route("/round/<round_code>/toggle/publicauthors")
@login_required
def toggle_public_authors(round_code):
    round = models.Round.query.filter_by(code=round_code).first()

    if current_user.id == round.story.user.id:
        if round.public_authors:
            round.public_authors = False
        else:
            round.public_authors = True

        db.session.add(round)
        db.session.commit()

        return redirect("/round/{}/settings".format(round_code))

    return redirect("/round/{}".format(round_code))

@app.route("/round/<round_code>/toggle/publiccontributions")
@login_required
def toggle_public_contributions(round_code):
    round = models.Round.query.filter_by(code=round_code).first()

    if current_user.id == round.story.user.id:
        if round.public_contributions:
            round.public_contributions = False
        else:
            round.public_contributions = True
            round.publish_date = datetime.now()

        db.session.add(round)
        db.session.commit()

        return redirect("/round/{}/settings".format(round_code))

    return redirect("/round/{}".format(round_code))

@app.route("/round/<round_code>/toggle/publicvotes")
@login_required
def toggle_public_votes(round_code):
    round = models.Round.query.filter_by(code=round_code).first()

    if current_user.id == round.story.user.id:
        if round.public_votes:
            round.public_votes = False
        else:
            round.public_votes = True
            round.vote_date = datetime.now()

        """
         Calculate contribution with the most points from votes
        """
        contributions = round.contributions
        distribution = []

        for c in contributions:
            c.total_score = sum([vote.value for vote in c.votes])
            distribution += [c.id] * c.total_score

        # Calculate winning contribution by drawing from weighted
        # probability distribution based on votes.
        # OLD METHOD: contribution with most voting points would win
        #winning_contribution = max(contributions, key=attrgetter("total_score"))

        if round.winning_contribution_id is None:
            round.winning_contribution_id = choice(distribution)
            print(f"Winning contribution has id {round.winning_contribution_id}")
        else:
            print(f"There is already a winner. We won't change the winning contribution.")

        db.session.add(round)
        db.session.commit()

        return redirect("/round/{}/settings".format(round_code))

    return redirect("/round/{}".format(round_code))

@app.route("/vote/<contribution_code>/<value>")
@login_required
def vote(contribution_code, value):
    contribution = models.Contribution.query.filter_by(code=contribution_code).first()

    # Regular votes (i.e. non-bonus points)
    if contribution.round.voting and int(value) in range(8) and not contribution.author.id == current_user.id:
        # We use the following encoding for votes
        # 0: Explicitly remove vote for this contribution
        # 1-5: Regular vote for this contribution
        # 6: Bonus vote in originality category
        # 7: Bonus vote in style category

        vote_bonus_type = Bonus.NONE
        BONUS_VALUE = 3

        # Figure out which type of vote we are handling first
        if int(value) == 6:
            vote_bonus_type = Bonus.ORIGINALITY
            value = BONUS_VALUE
        elif int(value) == 7:
            vote_bonus_type = Bonus.STYLE
            value = BONUS_VALUE

        # Retrieve vote that might already exist
        vote = models.Vote.query.filter_by(user_id=current_user.id, contribution_id=contribution.id, bonus_type=vote_bonus_type).first()

        # If a specific bonus vote already exists,
        # a second call to this endpoint means the user wants
        # to retract its bonus vote for this contribution.
        if vote is not None and vote_bonus_type != Bonus.NONE:
            db.session.delete(vote)
        # By providing value 0, user explicitly retracts their vote
        elif value == str(0):
            db.session.delete(vote)
        # Remaining case: new vote to record
        else:
            if vote is None:
                vote = models.Vote()
                vote.contribution_id = contribution.id
                vote.user_id = current_user.id
                vote.round_id = contribution.round.id

            # Check if user had given this specific vote to
            # a different contribution already
            same_valued_vote = models.Vote.query.filter_by(user_id=current_user.id, round_id=contribution.round.id, bonus_type=vote_bonus_type, value=value).first()

            # Properly delete existing votes for other contributions
            # in the case that user gives it to this contribution instead
            if same_valued_vote is not None:
                db.session.delete(same_valued_vote)

            vote.value = value
            db.session.add(vote)

        db.session.commit()

    return redirect(url_for("contribution", contribution_code=contribution.code))
