from config import get_connection, get_dialect
from tools.dialect import normalize, query_to_dicts, placeholder
from tools.security import validate_identifiers, MAX_QUERY_ROWS


def get_table_schema(table: str, connection_name: str) -> dict:
    """Returns column definitions for a table: name, type, nullable, default, position."""
    err = validate_identifiers(table=table)
    if err:
        return {"error": err, "connection": connection_name, "table": table}
    try:
        dialect = get_dialect(connection_name)
        conn = get_connection(connection_name)
        cursor = conn.cursor()
        ph = placeholder(dialect)

        # Strip schema prefix if present (e.g. demo_source.orders -> orders)
        bare_table = table.split(".")[-1]
        t = normalize(bare_table, dialect)

        if dialect == "oracle":
            rows = query_to_dicts(cursor, f"""
                SELECT column_name, data_type, nullable, data_default, data_length,
                       data_precision, data_scale, column_id AS position
                FROM user_tab_columns
                WHERE table_name = {ph}
                ORDER BY column_id
            """, [t])
            columns = [
                {
                    "name": r["column_name"],
                    "type": r["data_type"],
                    "nullable": r["nullable"] == "Y",
                    "default": r["data_default"],
                    "position": r["position"],
                }
                for r in rows
            ]

        elif dialect == "postgres":
            rows = query_to_dicts(cursor, f"""
                SELECT column_name, data_type, is_nullable, column_default,
                       character_maximum_length, numeric_precision, numeric_scale, ordinal_position
                FROM information_schema.columns
                WHERE table_name = {ph} AND table_schema = current_schema()
                ORDER BY ordinal_position
            """, [t])
            columns = [
                {
                    "name": r["column_name"],
                    "type": r["data_type"],
                    "nullable": r["is_nullable"] == "YES",
                    "default": r["column_default"],
                    "position": r["ordinal_position"],
                }
                for r in rows
            ]

        else:  # sqlserver
            rows = query_to_dicts(cursor, f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT,
                       CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, ORDINAL_POSITION
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = {ph}
                ORDER BY ORDINAL_POSITION
            """, [t])
            columns = [
                {
                    "name": r["column_name"],
                    "type": r["data_type"],
                    "nullable": r["is_nullable"] == "YES",
                    "default": r["column_default"],
                    "position": r["ordinal_position"],
                }
                for r in rows
            ]

        conn.close()
        return {
            "connection": connection_name,
            "table": table,
            "column_count": len(columns),
            "columns": columns,
        }
    except Exception as e:
        return {"error": str(e), "connection": connection_name, "table": table}


def compare_table_schemas(table: str) -> dict:
    """Diffs column definitions between source and target for a given table."""
    try:
        src = get_table_schema(table, "source")
        tgt = get_table_schema(table, "target")

        if "error" in src:
            return {"error": f"source: {src['error']}", "table": table}
        if "error" in tgt:
            return {"error": f"target: {tgt['error']}", "table": table}

        src_cols = {c["name"].upper(): c for c in src["columns"]}
        tgt_cols = {c["name"].upper(): c for c in tgt["columns"]}

        only_in_source = [c for c in src_cols if c not in tgt_cols]
        only_in_target = [c for c in tgt_cols if c not in src_cols]

        type_mismatches = []
        for col in src_cols:
            if col in tgt_cols:
                s, t = src_cols[col], tgt_cols[col]
                diffs = {}
                if s["type"] != t["type"]:
                    diffs["type"] = {"source": s["type"], "target": t["type"]}
                if s["nullable"] != t["nullable"]:
                    diffs["nullable"] = {"source": s["nullable"], "target": t["nullable"]}
                if diffs:
                    type_mismatches.append({"column": col, "differences": diffs})

        return {
            "table": table,
            "source_column_count": len(src_cols),
            "target_column_count": len(tgt_cols),
            "only_in_source": only_in_source,
            "only_in_target": only_in_target,
            "type_mismatches": type_mismatches,
            "schemas_match": not any([only_in_source, only_in_target, type_mismatches]),
        }
    except Exception as e:
        return {"error": str(e), "table": table}


def get_constraints(table: str, connection_name: str) -> dict:
    """Returns all constraints on a table: primary keys, foreign keys, unique, check."""
    err = validate_identifiers(table=table)
    if err:
        return {"error": err, "connection": connection_name, "table": table}
    try:
        dialect = get_dialect(connection_name)
        conn = get_connection(connection_name)
        cursor = conn.cursor()
        ph = placeholder(dialect)

        bare_table = table.split(".")[-1]
        t = normalize(bare_table, dialect)

        if dialect == "oracle":
            rows = query_to_dicts(cursor, f"""
                SELECT c.constraint_name, c.constraint_type, c.status,
                       cc.column_name, cc.position, c.search_condition
                FROM user_constraints c
                JOIN user_cons_columns cc ON c.constraint_name = cc.constraint_name
                WHERE c.table_name = {ph}
                ORDER BY c.constraint_type, cc.position
            """, [t])

        elif dialect == "postgres":
            rows = query_to_dicts(cursor, f"""
                SELECT tc.constraint_name, tc.constraint_type, 'ENABLED' AS status,
                       kcu.column_name, kcu.ordinal_position AS position,
                       cc.check_clause AS search_condition
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                LEFT JOIN information_schema.check_constraints cc
                    ON tc.constraint_name = cc.constraint_name
                    AND tc.constraint_schema = cc.constraint_schema
                WHERE tc.table_name = {ph} AND tc.table_schema = current_schema()
                ORDER BY tc.constraint_type, kcu.ordinal_position
            """, [t])

        else:  # sqlserver
            rows = query_to_dicts(cursor, f"""
                SELECT tc.CONSTRAINT_NAME, tc.CONSTRAINT_TYPE, 'ENABLED' AS STATUS,
                       kcu.COLUMN_NAME, kcu.ORDINAL_POSITION AS POSITION,
                       cc.CHECK_CLAUSE AS SEARCH_CONDITION
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                    ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                LEFT JOIN INFORMATION_SCHEMA.CHECK_CONSTRAINTS cc
                    ON tc.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
                WHERE tc.TABLE_NAME = {ph}
                ORDER BY tc.CONSTRAINT_TYPE, kcu.ORDINAL_POSITION
            """, [t])

        conn.close()

        # Group by constraint name
        grouped = {}
        for r in rows:
            cname = r["constraint_name"]
            if cname not in grouped:
                grouped[cname] = {
                    "name": cname,
                    "type": r["constraint_type"],
                    "status": r.get("status"),
                    "columns": [],
                    "check_clause": r.get("search_condition"),
                }
            if r.get("column_name"):
                grouped[cname]["columns"].append(r["column_name"])

        constraints = list(grouped.values())
        return {
            "connection": connection_name,
            "table": table,
            "constraint_count": len(constraints),
            "constraints": constraints,
        }
    except Exception as e:
        return {"error": str(e), "connection": connection_name, "table": table}


def compare_constraints(table: str) -> dict:
    """Diffs constraints between source and target for a given table."""
    try:
        src = get_constraints(table, "source")
        tgt = get_constraints(table, "target")

        if "error" in src:
            return {"error": f"source: {src['error']}", "table": table}
        if "error" in tgt:
            return {"error": f"target: {tgt['error']}", "table": table}

        # Key by type + sorted columns so naming differences don't matter
        def constraint_key(c):
            return f"{c['type']}::{','.join(sorted(c['columns']))}"

        src_keys = {constraint_key(c): c for c in src["constraints"]}
        tgt_keys = {constraint_key(c): c for c in tgt["constraints"]}

        only_in_source = [c for k, c in src_keys.items() if k not in tgt_keys]
        only_in_target = [c for k, c in tgt_keys.items() if k not in src_keys]

        return {
            "table": table,
            "source_constraint_count": len(src_keys),
            "target_constraint_count": len(tgt_keys),
            "only_in_source": only_in_source,
            "only_in_target": only_in_target,
            "constraints_match": not any([only_in_source, only_in_target]),
        }
    except Exception as e:
        return {"error": str(e), "table": table}


def execute_query(sql: str, connection_name: str, params: list | None = None) -> dict:
    """Runs a read-only SELECT query and returns up to MAX_QUERY_ROWS rows.
    Only SELECT and WITH (CTE) statements are allowed.

    Two layers of protection against writes:
      1. Keyword blocklist check before the query runs.
      2. Transaction rollback after execution as a belt-and-suspenders backstop.

    Placeholder syntax by dialect:
      Oracle:     :1, :2, :3
      PostgreSQL: %s
      SQL Server: ?
    """
    # Layer 1: keyword check on normalized SQL (strips whitespace and comments)
    normalized = " ".join(sql.split()).upper()
    blocked = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "TRUNCATE", "MERGE", "EXEC", "EXECUTE"]
    for word in blocked:
        if word in normalized.split() or normalized.startswith(word):
            return {"error": f"Write operations are not allowed. Blocked keyword: {word}"}

    if not normalized.startswith("SELECT") and not normalized.startswith("WITH"):
        return {"error": "Only SELECT or WITH (CTE) queries are allowed."}

    conn = None
    try:
        dialect = get_dialect(connection_name)
        conn = get_connection(connection_name)
        cursor = conn.cursor()

        cursor.execute(sql, params) if params else cursor.execute(sql)
        cols = [d[0].lower() for d in cursor.description]
        rows = [dict(zip(cols, row)) for row in cursor.fetchmany(MAX_QUERY_ROWS)]

        # Layer 2: rollback anything that somehow slipped through
        try:
            conn.rollback()
        except Exception:
            pass

        truncated = cursor.fetchone() is not None  # check if there were more rows

        return {
            "connection": connection_name,
            "dialect": dialect,
            "row_count": len(rows),
            "truncated": truncated,
            "limit": MAX_QUERY_ROWS,
            "rows": rows,
        }
    except Exception as e:
        return {"error": str(e), "connection": connection_name}
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def execute_query_on_both(
    sql_source: str,
    sql_target: str,
) -> dict:
    """Runs SQL against both source and target simultaneously and returns both result sets.

    sql_source and sql_target can be different queries -- useful when the two databases
    have different schemas, different column names, or different dialects. For example,
    you might SUM a column called 'total' on one side and 'amount' on the other.

    Each query is written for its own database engine so JOINs, aggregates, CTEs, and
    anything else that's dialect-specific all work naturally.

    Returns both result sets side by side along with the dialect used for each,
    so Claude can compare, aggregate, or summarize across engines.
    """
    src = execute_query(sql_source, "source")
    tgt = execute_query(sql_target, "target")

    return {
        "source": src,
        "target": tgt,
        "cross_dialect": src.get("dialect") != tgt.get("dialect"),
    }
