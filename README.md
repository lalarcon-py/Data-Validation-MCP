# MCP Data Validation Server

A Python MCP server that hooks Claude Desktop into a database layer so you can run data validation and cross-database comparisons just by asking questions in plain English. No writing SQL by hand, no copy-pasting results. You ask, Claude calls the right tool, you get an answer.

Supports Oracle, PostgreSQL, and SQL Server. Built with the MCP SDK and Python.

```
Claude Desktop  --stdio-->  server.py
                               |-- inventory (list tables, row counts)
                               |-- comparison (diff rows and counts)
                               |-- validation (nulls, duplicate PKs)
                               |-- schema (columns, constraints, arbitrary queries)
                                         |
                           source DB --- target DB
```

Built with help from [Claude Cowork](https://claude.ai) for scaffolding and tool design.

---

## Prerequisites

- Python 3.11+
- Claude Desktop
- One of: Oracle 19c, PostgreSQL 12+, or SQL Server with ODBC Driver 17

---

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Configure your connections**

```bash
cp .env.example .env
```

Fill in your credentials. Examples for each database are in `.env.example`. For Oracle you need a DSN, for Postgres you need host/port/name, for SQL Server you need the server name and DB name.

**3. Seed the demo data (optional)**

Oracle: run `seed/seed_demo_data.sql` in SQL Developer as SYS with SYSDBA role against orclpdb.

PostgreSQL: create `demo_source` and `demo_target` databases, then run `seed/seed_demo_data_postgres.sql` against each.

**4. Register with Claude Desktop**

Add this to `%APPDATA%\Claude\claude_desktop_config.json` (update the path to match your setup):

```json
{
  "mcpServers": {
    "data-validator": {
      "command": "C:\\path\\to\\MCP\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\MCP\\server.py"]
    }
  }
}
```

Restart Claude Desktop and the tools will be available.

---

## What you can ask Claude

```
"Test both connections"
"List the tables in source"
"Compare row counts for all tables"
"What columns are in the orders table on source?"
"Are there any schema differences in the orders table between source and target?"
"What constraints does the customers table have?"
"Are there any constraint differences between source and target for order_items?"
"Show me what's different about order ID 1004 between source and target"
"Check customers for null emails on source"
"Are there any duplicate PKs in order_items on target?"
"Run this query against source: SELECT status, COUNT(*) FROM orders GROUP BY status"
```

---

## Tools

See [TOOLS.md](TOOLS.md) for the full reference with parameters and example outputs.

---

## Swapping in your own databases

Update `.env` with your real connection strings. Table and column names are all passed as parameters so nothing in the code is hardcoded to the demo schema.

---

## Database support

| Feature | Oracle | PostgreSQL | SQL Server |
|---|---|---|---|
| Connection test | Yes | Yes | Yes |
| List tables | Yes | Yes | Yes |
| Row counts | Yes | Yes | Yes |
| Record diff | Yes | Yes | Yes |
| Schema inspection | Yes | Yes | Yes |
| Constraint inspection | Yes | Yes | Yes |
| Arbitrary queries | Yes | Yes | Yes |
