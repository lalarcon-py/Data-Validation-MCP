# Tool Reference

All tools return a plain dict. Errors come back as `{"error": "..."}` so Claude can read them and explain what went wrong.

---

## test_connection

Tests that a connection is alive by running a simple query.

| Param | Type | Description |
|---|---|---|
| `connection_name` | string | "source" or "target" |

```json
{ "connection": "source", "success": true, "latency_ms": 42.1 }
```

---

## list_tables

Lists all user-defined tables in the schema.

| Param | Type | Description |
|---|---|---|
| `connection_name` | string | "source" or "target" |

```json
{ "connection": "source", "tables": ["customers", "orders"], "count": 2 }
```

---

## get_row_count

Row count for one table on one connection.

| Param | Type | Description |
|---|---|---|
| `table` | string | Table name |
| `connection_name` | string | "source" or "target" |

---

## compare_row_counts

Side-by-side row count for a table across both connections.

| Param | Type | Description |
|---|---|---|
| `table` | string | Table name |

```json
{ "table": "orders", "source_count": 5, "target_count": 4, "delta": 1, "in_sync": false }
```

---

## compare_all_row_counts

Runs compare_row_counts for every table in source vs target in one call. Good for a quick full health check.

No parameters.

```json
{
  "tables_checked": 4,
  "out_of_sync_count": 1,
  "all_in_sync": false,
  "results": [...]
}
```

---

## diff_record

Fetches a row from both connections by primary key and shows which columns differ.

| Param | Type | Description |
|---|---|---|
| `table` | string | Table name |
| `pk_column` | string | Primary key column (e.g. "id") |
| `pk_value` | string | Value to look up |

```json
{
  "source_found": true,
  "target_found": false,
  "columns_differ": [],
  "identical": false
}
```

---

## validate_not_null

Counts nulls in specified columns.

| Param | Type | Description |
|---|---|---|
| `table` | string | Table name |
| `columns` | list | Column names to check |
| `connection_name` | string | "source" or "target" |

```json
{ "nulls_found": { "email": 1 }, "any_nulls": true }
```

---

## validate_pk_uniqueness

Checks for duplicate values in a primary key column.

| Param | Type | Description |
|---|---|---|
| `table` | string | Table name |
| `pk_column` | string | Column to check |
| `connection_name` | string | "source" or "target" |

```json
{ "duplicates": [{ "pk_value": "3", "count": 2 }], "is_unique": false }
```

---

## get_table_schema

Returns full column definitions for a table.

| Param | Type | Description |
|---|---|---|
| `table` | string | Table name |
| `connection_name` | string | "source" or "target" |

```json
{
  "columns": [
    { "name": "ID", "type": "NUMBER", "nullable": false, "default": null, "position": 1 },
    { "name": "EMAIL", "type": "VARCHAR2", "nullable": true, "default": null, "position": 3 }
  ]
}
```

---

## compare_table_schemas

Diffs column definitions between source and target for a table.

| Param | Type | Description |
|---|---|---|
| `table` | string | Table name |

```json
{
  "only_in_source": ["LEGACY_FIELD"],
  "only_in_target": [],
  "type_mismatches": [
    { "column": "STATUS", "differences": { "type": { "source": "VARCHAR2", "target": "CHAR" } } }
  ],
  "schemas_match": false
}
```

---

## get_constraints

Returns all constraints on a table (PK, FK, unique, check).

| Param | Type | Description |
|---|---|---|
| `table` | string | Table name |
| `connection_name` | string | "source" or "target" |

```json
{
  "constraints": [
    { "name": "SYS_C001", "type": "P", "columns": ["ID"] },
    { "name": "SYS_C002", "type": "C", "columns": ["EMAIL"], "check_clause": "EMAIL IS NOT NULL" }
  ]
}
```

---

## compare_constraints

Diffs constraints between source and target for a table.

| Param | Type | Description |
|---|---|---|
| `table` | string | Table name |

```json
{
  "only_in_source": [],
  "only_in_target": [{ "name": "UQ_EMAIL", "type": "U", "columns": ["EMAIL"] }],
  "constraints_match": false
}
```

---

## execute_query

Runs an arbitrary read-only SELECT query and returns the results. Use this when the other tools don't cover what you need.

| Param | Type | Description |
|---|---|---|
| `sql` | string | A SELECT or WITH (CTE) statement |
| `connection_name` | string | "source" or "target" |
| `params` | list (optional) | Bind parameters for the query |

```json
{
  "row_count": 3,
  "rows": [
    { "status": "completed", "count": 3 },
    { "status": "pending", "count": 1 }
  ]
}
```
