"""
db.py - SQLite storage for users and file metadata.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
import config


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS files (
                id            TEXT PRIMARY KEY,
                user_id       INTEGER NOT NULL,
                original_name TEXT NOT NULL,
                size          INTEGER NOT NULL,
                chunk_count   INTEGER NOT NULL,
                chunk_size    INTEGER NOT NULL,
                wrapped_key   BLOB NOT NULL,
                created_at    TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)


def _now():
    return datetime.now(timezone.utc).isoformat()


# ---------- users ----------

def create_user(username, password_hash):
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, password_hash, _now()))
            return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Username already taken")


def get_user_by_name(username):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_user_by_id(user_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


# ---------- files ----------

def add_file(file_id, user_id, name, size, chunk_count, chunk_size, wrapped_key):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO files (id, user_id, original_name, size, chunk_count, chunk_size, wrapped_key, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (file_id, user_id, name, size, chunk_count, chunk_size, wrapped_key, _now()))


def list_files(user_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM files WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
        return [dict(r) for r in rows]


def get_file(file_id, user_id):
    """Returns the file only if it belongs to this user, otherwise None."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM files WHERE id = ? AND user_id = ?", (file_id, user_id)).fetchone()
        return dict(row) if row else None


def delete_file(file_id, user_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM files WHERE id = ? AND user_id = ?", (file_id, user_id))