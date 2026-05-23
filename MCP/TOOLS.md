# Tool Reference

All tools are registered in `server.py` and exposed to Claude via the MCP protocol. Each tool returns a plain dict — MCP serializes it to JSON automatically. Errors are returned as `{"error": "<message>"}` rather than stack traces.

---

## test_connection

**Description:** Test connectivity to a named database by opening a connection and running `SELECT 1`.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `connection_name` | string | `"source"` or `"target"` |

**Example response (success):**
```json
{
  "connection": "source",
  "success": true,
  "latency_ms": 4.21
}
```

**Example response (failure):**
```json
{
  "connection": "target",
  "success": false,
  "latency_ms": 10003.1,
  "error": "Login timeout expired"
}
```

---

## list_tables

**Description:** Return all user-defined table names in the schema for a given connection.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `connection_name` | string | `"source"` or `"target"` |

**Example response:**
```json
{
  "connection": "source",
  "tables": ["customers", "order_items", "orders", "products"],
  "count": 4
}
```

---

## get_row_count

**Description:** Return the row count for a single table on one connection.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `table` | string | Table name |
| `connection_name` | string | `"source"` or `"target"` |

**Example response:**
```json
{
  "connection": "source",
  "table": "orders",
  "row_count": 5
}
```

---

## compare_row_counts

**Description:** Compare row counts for a table between source and target. Highlights replication lag or missing rows.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `table` | string | Table name |

**Example response:**
```json
{
  "table": "orders",
  "source_count": 5,
  "target_count": 4,
  "delta": 1,
  "in_sync": false
}
```

---

## diff_record

**Description:** Fetch a single row from both source and target by primary key and return a column-level diff.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `table` | string | Table name |
| `pk_column` | string | Primary key column name (e.g. `"id"`) |
| `pk_value` | string | Primary key value to look up |

**Example response (rows differ):**
```json
{
  "table": "orders",
  "pk_column": "id",
  "pk_value": "1001",
  "source_found": true,
  "target_found": true,
  "columns_differ": ["status"],
  "diff": {
    "status": { "source": "completed", "target": "shipped" }
  },
  "identical": false
}
```

**Example response (row missing from target):**
```json
{
  "table": "orders",
  "pk_column": "id",
  "pk_value": "1005",
  "source_found": true,
  "target_found": false,
  "columns_differ": [],
  "diff": {},
  "identical": false
}
```

---

## validate_not_null

**Description:** Count NULL values per specified column in a table. Useful for catching data quality issues before or after migration.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `table` | string | Table name |
| `columns` | list[string] | Column names to check |
| `connection_name` | string | `"source"` or `"target"` |

**Example response:**
```json
{
  "connection": "source",
  "table": "customers",
  "columns_checked": ["email", "name"],
  "nulls_found": { "email": 1 },
  "any_nulls": true
}
```

---

## validate_pk_uniqueness

**Description:** Check for duplicate values in a primary key column. Catches botched upserts or replication errors.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `table` | string | Table name |
| `pk_column` | string | Primary key column to check |
| `connection_name` | string | `"source"` or `"target"` |

**Example response (duplicates found):**
```json
{
  "connection": "target",
  "table": "order_items",
  "pk_column": "id",
  "duplicates": [
    { "pk_value": "3", "count": 2 }
  ],
  "duplicate_count": 1,
  "is_unique": false
}
```

**Example response (clean):**
```json
{
  "connection": "source",
  "table": "order_items",
  "pk_column": "id",
  "duplicates": [],
  "duplicate_count": 0,
  "is_unique": true
}
```
