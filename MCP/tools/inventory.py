from config import get_connection


def list_tables(connection_name: str) -> dict:
    try:
        conn = get_connection(connection_name)
        cursor = conn.cursor()
        # USER_TABLES works for both Oracle and SQL Server (via INFORMATION_SCHEMA fallback)
        try:
            cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
        except Exception:
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
    try:
        conn = get_connection(connection_name)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        conn.close()
        return {"connection": connection_name, "table": table, "row_count": count}
    except Exception as e:
        return {"error": str(e), "connection": connection_name, "table": table}
