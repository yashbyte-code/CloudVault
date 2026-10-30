"""
auth.py - password hashing, login checks, and the login_required guard.
"""
import re
from functools import wraps
from flask import session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import db

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
MIN_PASSWORD = 6
MAX_PASSWORD = 128

# Used when the username doesn't exist, so a wrong username and a wrong
# password take about the same time (stops username guessing by timing).
_DUMMY_HASH = generate_password_hash("dummy-password")


def register_user(username, password):
    username = username.strip().lower()
    if not USERNAME_RE.match(username):
        raise ValueError("Username must be 3-30 characters: letters, numbers or underscore.")
    if len(password) < MIN_PASSWORD:
        raise ValueError(f"Password must be at least {MIN_PASSWORD} characters.")
    if len(password) > MAX_PASSWORD:
        raise ValueError("Password is too long.")
    return db.create_user(username, generate_password_hash(password))


def verify_login(username, password):
    """Returns the user id if the login is correct, otherwise None."""
    user = db.get_user_by_name(username.strip().lower())
    if user is None:
        check_password_hash(_DUMMY_HASH, password)
        return None
    if check_password_hash(user["password_hash"], password):
        return user["id"]
    return None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(error="Please log in first."), 401
        return view(*args, **kwargs)
    return wrapper