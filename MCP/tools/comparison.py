from config import get_connection
from tools.inventory import get_row_count


def compare_row_counts(table: str) -> dict:
    try:
        source = get_row_count(table, "source")
        target = get_row_count(table, "target")

        if "error" in source:
            return {"error": f"source: {source['error']}", "table": table}
        if "error" in target:
            return {"error": f"target: {target['error']}", "table": table}

        src, tgt = source["row_count"], target["row_count"]
        return {
            "table": table,
            "source_count": src,
            "target_count": tgt,
            "delta": src - tgt,
            "in_sync": src == tgt,
        }
    except Exception as e:
        return {"error": str(e), "table": table}


def diff_record(table: str, pk_column: str, pk_value: str) -> dict:
    try:
        src_row = _fetch_row(table, pk_column, pk_value, "source")
        tgt_row = _fetch_row(table, pk_column, pk_value, "target")

        result = {
            "table": table,
            "pk_column": pk_column,
            "pk_value": pk_value,
            "source_found": src_row is not None,
            "target_found": tgt_row is not None,
            "columns_differ": [],
            "diff": {},
            "identical": False,
        }

        if src_row is None or tgt_row is None:
            return result

        for col in src_row:
            if src_row.get(col) != tgt_row.get(col):
                result["columns_differ"].append(col)
                result["diff"][col] = {"source": src_row[col], "target": tgt_row.get(col)}

        result["identical"] = len(result["columns_differ"]) == 0
        return result
    except Exception as e:
        return {"error": str(e), "table": table, "pk_column": pk_column, "pk_value": pk_value}


def _fetch_row(table: str, pk_column: str, pk_value: str, connection_name: str) -> dict | None:
    conn = get_connection(connection_name)
    cursor = conn.cursor()
    # FETCH FIRST 1 ROW ONLY works on Oracle 12c+ and modern SQL Server
    cursor.execute(
        f"SELECT * FROM {table} WHERE {pk_column} = :1 FETCH FIRST 1 ROW ONLY",
        [pk_value]
    )
    row = cursor.fetchone()
    columns = [d[0] for d in cursor.description]
    conn.close()
    if row is None:
        return None
    return dict(zip(columns, row))
