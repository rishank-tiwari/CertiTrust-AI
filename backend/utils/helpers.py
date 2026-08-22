import uuid
import os
from datetime import datetime, timezone

def generate_id() -> str:
    """Return a new UUID4 string."""
    return str(uuid.uuid4())

def get_current_timestamp() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)

def validate_file_type(filename: str) -> bool:
    """Check if file extension is in allowed list."""
    allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.webp']
    _, ext = os.path.splitext(filename)
    return ext.lower() in allowed_extensions

def format_file_size(size_bytes: int) -> str:
    """Human readable file size."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    p = size_bytes
    while p >= 1024 and i < len(size_name) - 1:
        p /= 1024.0
        i += 1
    return f"{p:.2f} {size_name[i]}"
