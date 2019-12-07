import os
import json
import math

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, current_date, timespent

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "supersecretkey"
# Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///timejournal.db")

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/timelog", methods=["GET", "POST"])
@login_required
def timejournal():
    """Show journal for the day"""
    # If POST or GET
    if request.method == "POST" or request.method == "GET":
        # Get the date the user selects. If user does not submit a date, get the current date.
        if not request.form.get("date"):
            date = current_date()
        else:
            date = request.form.get("date")

        # Get the information for all activities the user did on that chosen date
        rows = db.execute("SELECT name, category, timespent, notes, rating, minutes FROM activities WHERE userid = :user_id AND date = :date ORDER BY start", user_id=session["user_id"], date=date)

        # If no activities logged for that date and user, display an empty journal message.
        if len(rows) == 0:
            return render_template("nothing.html", date=date)

        # Calculate total number of hours spent in each category
        sleep_hours = 0
        class_hours = 0
        schoolwork_hours = 0
        extracurricular_hours = 0
        work_hours = 0
        exercise_hours = 0
        food_hours = 0
        fun_hours = 0
        other_hours = 0
        sad_hours = 0
        happy_hours = 0
        for row in rows:
            if row["category"] == "Sleep":
                sleep_hours += row["timespent"]
            if row["rating"] == "disliked":
                sad_hours += row["timespent"]
            if row["rating"] == "liked":
                happy_hours += row["timespent"]
            if row["category"] == "Class":
                class_hours += row["timespent"]
            if row["category"] == "Schoolwork":
                schoolwork_hours += row["timespent"]
            if row["category"] == "Extracurricular":
                extracurricular_hours += row["timespent"]
            if row["category"] == "Work":
                work_hours += row["timespent"]
            if row["category"] == "Exercise":
                exercise_hours += row["timespent"]
            if row["category"] == "Food":
                food_hours += row["timespent"]
            if row["category"] == "Fun":
                fun_hours += row["timespent"]
            if row["category"] == "Other":
                other_hours += row["timespent"]
        # Create a dictionary to store the category and the corresponding total hours spent doing things in that category
        category_hours = {}
        category_hours["Sleep"] = sleep_hours
        category_hours["Class"] = class_hours
        category_hours["Schoolwork"] = schoolwork_hours
        category_hours["Extracurricular"] = extracurricular_hours
        category_hours["Work"] = work_hours
        category_hours["Exercise"] = exercise_hours
        category_hours["Food"] = food_hours
        category_hours["Fun"] = fun_hours
        category_hours["Other"] = other_hours
        total_hours = sleep_hours + class_hours + schoolwork_hours + extracurricular_hours + work_hours + exercise_hours + food_hours + fun_hours + other_hours
        hours_remaining = 24 - total_hours
        # Create a list of all categories
        category_list = {"Sleep", "Class", "Schoolwork", "Extracurricular", "Work", "Exercise", "Food", "Fun", "Other"}

        # Get all of the total hours spent in each category for a user on a specific date
        summary_rows = db.execute("SELECT * FROM timesummary WHERE userid = :user_id AND date = :date", user_id=session["user_id"], date=date)
        # If there is no information stored about category time totals for a user on a specific date, add the information to the database based on the above calculated category hours
        if len(summary_rows) < 1:
            # Iterate through category list, for each of the categories, insert the total hours into the database
            for category in category_list:
                db.execute("INSERT INTO timesummary (userid, date, category, total, minutes) VALUES (:user_id, :date, :category_name, :total, :minutes)", user_id=session["user_id"], date=date, category_name=category, total=category_hours[category], minutes=round((category_hours[category])*60))
            # Insert the number of total hours the user spent in activites rated as "liked" on a specific day
            db.execute("INSERT INTO timesummary (userid, date, category, total, minutes) VALUES (:user_id, :date, :emotion, :total, :minutes)", user_id=session["user_id"], date=date, emotion="Happy", total=happy_hours, minutes=round(happy_hours*60))
            # Insert the number of total hours the user spent in activites rated as "disliked" on a specific day
            db.execute("INSERT INTO timesummary (userid, date, category, total, minutes) VALUES (:user_id, :date, :emotion, :total, :minutes)", user_id=session["user_id"], date=date, emotion="Sad", total=sad_hours, minutes=round(sad_hours*60))

        # If there already exists information stored about category time totals for a user on a specific date, update the information to the database based on the above calculated category hours (since users may have added new activity entries for a date)
        else:
            # Iterate through category list, for each of the categories, update the total hours into the databse
            for category in category_list:
                db.execute("UPDATE timesummary SET total = :total, minutes = :minutes WHERE userid = :user_id AND category = :category_name AND date = :date", total=category_hours[category], user_id=session["user_id"], category_name=category, date=date, minutes=round((category_hours[category])*60))
            # Update the number of total hours the user spent in activites rated as "liked" on a specific day
            db.execute("UPDATE timesummary SET total = :total, minutes = :minutes WHERE userid = :user_id AND category = :emotion AND date = :date", user_id=session["user_id"], date=date, emotion="Happy", total=happy_hours, minutes=round(happy_hours*60))
            # Update the number of total hours the user spent in activites rated as "disliked" on a specific day
            db.execute("UPDATE timesummary SET total = :total, minutes = :minutes WHERE userid = :user_id AND category = :emotion AND date = :date", user_id=session["user_id"], date=date, emotion="Sad", total=sad_hours, minutes=round(sad_hours*60))

        # Get all of the total hours spent in each category for a user on a specific date (updated)
        summary_rows = db.execute("SELECT * FROM timesummary WHERE userid = :user_id AND date = :date AND total != 0 AND category != 'Happy' AND category != 'Sad' ORDER BY total DESC", user_id=session["user_id"], date=date)

        # Advice
        list_of_advice = []
        # If the user logged less than 7 hours spent for activities in the "sleep" category, recommend for the user to sleep more.
        if sleep_hours < 7:
            advice = "You should sleep more. Research shows that getting seven to eight hours of sleep every night is good for your health."
            list_of_advice.append(advice)
        # If the user logged more hours spent doing activities that they rated as "disliked" than "liked", recommend for the user to do more activities that they enjoy doing.
        if happy_hours < sad_hours:
            advice = "You're doing more things that make you unhappy than that make you happy. Try to do more of what you love!"
            list_of_advice.append(advice)
        # If the user logged less than half an hour spent for activities in the "exercise" category, recommend for the user to exercise more.
        if exercise_hours < 0.5:
            advice = "You should exercise more. You should aim for at least 30 minutes of physical activity of moderate intensity every day."
            list_of_advice.append(advice)
        # If the user logged less than 1 hour spent for activities in the "food" category, check to make sure the user is eating enough.
        if food_hours < 1:
            advice = "Make sure you are eating proper meals. You didn't spend much time eating today."
            list_of_advice.append(advice)
        # If there is no advice, just say they are doing great.
        if len(list_of_advice) == 0:
            list_of_advice.append("You're doing great! Keep doing what you're doing.")


        list_of_data = [["Activity", "Hours per Day"], ["Not logged", hours_remaining]]
        for activity in summary_rows:
            list_to_add = []
            list_to_add.append(activity["category"])
            list_to_add.append(activity["total"])
            list_of_data.append(list_to_add)
        pie_data = json.dumps(list_of_data)

        return render_template("timelog.html", rows=rows, summary_rows=summary_rows, date=date, list_of_advice=list_of_advice, list_of_data=list_of_data, pie_data=pie_data)

