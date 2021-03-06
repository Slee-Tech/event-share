from flask import Flask, session, flash, redirect, render_template, request, session, url_for
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
# uncomment to allow hitting back button after logging in
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
    # handles request for loading submission form
    if request.method == "GET":
        return render_template("share.html", error="", success="")
    else:
        # handles POST submissions
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
        
        # checks to see if form was submitted from edit page and if it should be updated
        if request.form.get("save_changes"):
            event_id = request.form.get("delete_event_id")
            db.execute("UPDATE events SET name=:n, description=:d, date=:date, time=:t, hour=:h, location=:l WHERE id = :id", {"n": name, "d":description, "date":date, "t":time, "h":am_pm, "l":location,"id": event_id})
            db.commit()
            message = f"successfully edited event. Add another if you'd like."
            return render_template("share.html", error="", success=message)
        
        # checks if event was submitted to be deleted
        elif request.form.get("delete_event"):
            event_id = request.form.get("delete_event_id")
            event = session["events"]
            # using list comprehension to get the ids of events in session["events"] to access index
            ev_ids = [ev[0] for ev in event]
            # removes event if id is found in list of ids
            for i, ev in enumerate(ev_ids):
                if ev == int(event_id):
                    session["events"].pop(i)
            db.execute("DELETE FROM events WHERE id = :id", {"id": event_id})
            db.commit()
            test = f"Event with id of {event_id} was successfully deleted and {ev_ids}"
            message = "You event was successfully deleted."
            return render_template("events.html", events=session["events"], attend=session["attendees"], success=message)
        # this means the form was submitted from share page
        else:
            db.execute("INSERT INTO events (name, description, date, time, hour, location, userid) VALUES(:name, :desc, :date, :time, :hour, :loc, :id)", {"name":name, "desc":description, "date":date, "time":time, "hour":am_pm, "loc":location, "id":poster_id})
            db.commit()
            return render_template("share.html", error="", success="Event added successfully. Add another event if you'd like.")

@app.route('/view', methods=["GET", "POST"])
def view():
    events_list = db.execute("SELECT * FROM events").fetchall()
    # this query should get all of the data needed, gives event info, attendees names, and user_id of creator, will have to edit events template
    event_info = db.execute("SELECT users.name as username, events.* FROM users JOIN attendees on users.id = attendees.user_id join events on attendees.event_id = events.id").fetchall();
    # adds unique event ids from query as keys into dict, then chains registered attendees to each bucket 
    attendees = {}
    if event_info:
        for events in event_info:
            if events.id not in attendees:
                attendees[events.id] = []
            attendees[events.id].append(events.username)
    else:
        # still creates index if no attendees are registered
        for events in events_list:
            if events.id not in attendees:
                attendees[events.id] = []

    session["events"] = events_list
    session["attendees"] = attendees

    db.commit()
    return render_template("events.html", events=events_list, attend=attendees, success="")
    # should show a list of all current events, show in a table - done
    # should allow users to register, unless they added the event, then allow user to edit or delete - done
    # should show list of registered attendees from attendees table, a dropdown by clicking somewhere in event table -done

@app.route('/view/<string:event_id>', methods=["POST"])
def attend(event_id):
        # posting the attend form should bring to a confirmation page then redirect with the updated list
        # will add user to list of registered attendees table and give a confirmation
        # will have to add in session["user_id"] and event id as argument then insert into attendees table
    ev_id = event_id
    event = db.execute("SELECT * FROM events WHERE id = :id", {"id": ev_id}).fetchone()
    db.execute("INSERT INTO attendees (event_id, user_id) VALUES(:ev_id, :u_id)", {"ev_id":ev_id, "u_id":session["user_id"]})
    db.commit()
    session["attendees"][int(ev_id)].append(session["name"])
    # now insert user and event id into attendees to update
    message = f"You've successfully registered to attend the {event.name} event. Continue browsing events."
    return render_template("events.html", events=session["events"], attend=session["attendees"], success=message)

@app.route('/view/edit/<string:event_id>', methods=["GET", "POST"])
def edit(event_id):
    if request.method == "GET":
        event = db.execute("SELECT * FROM events WHERE id = :id", {"id": event_id}).fetchone()
        db.commit()
        return render_template("edit.html", ev=event)
