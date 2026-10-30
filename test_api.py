import os, io, shutil, hashlib

# test settings, set BEFORE importing the app
os.environ["STORAGE_MODE"] = "local"
os.environ["DB_PATH"] = "test_api.db"
os.environ["LOCAL_STORAGE_DIR"] = "test_api_storage"
os.environ["SECRET_KEY"] = "test-secret-key"
from crypto import generate_master_key
os.environ["MASTER_KEY"] = generate_master_key()


def cleanup():
    if os.path.exists("test_api.db"):
        os.remove("test_api.db")
    shutil.rmtree("test_api_storage", ignore_errors=True)


cleanup()
from app import app as flask_app

results = []
def check(label, condition):
    print(f"{label:<58} {'PASS' if condition else 'FAIL'}")
    results.append(bool(condition))

alice = flask_app.test_client()
bob = flask_app.test_client()
original = os.urandom(int(2.5 * 1024 * 1024))

# --- access control ---
check("List files without login is rejected (401)", alice.get("/api/files").status_code == 401)
r = alice.get("/dashboard.html")
check("Dashboard page redirects to login when logged out",
      r.status_code == 302 and r.headers["Location"].endswith("/login.html"))

# --- register / login ---
check("Register with short password is rejected (400)",
      alice.post("/api/register", json={"username": "alice", "password": "123"}).status_code == 400)
check("Register works (201)",
      alice.post("/api/register", json={"username": "alice", "password": "secret123"}).status_code == 201)
check("Duplicate username is rejected (409)",
      bob.post("/api/register", json={"username": "ALICE", "password": "secret123"}).status_code == 409)
alice.post("/api/logout")
check("Wrong password is rejected (401)",
      alice.post("/api/login", json={"username": "alice", "password": "wrongpass"}).status_code == 401)
check("Correct login works (200)",
      alice.post("/api/login", json={"username": "alice", "password": "secret123"}).status_code == 200)
check("Dashboard page opens when logged in", alice.get("/dashboard.html").status_code == 200)

# --- upload / list / download ---
r = alice.post("/api/files", data={"file": (io.BytesIO(original), "report.bin")},
               content_type="multipart/form-data")
check("Upload works (201)", r.status_code == 201)
file_id = r.get_json()["id"]

files = alice.get("/api/files").get_json()["files"]
check("File shows in list with 3 chunks",
      len(files) == 1 and files[0]["name"] == "report.bin" and files[0]["chunks"] == 3)

r = alice.get(f"/api/files/{file_id}/download")
check("Download matches original (SHA-256)",
      r.status_code == 200 and hashlib.sha256(r.data).hexdigest() == hashlib.sha256(original).hexdigest())
check("Download has the right file name", "report.bin" in r.headers["Content-Disposition"])

# --- another user cannot touch Alice's file ---
bob.post("/api/register", json={"username": "bob", "password": "secret456"})
check("Bob's file list is empty", bob.get("/api/files").get_json()["files"] == [])
check("Bob cannot download Alice's file (404)", bob.get(f"/api/files/{file_id}/download").status_code == 404)
check("Bob cannot delete Alice's file (404)", bob.delete(f"/api/files/{file_id}").status_code == 404)

# --- bad uploads ---
check("Upload with no file is rejected (400)",
      alice.post("/api/files", data={}, content_type="multipart/form-data").status_code == 400)

# --- delete / logout ---
check("Alice can delete her file (200)", alice.delete(f"/api/files/{file_id}").status_code == 200)
check("List is empty after delete", alice.get("/api/files").get_json()["files"] == [])
alice.post("/api/logout")
check("After logout, API is blocked again (401)", alice.get("/api/files").status_code == 401)

# --- pages ---
check("Home page loads", alice.get("/").status_code == 200)
check("Portfolio page loads", alice.get("/portfolio/index.html").status_code == 200)

cleanup()
print()
print("ALL TESTS PASSED" if all(results) else "SOME TESTS FAILED")