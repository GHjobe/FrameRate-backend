from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


def in_list(column, values):
    """SQL text for a CHECK constraint such as: role IN ('user', 'moderator', 'admin')."""
    quoted = ", ".join(f"'{v}'" for v in values)
    return f"{column} IN ({quoted})"