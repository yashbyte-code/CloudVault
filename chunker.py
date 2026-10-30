"""
chunker.py - split a file stream into fixed-size chunks.

Chunks are produced one at a time (a generator), so even a very large
file never has to sit fully in memory.
"""

CHUNK_SIZE = 1024 * 1024  # 1 MB


def iter_chunks(stream, chunk_size=CHUNK_SIZE):
    """Yield (index, data) for each chunk read from a binary stream."""
    index = 0
    while True:
        data = stream.read(chunk_size)
        if not data:          # end of file
            break
        yield index, data
        index += 1


def count_chunks(file_size, chunk_size=CHUNK_SIZE):
    """How many chunks a file of this size will produce."""
    if file_size == 0:
        return 0
    return (file_size + chunk_size - 1) // chunk_size


def join_chunks(chunks, out_stream):
    """Write chunks (in order) to an output stream. Returns total bytes."""
    total = 0
    for data in chunks:
        out_stream.write(data)
        total += len(data)
    return total