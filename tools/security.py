import re

# Max rows execute_query will return. Prevents memory issues on large tables.
MAX_QUERY_ROWS = 500

# Valid identifier pattern: letters/numbers/underscores, optional schema prefix (schema.table)
# Allows $ and # which are valid in Oracle identifiers.
_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_$#]*(\.[a-zA-Z_][a-zA-Z0-9_$#]*)?$")


def validate_identifier(name: str, label: str = "identifier") -> str | None:
    """Validates a table or column name. Returns an error string if invalid, None if clean.

    This blocks SQL injection attempts via table/column name parameters.
    Valid examples: 'orders', 'demo_source.orders', 'order_items', 'customer_id'
    Invalid examples: 'orders; DROP TABLE orders', 'orders--', '../etc'
    """
    if not name or not isinstance(name, str):
        return f"Invalid {label}: must be a non-empty string."
    if not _IDENTIFIER_RE.match(name.strip()):
        return (
            f"Invalid {label} '{name}'. Only letters, numbers, underscores, and an optional "
            f"schema prefix (schema.table) are allowed."
        )
    return None


def validate_identifiers(**kwargs) -> str | None:
    """Validates multiple identifiers at once. Pass as keyword args: table='orders', column='id'.
    Returns the first error found, or None if all are valid.
    """
    for label, value in kwargs.items():
        err = validate_identifier(value, label)
        if err:
            return err
    return None
