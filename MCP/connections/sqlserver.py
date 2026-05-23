import pyodbc


def get_sqlserver_connection(
    driver: str,
    server: str,
    database: str,
    user: str | None = None,
    password: str | None = None,
) -> pyodbc.Connection:
    """Open a pyodbc connection. Falls back to Windows auth if user/password are omitted."""
    if user and password:
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={user};PWD={password};"
        )
    else:
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            "Trusted_Connection=yes;"
        )

    return pyodbc.connect(conn_str, timeout=10)
