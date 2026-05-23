"""
MCP Data Validation Server
Entry point — registers all tools and starts the stdio server.
"""

import time
from mcp.server.fastmcp import FastMCP

from config import get_connection
from tools.inventory import list_tables, get_row_count
from tools.comparison import compare_row_counts, diff_record
from tools.validation import validate_not_null, validate_pk_uniqueness

mcp = FastMCP("data-validator")


@mcp.tool()
def test_connection(connection_name: str) -> dict:
    """Test connectivity by opening a connection and running SELECT 1. Returns success, latency_ms, and any error."""
    start = time.perf_counter()
    try:
        conn = get_connection(connection_name)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
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


@mcp.tool()
def list_tables_tool(connection_name: str) -> dict:
    """List all user-defined tables in the schema for a named connection ("source" or "target")."""
    return list_tables(connection_name)


@mcp.tool()
def get_row_count_tool(table: str, connection_name: str) -> dict:
    """Return the row count for a table on a given connection ("source" or "target")."""
    return get_row_count(table, connection_name)


@mcp.tool()
def compare_row_counts_tool(table: str) -> dict:
    """Compare row counts for a table between source and target. Returns counts, delta, and in_sync flag."""
    return compare_row_counts(table)


@mcp.tool()
def diff_record_tool(table: str, pk_column: str, pk_value: str) -> dict:
    """
    Fetch a row from both source and target by primary key and return a column-level diff.
    pk_value should be passed as a string regardless of the column's underlying type.
    """
    return diff_record(table, pk_column, pk_value)


@mcp.tool()
def validate_not_null_tool(table: str, columns: list[str], connection_name: str) -> dict:
    """Check specified columns in a table for NULL values on a given connection."""
    return validate_not_null(table, columns, connection_name)


@mcp.tool()
def validate_pk_uniqueness_tool(table: str, pk_column: str, connection_name: str) -> dict:
    """Check for duplicate values in a primary key column on a given connection."""
    return validate_pk_uniqueness(table, pk_column, connection_name)


if __name__ == "__main__":
    mcp.run()
