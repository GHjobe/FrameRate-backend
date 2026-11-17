import re
from werkzeug.security import generate_password_hash, check_password_hash

MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def check_password_policy(password: str) -> list[str]:
    """Returns a list of problems. Empty list = password is OK."""
    problems: list[str] = []
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if not re.search(r"[A-Za-z]", password):
        problems.append("Password must contain at least one letter.")
    if not re.search(r"\d", password):
        problems.append("Password must contain at least one number.")
    return problems