"""
crypto.py - AES-256-GCM encryption for chunks, with envelope encryption.

Layout of an encrypted blob:  nonce (12 bytes) + ciphertext + GCM tag
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

NONCE_SIZE = 12


# ---------- master key ----------

def generate_master_key() -> str:
    """Create a new master key as a base64 string (store it in .env)."""
    return base64.urlsafe_b64encode(AESGCM.generate_key(bit_length=256)).decode()


def load_master_key(b64_key: str) -> bytes:
    """Turn the base64 string from .env back into 32 raw bytes."""
    key = base64.urlsafe_b64decode(b64_key.encode())
    if len(key) != 32:
        raise ValueError("MASTER_KEY must decode to exactly 32 bytes")
    return key


# ---------- per-file key (envelope encryption) ----------

def generate_file_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)


def wrap_key(file_key: bytes, master_key: bytes, file_id: str) -> bytes:
    """Encrypt the file key with the master key. Safe to store in the database."""
    nonce = os.urandom(NONCE_SIZE)
    ct = AESGCM(master_key).encrypt(nonce, file_key, file_id.encode())
    return nonce + ct


def unwrap_key(wrapped: bytes, master_key: bytes, file_id: str) -> bytes:
    nonce, ct = wrapped[:NONCE_SIZE], wrapped[NONCE_SIZE:]
    return AESGCM(master_key).decrypt(nonce, ct, file_id.encode())


# ---------- chunk encryption ----------

def _aad(file_id: str, index: int) -> bytes:
    # binds the chunk to its file and position
    return f"{file_id}:{index}".encode()


def encrypt_chunk(file_key: bytes, file_id: str, index: int, data: bytes) -> bytes:
    nonce = os.urandom(NONCE_SIZE)
    ct = AESGCM(file_key).encrypt(nonce, data, _aad(file_id, index))
    return nonce + ct


def decrypt_chunk(file_key: bytes, file_id: str, index: int, blob: bytes) -> bytes:
    nonce, ct = blob[:NONCE_SIZE], blob[NONCE_SIZE:]
    return AESGCM(file_key).decrypt(nonce, ct, _aad(file_id, index))