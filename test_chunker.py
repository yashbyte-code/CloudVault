import os
import hashlib
from chunker import iter_chunks, join_chunks, count_chunks, CHUNK_SIZE


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(65536):
            h.update(block)
    return h.hexdigest()


def run_test(size_bytes, label):
    original = "test_original.bin"
    rebuilt = "test_rebuilt.bin"

    # make a file of random bytes
    with open(original, "wb") as f:
        f.write(os.urandom(size_bytes))

    # split into chunks (kept in a list only for this small test)
    with open(original, "rb") as f:
        chunks = [data for _, data in iter_chunks(f)]

    # rebuild
    with open(rebuilt, "wb") as f:
        join_chunks(chunks, f)

    same = sha256(original) == sha256(rebuilt)
    expected = count_chunks(size_bytes)
    ok = same and len(chunks) == expected
    print(f"{label:<28} chunks={len(chunks)} expected={expected} match={same} -> {'PASS' if ok else 'FAIL'}")

    os.remove(original)
    os.remove(rebuilt)
    return ok


results = [
    run_test(0, "empty file"),
    run_test(500, "tiny file (500 bytes)"),
    run_test(CHUNK_SIZE, "exactly 1 chunk"),
    run_test(CHUNK_SIZE + 1, "1 chunk + 1 byte"),
    run_test(int(3.5 * CHUNK_SIZE), "3.5 MB file"),
]

print()
print("ALL TESTS PASSED" if all(results) else "SOME TESTS FAILED")