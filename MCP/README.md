# MCP Data Validation Server

A Python MCP server that connects Claude Desktop to a database layer for data validation and replication checks. Ask natural language questions like *"compare row counts for orders between source and target"* and Claude calls the tools to get real answers — no custom UI, no manual SQL.

```
Claude Desktop  ──stdio──►  server.py
                               ├── inventory tools
                               ├── comparison tools
                               └── validation tools
                                       │
                          ┌───────────┴────────────┐
                       demo_source            demo_target
```

Built with Python, [MCP SDK](https://github.com/modelcontextprotocol/python-sdk), and [Claude Cowork](https://claude.ai) to accelerate the scaffolding and tool design.

---

## Prerequisites

- Python 3.11+
- SQL Server (Express is fine) with ODBC Driver 17
- Claude Desktop

---

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Configure connections**

```bash
cp .env.example .env
```

Fill in `.env` with your SQL Server credentials. Leave `USER`/`PASSWORD` blank to use Windows Integrated Auth.

For Oracle, set `*_DRIVER=oracle` and add `*_DSN=<host>/<service>`.

**3. Seed the demo databases**

```bash
sqlcmd -S localhost -i seed/seed_demo_data.sql
```

This creates `demo_source` and `demo_target` with intentional drift so every tool has something real to find.

**4. Register with Claude Desktop**

Merge `claude_desktop_config.json` into `%APPDATA%\Claude\claude_desktop_config.json`, updating the path to `server.py`. Restart Claude Desktop.

---

## Tools

See [TOOLS.md](TOOLS.md) for the full reference. Quick list:

- `test_connection` — smoke test for a named connection
- `list_tables` — discover what tables exist
- `get_row_count` — row count for one table on one connection
- `compare_row_counts` — side-by-side count with delta
- `diff_record` — column-level diff for a single row by PK
- `validate_not_null` — detect nulls in specified columns
- `validate_pk_uniqueness` — detect duplicate PKs

---

## Example prompts

```
"Test the connection to both source and target"
"List all tables in the source database"
"Compare row counts for the orders table"
"Show me any differences in order ID 1004 between source and target"
"Check the customers table for null emails on source"
"Are there any duplicate primary keys in order_items on target?"
```

---

## Swapping in your own databases

Update `.env` with real connection strings and point Claude at your actual tables. No code changes needed — table and column names are all passed as parameters.
