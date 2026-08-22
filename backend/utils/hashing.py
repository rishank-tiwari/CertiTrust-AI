import hashlib

def generate_file_hash(file_path: str) -> str:
    """Read file in chunks and return SHA-256 hex digest."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_string_hash(data: str) -> str:
    """Return SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