@app.route("/entry", methods=["GET", "POST"])
@login_required
def entry():
    """Add a new activity entry"""
    if request.method == "POST":
        if not request.form.get("activity"):
            return apology("must provide an activity name", 403)
        # can make timespent optional later
        # elif not request.form.get("timespent"):
        #     return apology("must provide hours spent doing the activity", 403)
        elif not request.form.get("start"):
            return apology("must provide activity start time", 403)
        elif not request.form.get("end"):
            return apology("must provide activity end time", 403)
        elif not request.form.get("date"):
            return apology("must provide date of the activity", 403)
        elif not request.form.get("category"):
            return apology("must provide category of the activity", 403)
        elif not request.form.get("rating"):
            return apology("must rate the activity", 403)
        activity_name = request.form.get("activity")
        # time_spent = request.form.get("timespent")
        start_time = request.form.get("start")
        end_time = request.form.get("end")
        activity_date = request.form.get("date")
        activity_category = request.form.get("category")
        activity_notes = request.form.get("notes")
        activity_rating = request.form.get("rating")
        activity_minutes = timespent(start_time, end_time)
        activity_hours = activity_minutes / 60
        activity_duration = round(activity_hours, 2)
        if activity_notes == None:
            db.execute("INSERT INTO activities (user, name, category, timespent, start, end, date, rating, minutes) VALUES (:user_id, :name, :category, :timespent, :start, :end, :date, :rating, :minutes)", user_id=session["user_id"], name=activity_name, category=activity_category, timespent=activity_duration, start=start_time, end=end_time, date=activity_date, rating=activity_rating, minutes=activity_minutes)
        else:
            db.execute("INSERT INTO activities (userid, name, category, timespent, start, end, date, notes, rating, minutes) VALUES (:user_id, :name, :category, :timespent, :start, :end, :date, :notes, :rating, :minutes)", user_id=session["user_id"], name=activity_name, category=activity_category, timespent=activity_duration, start=start_time, end=end_time, date=activity_date, notes=activity_notes, rating=activity_rating, minutes=activity_minutes)
        return redirect("/timelog")
    else:
        return render_template("entry.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        print(session)

        # Redirect user to timelog
        return redirect("/timelog")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to index
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # If method is POST
    if request.method == "POST":
        # Check to make sure user inputted a username
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)
        # Make sure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)
        # Query database for username
        username = request.form.get("username")
        password = request.form.get("password")
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        # Check to make sure the username is unique
        if len(rows) == 1:
            return apology("username already taken", 403)
        # If it is unique, add the user to the database
        else:
            pass_hash = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :pass_hash)", username=username, pass_hash=pass_hash)
            return redirect("/timelog")
    # If method is GET
    else:
        return render_template("register.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
