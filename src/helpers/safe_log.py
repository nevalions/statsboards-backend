"""Helper functions for safe logging without exposing sensitive data."""

from typing import Any

SENSITIVE_FIELDS = {
    "password",
    "hashed_password",
    "token",
    "api_key",
    "secret",
    "session_token",
    "refresh_token",
    "access_token",
    "auth_token",
    "bearer_token",
    "private_key",
    "api_secret",
    "plain_password",
    "secret_key",
}


def safe_log_obj(obj: Any, max_fields: int = 5) -> str:
    """
    Convert object to safe loggable string, redacting sensitive fields.

    Args:
        obj: Object to log (dict, object with __dict__, etc.)
        max_fields: Maximum number of fields to include (default: 5)

    Returns:
        String representation with sensitive fields redacted
    """
    if obj is None:
        return "None"

    if hasattr(obj, "__dict__"):
        data_dict = obj.__dict__
    elif isinstance(obj, dict):
        data_dict = obj
    else:
        return str(obj)

    safe_dict = {}
    field_count = 0

    for key, value in data_dict.items():
        if key.startswith("_"):
            continue

        if key.lower() in SENSITIVE_FIELDS:
            safe_dict[key] = "***REDACTED***"
            field_count += 1
        else:
            if field_count < max_fields:
                if isinstance(value, (dict, list)):
                    safe_dict[key] = f"<{type(value).__name__} with {len(value)} items>"
                elif hasattr(value, "__dict__"):
                    safe_dict[key] = f"<{type(value).__name__}>"
                else:
                    safe_dict[key] = value
                field_count += 1
            else:
                safe_dict[key] = "... (truncated)"

    return str(safe_dict)
