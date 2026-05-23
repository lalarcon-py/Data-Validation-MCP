from config import get_connection


def validate_not_null(table: str, columns: list[str], connection_name: str) -> dict:
    try:
        conn = get_connection(connection_name)
        cursor = conn.cursor()
        nulls_found = {}
        for col in columns:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL")
            count = cursor.fetchone()[0]
            if count > 0:
                nulls_found[col] = count
        conn.close()
        return {
            "connection": connection_name,
            "table": table,
            "columns_checked": columns,
            "nulls_found": nulls_found,
            "any_nulls": len(nulls_found) > 0,
        }
    except Exception as e:
        return {"error": str(e), "connection": connection_name, "table": table}


def validate_pk_uniqueness(table: str, pk_column: str, connection_name: str) -> dict:
    try:
        conn = get_connection(connection_name)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT {pk_column}, COUNT(*) AS cnt
            FROM {table}
            GROUP BY {pk_column}
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
        """)
        duplicates = [{"pk_value": str(row[0]), "count": row[1]} for row in cursor.fetchall()]
        conn.close()
        return {
            "connection": connection_name,
            "table": table,
            "pk_column": pk_column,
            "duplicates": duplicates,
            "duplicate_count": len(duplicates),
            "is_unique": len(duplicates) == 0,
        }
    except Exception as e:
        return {"error": str(e), "connection": connection_name, "table": table}
