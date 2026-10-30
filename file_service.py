
"""
file_service.py - upload / download / delete logic that joins
chunker + crypto + storage + db together.
"""
import uuid
import db
import storage
from chunker import iter_chunks, CHUNK_SIZE
from crypto import generate_file_key, wrap_key, unwrap_key, encrypt_chunk, decrypt_chunk


def chunk_key(file_id, index):
    return f"files/{file_id}/chunk_{index:04d}.enc"


def upload_file(stream, filename, user_id, master_key):
    file_id = uuid.uuid4().hex
    file_key = generate_file_key()
    total_size = 0
    count = 0
    try:
        for index, data in iter_chunks(stream):
            blob = encrypt_chunk(file_key, file_id, index, data)
            storage.put_chunk(chunk_key(file_id, index), blob)
            total_size += len(data)
            count += 1
        wrapped = wrap_key(file_key, master_key, file_id)
        db.add_file(file_id, user_id, filename, total_size, count, CHUNK_SIZE, wrapped)
    except Exception:
        storage.delete_prefix(f"files/{file_id}/")   # clean up half-uploaded chunks
        raise
    return file_id


def download_chunks(record, master_key):
    """Yield decrypted chunks of a file, in order."""
    file_id = record["id"]
    file_key = unwrap_key(record["wrapped_key"], master_key, file_id)
    for index in range(record["chunk_count"]):
        blob = storage.get_chunk(chunk_key(file_id, index))
        yield decrypt_chunk(file_key, file_id, index, blob)


def remove_file(file_id, user_id):
    record = db.get_file(file_id, user_id)
    if record is None:
        return False
    storage.delete_prefix(f"files/{file_id}/")
    db.delete_file(file_id, user_id)
    return True