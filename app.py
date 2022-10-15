import sqlite3
import os
import datetime as dt
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from flask import Flask, render_template, request, redirect, session, Response
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from helper_functions import error, login_required

# Configure app
app = Flask(__name__)
# configure app not to cache responses
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Load environment variables
load_dotenv()

# Configure the app to use filesystem instead of signed cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
Session(app)


# Welcome page
@app.route("/")
def homepage():
    return render_template("homepage.html")


@app.route("/", methods=["GET", "POST"], subdomain="parse")
def parse():
    # Set up a sql connection

    connection = sqlite3.connect("owmail.db")
    db = connection.cursor() 
    
    # Insert into the email db all emails that might have been POSTed to /parse by the parse webhook
    db.execute("INSERT INTO emails (sender, recipients, subject, content) VALUES (:sender, :recipients, :subject, :content)",
    {"sender": request.form.get("from"), "recipients": request.form.get("to"), "subject": request.form.get("subject"), 
    "content": request.form.get("text")})
    connection.commit()
    connection.close()
    # Tell the parser that we recieved the email
    status_code = Response(status=200)
    return status_code

# Inbox
@app.route("/inbox", methods=["GET"])
@login_required
def inbox():
    # Set up a sql connection
    connection = sqlite3.connect("owmail.db")
    db = connection.cursor()

    # Retrieve all emails from the db for this user
    emails = db.execute("SELECT * FROM emails WHERE recipients = :address", {"address": session["user_address"]})

    # Check if user has emails
    return render_template("inbox.html", emails=emails)


# View a full email
@app.route("/email", methods=["GET", "POST"])
@login_required
def email():
    # Set up a sql connection
    connection = sqlite3.connect("owmail.db")
    db = connection.cursor()

    # Access the email_id through an HTML button
    email_id = request.form.get("email_id")
    db.execute("SELECT * From emails WHERE email_id = :email_id", {"email_id": email_id})
    email = db.fetchall()
    return render_template("full_email.html", email=email)

# Send an Email
@app.route("/send", methods=["GET", "POST"])
@login_required
def send():
    # Set up a sql connection
    connection = sqlite3.connect("owmail.db")
    db = connection.cursor()
    # If information is submitted through a form, handle the post request
    if request.method == "POST":
        # Check if subject or text is empty
        if not request.form.get("subject") or not request.form.get("text"):
            return error("Please include a subject and content", 403)
        else:
            # Collect current date
            now = dt.datetime.now()
            date_time = now.strftime("%a, %b %-d, %Y, %-I:%M %p")
            # Insert into email DB
            db.execute("INSERT INTO emails (sender, recipients, subject, content, date_time) VALUES (:sender, :recipients, :subject, :content, :date_time)", 
            {"sender": session["user_address"], "recipients": request.form.get("to"), 
            "subject": request.form.get("subject"), "content": request.form.get("text"), "date_time": date_time})
            connection.commit()
            connection.close()

            # Send email with sendgrid api
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            #user_id = str(session["user_address"])
            from_email = Email(session["user_address"])
            to_email = To(request.form.get("to"))
            subject = str(request.form.get("subject"))
            content = Content("text/plain", request.form.get("text"))
            
            mail = Mail(from_email, to_email, subject, content)

            sg.send(mail)
            

            return redirect("/inbox")
    else:
        return render_template("send.html")

# Can't accept sign ups because of security reasons
@app.route("/signup", methods=["GET", "POST"])
def signup():
    return render_template("signup.html")
#     # return render_template("signup.html")
#     # Set up a sql connection
#     connection = sqlite3.connect("owmail.db")
#     db = connection.cursor()

#     # If information is submitted through a form, handle the post request
#     if request.method == "POST":
#         # Ensure all fields are filled
#         if not request.form.get("address") or not request.form.get("password") or not request.form.get("confirm"):
#             return error("Missing Fields", 400)

#         # Ensure address ends in "@owmail.co"
#         if not request.form.get("address").endswith("@owmail.co"):
#             return error("Email address must end in '@owmail.co'", 400)

#         # Ensure address is more than 4 chars
#         if len(request.form.get("address")) < 13:
#             return error("Email address must be more than 4 characters", 400)

#         # Ensure password and confirmation match
#         if request.form.get("password") != request.form.get("confirm"):
#             return error("Password and Confirmation do not match", 400)

#         # Ensure address is available
#         rows = db.execute("SELECT * FROM users WHERE address = :address", {"address": request.form.get("address")})
#         for tuple in rows:
#             # See if in the first tuple, the 2nd element is the address entered by the user
#             if tuple[1] == request.form.get("address"):
#                 return error("Sorry, that Owmail Address is already taken", 400)

#         # If signup was succesful, add the new user to the database
#         password = generate_password_hash(request.form.get("password"))
#         db.execute("INSERT INTO users (address, password) VALUES (:address, :password)", 
#         {"address": request.form.get("address"), "password": password})
        
#         # Save the user session
#         db.execute("SELECT id FROM users WHERE address = :address", 
#         {"address": request.form.get("address")})
#         row = db.fetchall()
#         session["user_id"] = row[0][0]
#         session["user_address"] = request.form.get("address")
#         # Save changes, close connection, and then redirect to inbox
#         connection.commit()
#         connection.close()
#         return redirect("/inbox")
#     else:
#         if not session:
#             return render_template("signup.html")
#         else:
#             session.clear()
#             return render_template("signup.html")
# Log in    
@app.route("/login", methods=["GET", "POST"])
def login():
    # Set up sqlite connection
    connection = sqlite3.connect("owmail.db")
    db = connection.cursor()

    # Forget user ID
    session.clear()

    # If information is submitted through a form, handle the post request
    if request.method == "POST":

        # Ensure all fields are filled
        if not request.form.get("address") or not request.form.get("password"):
            return error("Missing Fields", 400)
        
        # If there is a person in the db with the same address and password
        rows = db.execute("SELECT * FROM users WHERE address = :address", {"address": request.form.get("address")})
        row = rows.fetchall()
        if not row or not check_password_hash(row[0][2], request.form.get("password")):
            return error("Invalid username and/or password", 400)

        # Save the session id and redirect to the inbox
        session["user_id"] = row[0][0]
        session["user_address"] = request.form.get("address")
        return redirect("/inbox")
    else:
        return render_template("login.html")

# Log out
@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    session.clear()
    return redirect("/")


# Run app
if __name__ == "__main__":
    app.run()