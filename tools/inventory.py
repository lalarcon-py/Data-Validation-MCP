from config import get_connection, get_dialect
from tools.security import validate_identifiers


def list_tables(connection_name: str) -> dict:
    try:
        conn = get_connection(connection_name)
        dialect = get_dialect(connection_name)
        cursor = conn.cursor()

        if dialect == "oracle":
            cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
        elif dialect == "postgres":
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = current_schema() AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
        else:
            cursor.execute("""
                SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME
            """)

        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"connection": connection_name, "tables": tables, "count": len(tables)}
    except Exception as e:
        return {"error": str(e), "connection": connection_name}


def get_row_count(table: str, connection_name: str) -> dict:
    err = validate_identifiers(table=table)
    if err:
        return {"error": err, "connection": connection_name, "table": table}
    try:
        conn = get_connection(connection_name)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        conn.close()
        return {"connection": connection_name, "table": table, "row_count": count}
    except Exception as e:
        return {"error": str(e), "connection": connection_name, "table": table}
