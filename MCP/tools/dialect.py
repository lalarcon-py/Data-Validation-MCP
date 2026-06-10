# Helpers that handle the SQL syntax differences between Oracle, PostgreSQL, and SQL Server.
# Every tool imports from here instead of hardcoding dialect-specific SQL.


def placeholder(dialect: str) -> str:
    """Parameter placeholder for prepared statements."""
    if dialect == "postgres":
        return "%s"
    if dialect == "oracle":
        return ":1"
    return "?"


def limit_one(dialect: str, query: str) -> str:
    """Wraps a SELECT to return only the first row."""
    if dialect == "sqlserver":
        return query.replace("SELECT ", "SELECT TOP 1 ", 1)
    return f"{query} FETCH FIRST 1 ROW ONLY"


def quote(name: str, dialect: str) -> str:
    """Quotes an identifier (table or column name)."""
    if dialect == "sqlserver":
        return f"[{name}]"
    if dialect == "postgres":
        return f'"{name}"'
    return name  # Oracle handles unquoted names fine


def normalize(name: str, dialect: str) -> str:
    """Normalizes a name for use in catalog queries.
    Oracle stores everything uppercase, Postgres stores lowercase."""
    if dialect == "oracle":
        return name.upper()
    return name.lower()


def query_to_dicts(cursor, query: str, params=None) -> list[dict]:
    """Runs a query and returns results as a list of dicts with lowercase keys.
    Makes it easy to compare results across different databases."""
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    cols = [d[0].lower() for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]
