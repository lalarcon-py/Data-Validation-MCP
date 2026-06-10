import os
from dotenv import load_dotenv

load_dotenv()

_PREFIXES = {
    "source": "SOURCE_DB",
    "target": "TARGET_DB",
}


def get_dialect(name: str) -> str:
    """Returns 'oracle', 'postgres', or 'sqlserver' based on the driver setting."""
    prefix = _PREFIXES[name.lower()]
    driver = os.getenv(f"{prefix}_DRIVER", "").lower()
    if "oracle" in driver:
        return "oracle"
    if "postgres" in driver or "postgresql" in driver:
        return "postgres"
    return "sqlserver"


def get_connection(name: str):
    """Returns an open database connection for 'source' or 'target'."""
    name = name.lower()
    if name not in _PREFIXES:
        raise ValueError(f"Unknown connection '{name}'. Use 'source' or 'target'.")

    prefix = _PREFIXES[name]
    driver = _require(prefix, "DRIVER")

    if "oracle" in driver.lower():
        from connections.oracle import get_oracle_connection
        return get_oracle_connection(
            user=_require(prefix, "USER"),
            password=_require(prefix, "PASSWORD"),
            dsn=_require(prefix, "DSN"),
        )

    if "postgres" in driver.lower() or "postgresql" in driver.lower():
        from connections.postgres import get_postgres_connection
        return get_postgres_connection(
            host=_require(prefix, "HOST"),
            port=os.getenv(f"{prefix}_PORT", "5432"),
            database=_require(prefix, "NAME"),
            user=_require(prefix, "USER"),
            password=_require(prefix, "PASSWORD"),
        )

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
        raise ValueError(f"Missing env var '{full_key}'. Check your .env file.")
    return value
