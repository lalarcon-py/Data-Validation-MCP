"""
MCP Data Validation Server
Connects Claude to Oracle, PostgreSQL, or SQL Server for data validation,
schema inspection, and cross-database comparison.
"""

import time
from mcp.server.fastmcp import FastMCP

from config import get_connection, get_dialect
from tools.inventory import list_tables, get_row_count
from tools.comparison import compare_row_counts, compare_all_row_counts, diff_record
from tools.validation import validate_not_null, validate_pk_uniqueness
from tools.schema import (
    get_table_schema,
    compare_table_schemas,
    get_constraints,
    compare_constraints,
    execute_query,
    execute_query_on_both,
)

mcp = FastMCP("data-validator")


# --- Connectivity ---

@mcp.tool()
def test_connection(connection_name: str) -> dict:
    """Tests connectivity to 'source' or 'target' by running a simple query. Returns success, latency, and any error."""
    start = time.perf_counter()
    try:
        conn = get_connection(connection_name)
        dialect = get_dialect(connection_name)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL" if dialect == "oracle" else "SELECT 1")
        cursor.fetchone()
        conn.close()
        return {
            "connection": connection_name,
            "success": True,
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        }
    except Exception as e:
        return {
            "connection": connection_name,
            "success": False,
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "error": str(e),
        }


# --- Inventory ---

@mcp.tool()
def list_tables_tool(connection_name: str) -> dict:
    """Lists all user-defined tables in the schema for 'source' or 'target'."""
    return list_tables(connection_name)


@mcp.tool()
def get_row_count_tool(table: str, connection_name: str) -> dict:
    """Returns the row count for a single table on one connection."""
    return get_row_count(table, connection_name)


# --- Row Count Comparison ---

@mcp.tool()
def compare_row_counts_tool(table: str) -> dict:
    """Compares row counts for a table between source and target. Returns counts, delta, and whether they match."""
    return compare_row_counts(table)


@mcp.tool()
def compare_all_row_counts_tool() -> dict:
    """Compares row counts for every table in source vs target in one shot. Good for a quick full health check."""
    return compare_all_row_counts()


# --- Record Diff ---

@mcp.tool()
def diff_record_tool(table: str, pk_column: str, pk_value: str) -> dict:
    """Fetches a single row from both source and target by primary key and shows which columns differ."""
    return diff_record(table, pk_column, pk_value)


# --- Data Quality ---

@mcp.tool()
def validate_not_null_tool(table: str, columns: list[str], connection_name: str) -> dict:
    """Checks specified columns in a table for NULL values on a given connection."""
    return validate_not_null(table, columns, connection_name)


@mcp.tool()
def validate_pk_uniqueness_tool(table: str, pk_column: str, connection_name: str) -> dict:
    """Checks for duplicate values in a primary key column. Catches botched upserts and replication issues."""
    return validate_pk_uniqueness(table, pk_column, connection_name)


# --- Schema Inspection ---

@mcp.tool()
def get_table_schema_tool(table: str, connection_name: str) -> dict:
    """Returns full column definitions for a table: name, data type, nullable, default value, and position."""
    return get_table_schema(table, connection_name)


@mcp.tool()
def compare_table_schemas_tool(table: str) -> dict:
    """Diffs column definitions between source and target. Shows columns that only exist on one side and any type or nullability mismatches."""
    return compare_table_schemas(table)


# --- Constraint Inspection ---

@mcp.tool()
def get_constraints_tool(table: str, connection_name: str) -> dict:
    """Returns all constraints on a table: primary keys, foreign keys, unique constraints, and check constraints."""
    return get_constraints(table, connection_name)


@mcp.tool()
def compare_constraints_tool(table: str) -> dict:
    """Diffs constraints between source and target. Shows constraints that only exist on one side."""
    return compare_constraints(table)


# --- Arbitrary Query ---

@mcp.tool()
def execute_query_tool(sql: str, connection_name: str, params: list | None = None) -> dict:
    """Runs a read-only SELECT query against a connection and returns the results as rows.
    Use this when the other tools don't cover what you need. Only SELECT and WITH (CTE) statements are allowed.
    The response includes the dialect so you know which placeholder syntax was used."""
    return execute_query(sql, connection_name, params)


@mcp.tool()
def execute_query_on_both_tool(sql_source: str, sql_target: str) -> dict:
    """Runs SQL against source and target simultaneously and returns both result sets side by side.

    sql_source and sql_target can be completely different queries. This is intentional:
    source might be PostgreSQL with a column called 'total' and target might be SQL Server
    with a column called 'amount'. You write the right SQL for each side and get both
    results back together.

    Good for things like:
      - Comparing total revenue across two different DB engines
      - Running the same aggregation on two databases with different schemas
      - Any query where you want both outputs at once without calling execute_query twice
    """
    return execute_query_on_both(sql_source, sql_target)


if __name__ == "__main__":
    mcp.run()
