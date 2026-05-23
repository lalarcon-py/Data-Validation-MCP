"""
Loads named database connections from .env and returns the appropriate
connection factory. Supported names: "source", "target".
"""

import os
from dotenv import load_dotenv

load_dotenv()

_PREFIXES = {
    "source": "SOURCE_DB",
    "target": "TARGET_DB",
}


def get_connection(name: str):
    """Return an open database connection for "source" or "target"."""
    name = name.lower()
    if name not in _PREFIXES:
        raise ValueError(f"Unknown connection '{name}'. Must be one of: {list(_PREFIXES)}")

    prefix = _PREFIXES[name]
    driver = _require(prefix, "DRIVER")

    if "oracle" in driver.lower():
        from connections.oracle import get_oracle_connection
        return get_oracle_connection(
            user=_require(prefix, "USER"),
            password=_require(prefix, "PASSWORD"),
            dsn=_require(prefix, "DSN"),
        )
    else:
        from connections.sqlserver import get_sqlserver_connection
        return get_sqlserver_connection(
            driver=driver,
            server=_require(prefix, "SERVER"),
            database=_require(prefix, "NAME"),
            user=os.getenv(f"{prefix}_USER"),
            password=os.getenv(f"{prefix}_PASSWORD"),
        )


def _require(prefix: str, key: str) -> str:
    full_key = f"{prefix}_{key}"
    value = os.getenv(full_key)
    if not value:
        raise ValueError(f"Required env var '{full_key}' is not set. Check your .env file.")
    return value
