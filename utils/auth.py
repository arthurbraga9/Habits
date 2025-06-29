import hashlib

def hash_password(password: str) -> str:
    """Return a SHA-256 hash for the given password."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Check a plaintext password against an existing hash."""
    return hash_password(password) == hashed
