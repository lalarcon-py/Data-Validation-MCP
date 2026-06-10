from config import get_connection, get_dialect
from tools.inventory import get_row_count
from tools.dialect import placeholder, limit_one, quote
from tools.security import validate_identifiers


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


def compare_all_row_counts() -> dict:
    """Compares row counts for every table across both connections.

    Normalizes table names before comparing so Oracle (uppercase) and
    Postgres/SQL Server (lowercase) don't cause false mismatches.
    Also reports tables that exist on one side but not the other.
    """
    try:
        from tools.inventory import list_tables

        src_result = list_tables("source")
        tgt_result = list_tables("target")

        if "error" in src_result:
            return src_result
        if "error" in tgt_result:
            return tgt_result

        # Normalize to uppercase for comparison, keep original names for querying
        src_map = {t.upper(): t for t in src_result["tables"]}
        tgt_map = {t.upper(): t for t in tgt_result["tables"]}

        src_keys = set(src_map)
        tgt_keys = set(tgt_map)

        only_in_source = sorted(src_keys - tgt_keys)
        only_in_target = sorted(tgt_keys - src_keys)
        common = sorted(src_keys & tgt_keys)

        results = []
        for key in common:
            # Use the original name each side returned to avoid case issues
            src_count = get_row_count(src_map[key], "source")
            tgt_count = get_row_count(tgt_map[key], "target")

            if "error" in src_count or "error" in tgt_count:
                results.append({
                    "table": key,
                    "error": src_count.get("error") or tgt_count.get("error"),
                })
                continue

            s, t = src_count["row_count"], tgt_count["row_count"]
            results.append({
                "table": key,
                "source_count": s,
                "target_count": t,
                "delta": s - t,
                "in_sync": s == t,
            })

        out_of_sync = [r for r in results if not r.get("in_sync", True)]

        return {
            "source_dialect": get_dialect("source"),
            "target_dialect": get_dialect("target"),
            "tables_compared": len(common),
            "only_in_source": only_in_source,
            "only_in_target": only_in_target,
            "out_of_sync_count": len(out_of_sync),
            "all_in_sync": len(out_of_sync) == 0,
            "results": results,
        }
    except Exception as e:
        return {"error": str(e)}


def diff_record(table: str, pk_column: str, pk_value: str) -> dict:
    """Fetches a row from both connections by PK and diffs at the column level.
    Each side gets its own dialect-aware query, so Oracle vs Postgres works fine.
    """
    err = validate_identifiers(table=table, pk_column=pk_column)
    if err:
        return {"error": err, "table": table, "pk_column": pk_column, "pk_value": pk_value}
    try:
        src_row = _fetch_row(table, pk_column, pk_value, "source")
        tgt_row = _fetch_row(table, pk_column, pk_value, "target")

        result = {
            "table": table,
            "pk_column": pk_column,
            "pk_value": pk_value,
            "source_dialect": get_dialect("source"),
            "target_dialect": get_dialect("target"),
            "source_found": src_row is not None,
            "target_found": tgt_row is not None,
            "columns_differ": [],
            "diff": {},
            "identical": False,
        }

        if src_row is None or tgt_row is None:
            return result

        # Normalize column names to uppercase for cross-DB comparison
        src_norm = {k.upper(): v for k, v in src_row.items()}
        tgt_norm = {k.upper(): v for k, v in tgt_row.items()}

        for col in src_norm:
            src_val = src_norm.get(col)
            tgt_val = tgt_norm.get(col)
            if str(src_val) != str(tgt_val):  # stringify to handle type differences (e.g. NUMBER vs INT)
                result["columns_differ"].append(col)
                result["diff"][col] = {"source": src_val, "target": tgt_val}

        result["identical"] = len(result["columns_differ"]) == 0
        return result
    except Exception as e:
        return {"error": str(e), "table": table, "pk_column": pk_column, "pk_value": pk_value}


def _fetch_row(table: str, pk_column: str, pk_value: str, connection_name: str) -> dict | None:
    # Each call gets its own dialect so source and target can be different DB engines
    dialect = get_dialect(connection_name)
    conn = get_connection(connection_name)
    cursor = conn.cursor()

    ph = placeholder(dialect)
    tbl = quote(table, dialect) if "." not in table else table
    col = quote(pk_column, dialect) if dialect == "sqlserver" else pk_column

    query = limit_one(dialect, f"SELECT * FROM {tbl} WHERE {col} = {ph}")
    cursor.execute(query, [pk_value])

    row = cursor.fetchone()
    columns = [d[0] for d in cursor.description]
    conn.close()

    if row is None:
        return None
    return dict(zip(columns, row))
