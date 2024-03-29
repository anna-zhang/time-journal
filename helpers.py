import os
import requests
import urllib.parse
import datetime

from flask import redirect, render_template, request, session
from functools import wraps


def current_date():
    d = datetime.datetime.today()
    date = d.strftime('%Y-%m-%d')
    return date


def timespent(start, end):
    FMT = '%H:%M'
    start_time = datetime.datetime.strptime(start, FMT)
    end_time = datetime.datetime.strptime(end, FMT)
    # returns a timedelta object
    duration = end_time - start_time
    seconds = datetime.timedelta.total_seconds(duration)
    if seconds < 0:
        seconds = seconds + 86400
    minutes = seconds / 60

    minutes = round(minutes, 2)
    return(minutes)

# print(timespent("20:30", "01:30"))
# print(timespent("20:30", "22:30"))


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(session)
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
