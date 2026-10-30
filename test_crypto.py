import os
from cryptography.exceptions import InvalidTag
from crypto import (generate_master_key, load_master_key, generate_file_key,
                    wrap_key, unwrap_key, encrypt_chunk, decrypt_chunk)

results = []

def check(label, condition):
    print(f"{label:<55} {'PASS' if condition else 'FAIL'}")
    results.append(condition)

def raises_invalid(fn):
    try:
        fn()
        return False
    except InvalidTag:
        return True

master = load_master_key(generate_master_key())
file_key = generate_file_key()
file_id = "file-abc"
data = os.urandom(1024 * 1024)

# 1. round trip
blob = encrypt_chunk(file_key, file_id, 0, data)
check("Encrypt then decrypt returns original data", decrypt_chunk(file_key, file_id, 0, blob) == data)

# 2. ciphertext is not plaintext
check("Encrypted data differs from original", data not in blob)

# 3. fresh nonce each time
blob2 = encrypt_chunk(file_key, file_id, 0, data)
check("Same chunk encrypted twice gives different output", blob != blob2)

# 4. tampering is detected
tampered = bytearray(blob)
tampered[100] ^= 1
check("Flipping one bit is detected", raises_invalid(lambda: decrypt_chunk(file_key, file_id, 0, bytes(tampered))))

# 5. chunk swapped to a different position
check("Chunk moved to another position is rejected", raises_invalid(lambda: decrypt_chunk(file_key, file_id, 1, blob)))

# 6. chunk copied into a different file
check("Chunk used in a different file is rejected", raises_invalid(lambda: decrypt_chunk(file_key, "file-xyz", 0, blob)))

# 7. wrong file key
check("Wrong file key is rejected", raises_invalid(lambda: decrypt_chunk(generate_file_key(), file_id, 0, blob)))

# 8. key wrapping round trip
wrapped = wrap_key(file_key, master, file_id)
check("Wrapped file key unwraps correctly", unwrap_key(wrapped, master, file_id) == file_key)

# 9. wrong master key
other_master = load_master_key(generate_master_key())
check("Wrong master key cannot unwrap file key", raises_invalid(lambda: unwrap_key(wrapped, other_master, file_id)))

# 10. empty chunk still works
empty_blob = encrypt_chunk(file_key, file_id, 0, b"")
check("Empty chunk round trip", decrypt_chunk(file_key, file_id, 0, empty_blob) == b"")

print()
print("ALL TESTS PASSED" if all(results) else "SOME TESTS FAILED")