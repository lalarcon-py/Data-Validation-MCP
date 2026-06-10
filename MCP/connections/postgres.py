import psycopg2


def get_postgres_connection(
    host: str,
    port: str,
    database: str,
    user: str,
    password: str,
) -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=host,
        port=int(port),
        dbname=database,
        user=user,
        password=password,
        connect_timeout=10,
    )
