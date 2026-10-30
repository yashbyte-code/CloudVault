"""
app.py - the Flask application: serves the pages and the JSON API.
Run with:  python app.py
"""
import os
import re
from datetime import timedelta
from urllib.parse import quote

from flask import (Flask, request, session, jsonify, redirect,
                   send_from_directory, Response)

import config
import db
import auth
import file_service
from crypto import load_master_key

# ---------- startup checks ----------
if not config.SECRET_KEY:
    raise SystemExit("SECRET_KEY is missing in your .env file.")
if not config.MASTER_KEY:
    raise SystemExit("MASTER_KEY is missing in your .env file. Run generate_key.py first.")
if config.STORAGE_MODE == "s3" and not config.S3_BUCKET:
    raise SystemExit("STORAGE_MODE is s3 but S3_BUCKET is missing in your .env file.")

MASTER_KEY = load_master_key(config.MASTER_KEY)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=config.SECRET_KEY,
    MAX_CONTENT_LENGTH=100 * 1024 * 1024,        # 100 MB upload limit
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

db.init_db()

TEMPLATES_DIR = os.path.join(app.root_path, "templates")
PORTFOLIO_DIR = os.path.join(app.root_path, "portfolio")


@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


# ---------- pages ----------

@app.get("/")
@app.get("/home.html")
def home_page():
    return send_from_directory(TEMPLATES_DIR, "home.html")


@app.get("/login.html")
def login_page():
    return send_from_directory(TEMPLATES_DIR, "login.html")


@app.get("/dashboard.html")
def dashboard_page():
    if "user_id" not in session:
        return redirect("/login.html")
    return send_from_directory(TEMPLATES_DIR, "dashboard.html")


@app.get("/portfolio/")
@app.get("/portfolio/index.html")
def portfolio_page():
    return send_from_directory(PORTFOLIO_DIR, "index.html")


# ---------- auth API ----------

def _login(user_id):
    session.clear()                 # start a fresh session on every login
    session["user_id"] = user_id
    session.permanent = True


@app.post("/api/register")
def api_register():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", ""))
    password = str(data.get("password", ""))
    try:
        user_id = auth.register_user(username, password)
    except ValueError as e:
        message = str(e)
        status = 409 if "already taken" in message else 400
        return jsonify(error=message), status
    _login(user_id)
    return jsonify(message="Account created.", username=username.strip().lower()), 201


@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", ""))
    password = str(data.get("password", ""))
    user_id = auth.verify_login(username, password)
    if user_id is None:
        return jsonify(error="Invalid username or password."), 401
    _login(user_id)
    return jsonify(message="Logged in.", username=username.strip().lower())


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(message="Logged out.")


@app.get("/api/me")
@auth.login_required
def api_me():
    user = db.get_user_by_id(session["user_id"])
    return jsonify(username=user["username"])


# ---------- file API ----------

def clean_filename(name):
    name = os.path.basename(name.replace("\\", "/")).strip()
    name = re.sub(r"[\x00-\x1f]", "", name)
    return name[:200] or "file"


@app.get("/api/files")
@auth.login_required
def api_list():
    files = db.list_files(session["user_id"])
    return jsonify(files=[
        {
            "id": f["id"],
            "name": f["original_name"],
            "size": f["size"],
            "chunks": f["chunk_count"],
            "created_at": f["created_at"],
        }
        for f in files
    ])


@app.post("/api/files")
@auth.login_required
def api_upload():
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify(error="No file was sent."), 400
    name = clean_filename(uploaded.filename)
    try:
        file_id = file_service.upload_file(uploaded.stream, name, session["user_id"], MASTER_KEY)
    except Exception:
        app.logger.exception("Upload failed")
        return jsonify(error="Upload failed. Please try again."), 500
    return jsonify(message="Upload successful.", id=file_id, name=name), 201


@app.get("/api/files/<file_id>/download")
@auth.login_required
def api_download(file_id):
    record = db.get_file(file_id, session["user_id"])
    if record is None:
        return jsonify(error="File not found."), 404
    headers = {
        "Content-Disposition": "attachment; filename*=UTF-8''" + quote(record["original_name"], safe=""),
        "Content-Length": str(record["size"]),
    }
    return Response(file_service.download_chunks(record, MASTER_KEY),
                    mimetype="application/octet-stream", headers=headers)


@app.delete("/api/files/<file_id>")
@auth.login_required
def api_delete(file_id):
    if file_service.remove_file(file_id, session["user_id"]):
        return jsonify(message="File deleted.")
    return jsonify(error="File not found."), 404


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="File is too large (limit is 100 MB)."), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)