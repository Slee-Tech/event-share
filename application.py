from flask import Flask, session, flash, redirect, render_template, request, session
from flask_session import Session
from flask import jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from datetime import datetime, date

app = Flask(__name__)

# Set up database
engine = create_engine("sqlite:///event.db")
db = scoped_session(sessionmaker(bind=engine))

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
def index():
    query = db.execute("SELECT * FROM users").fetchall()
    db.commit()
    return render_template("index.html", sample=query)

@app.route('/home', methods=["GET", "POST"])
def home():

    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("home.html", error="You failed to enter a username.")
        elif not request.form.get("password"):
            return render_template("home.html", error="You failed to enter a password.")
        rows = db.execute("SELECT * FROM users WHERE name = :username", {"username":request.form.get("username")}).fetchone()
        db.commit()
        
        if not rows: #check_password_hash(rows["hash"], request.form.get("password"))
            return render_template("home.html", error="No such user")

        session["user_id"] = rows["id"]
        session["name"] = rows["name"]

        return render_template("home.html", name=session["name"])
    else:
        return render_template("home.html", name=session["name"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route('/register', methods=["POST"])
def register():
    if not request.form.get("new_user"):
        return render_template("error.html", error="No name entered")

    elif not request.form.get("new_password"):
        return render_template("error.html", error="No password entered")

    #elif not request.form.get("password") == request.form.get("confirmation"):
        #return render_template("login.html")

    hash = generate_password_hash(request.form.get("new_password"))
    user = request.form.get("new_user")
    result = db.execute("INSERT INTO users (name, password) VALUES(:username, :hash)", {"username":user, "hash":hash})
    db.commit()
    session["name"] = user
    
    get_user_id = db.execute("SELECT * FROM users WHERE name = :username", {"username":user}).fetchone()
    db.commit()
    session["user_id"] = get_user_id["id"]

    return redirect("/home")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/share', methods=["GET", "POST"])
def share():
    if request.method == "GET":
        return render_template("share.html", error="", success="")
    else:
        if not request.form.get("event_name"):
            return render_template("share.html", error="You failed to name the event.")
        elif not request.form.get("event_location"):
            return render_template("share.html", error="You failed to give the location of the event.")
        elif not request.form.get("event_date"):
            return render_template("share.html", error="You failed to state the date of the event.")
        elif not request.form.get("event_time"):
            return render_template("share.html", error="You failed to state when the event is.")
        elif not request.form.get("event_am_pm"):
            return render_template("share.html", error="You failed to specify if the event is in the AM or PM.")
        elif not request.form.get("event_desc"):
            return render_template("share.html", error="You failed to describe the event.")
        else:
            name = request.form.get("event_name")
            location = request.form.get("event_location")
            date = request.form.get("event_date")
            time = request.form.get("event_time")
            am_pm = request.form.get("event_am_pm")
            description = request.form.get("event_desc")
            poster_id = session["user_id"]
        db.execute("INSERT INTO events (name, description, date, time, hour, location, userid) VALUES(:name, :desc, :date, :time, :hour, :loc, :id)", {"name":name, "desc":description, "date":date, "time":time, "hour":am_pm, "loc":location, "id":poster_id})
        db.commit()
        return render_template("share.html", error="", success="Event added successfully. Add another event if you'd like.")



    # needs to handle form submission for new event on POST request 
    # GET will render share template
    # will event add to events table
    # may redirect back to home
    

@app.route('/view', methods=["GET", "POST"])
def view():
    events_list = db.execute("SELECT * FROM events").fetchall()
    db.commit()
    return render_template("events.html", events=events_list)
    # should show a list of all current events, show in a table - done
    # should allow users to register, unless they added the event, then allow user to edit or delete
    # should show list of registered attendees from attendees table, a dropdown by clicking somewhere in event table

