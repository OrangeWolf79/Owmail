from functools import wraps
from flask import redirect, render_template, session

# Render an error if something went wrong
def error(message, err_code):
    return render_template("error.html", message=message, err_code=err_code)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function