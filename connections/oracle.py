import oracledb


def get_oracle_connection(user: str, password: str, dsn: str) -> oracledb.Connection:
    """Open an oracledb thin-mode connection. No Instant Client required."""
    return oracledb.connect(user=user, password=password, dsn=dsn)
