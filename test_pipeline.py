import os, io, hashlib, shutil

# force test settings BEFORE importing our modules
os.environ["STORAGE_MODE"] = "local"
os.environ["DB_PATH"] = "test_cloudvault.db"
os.environ["LOCAL_STORAGE_DIR"] = "test_local_storage"

import db, storage, file_service
from crypto import generate_master_key, load_master_key
from cryptography.exceptions import InvalidTag


def cleanup():
    if os.path.exists("test_cloudvault.db"):
        os.remove("test_cloudvault.db")
    shutil.rmtree("test_local_storage", ignore_errors=True)

results = []
def check(label, condition):
    print(f"{label:<58} {'PASS' if condition else 'FAIL'}")
    results.append(condition)

cleanup()
db.init_db()
master = load_master_key(generate_master_key())

alice = db.create_user("alice", "placeholder-hash")
bob = db.create_user("bob", "placeholder-hash")

original = os.urandom(int(3.5 * 1024 * 1024))     # 3.5 MB -> 4 chunks
file_id = file_service.upload_file(io.BytesIO(original), "report.bin", alice, master)

# upload recorded correctly
files = db.list_files(alice)
check("File appears in Alice's list", len(files) == 1 and files[0]["original_name"] == "report.bin")
check("Metadata: size and chunk count are correct", files[0]["size"] == len(original) and files[0]["chunk_count"] == 4)
chunk_dir = os.path.join("test_local_storage", "files", file_id)
check("4 encrypted chunk files exist in storage", len(os.listdir(chunk_dir)) == 4)

# stored data is really encrypted
with open(os.path.join(chunk_dir, "chunk_0000.enc"), "rb") as f:
    raw = f.read()
check("Stored chunk does not contain the plaintext", original[:64] not in raw)

# download gives back the exact file
record = db.get_file(file_id, alice)
rebuilt = b"".join(file_service.download_chunks(record, master))
check("Downloaded file matches original (SHA-256)",
      hashlib.sha256(rebuilt).hexdigest() == hashlib.sha256(original).hexdigest())

# user isolation
check("Bob cannot see Alice's file", db.get_file(file_id, bob) is None and db.list_files(bob) == [])
check("Bob cannot delete Alice's file", file_service.remove_file(file_id, bob) is False)

# tampering detected
tampered_path = os.path.join(chunk_dir, "chunk_0002.enc")
with open(tampered_path, "rb") as f:
    data = bytearray(f.read())
data[50] ^= 1
with open(tampered_path, "wb") as f:
    f.write(data)
try:
    b"".join(file_service.download_chunks(record, master))
    detected = False
except InvalidTag:
    detected = True
check("Tampered chunk in storage is detected on download", detected)

# delete
check("Alice can delete her file", file_service.remove_file(file_id, alice) is True)
check("Chunks and database row are gone",
      not os.path.exists(chunk_dir) and db.list_files(alice) == [])

# empty file
empty_id = file_service.upload_file(io.BytesIO(b""), "empty.txt", alice, master)
empty_rec = db.get_file(empty_id, alice)
check("Empty file uploads and downloads as empty",
      empty_rec["chunk_count"] == 0 and b"".join(file_service.download_chunks(empty_rec, master)) == b"")

cleanup()
print()
print("ALL TESTS PASSED" if all(results) else "SOME TESTS FAILED")