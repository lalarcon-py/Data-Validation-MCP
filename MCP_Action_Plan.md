# MCP Data Validation Server - Action Plan

## Project Overview

A custom **Model Context Protocol (MCP) server** that connects Claude to a database layer for data validation and replication checks. Claude becomes the interface - you can ask natural language questions like *"compare row counts for the Orders table between source and target"* and Claude calls your tools to get real answers.

**Transport:** stdio (local, Claude Desktop)
**Language:** Python
**Database:** Generic - configurable via `.env` (supports SQL Server and Oracle out of the box)

---

## Demo Scenario (Generic)

To keep this project GA and portfolio-safe, we'll use a **fictional e-commerce dataset** as the demo context:

- **Source DB** - a simulated "production" database
- **Target DB** - a simulated "replica" or "warehouse" database
- **Tables** - `customers`, `orders`, `order_items`, `products`

Both databases can be run locally using **SQL Server Express** (free) or **SQLite** for zero-setup demos. Connection names in code are always `"source"` and `"target"` - never environment-specific names.

---

## Project Structure

```
MCP/
├── server.py                  # Entry point - MCP server definition
├── config.py                  # Loads named connections from .env
├── tools/
│   ├── __init__.py
│   ├── inventory.py           # list_tables, get_row_count
│   ├── comparison.py          # compare_row_counts, diff_record
│   └── validation.py          # validate_not_null, validate_pk_uniqueness
├── connections/
│   ├── __init__.py
│   ├── sqlserver.py           # pyodbc connection factory
│   └── oracle.py              # python-oracledb connection factory
├── seed/
│   └── seed_demo_data.sql     # Creates + populates demo tables
├── .env                       # Connection strings (gitignored)
├── .env.example               # Template for anyone cloning the repo
├── requirements.txt
├── README.md
└── claude_desktop_config.json
```

---

## Phase 1 - Project Scaffold

- [ ] Create the folder structure above
- [ ] Write `requirements.txt`:
  ```
  mcp>=1.0.0
  pyodbc>=5.0.0
  python-oracledb>=2.0.0
  python-dotenv>=1.0.0
  ```
- [ ] Write `.env.example` with placeholder values:
  ```
  SOURCE_DB_DRIVER=ODBC Driver 17 for SQL Server
  SOURCE_DB_SERVER=localhost
  SOURCE_DB_NAME=demo_source
  SOURCE_DB_USER=sa
  SOURCE_DB_PASSWORD=yourpassword

  TARGET_DB_DRIVER=ODBC Driver 17 for SQL Server
  TARGET_DB_SERVER=localhost
  TARGET_DB_NAME=demo_target
  TARGET_DB_USER=sa
  TARGET_DB_PASSWORD=yourpassword
  ```
- [ ] Add `.env` to `.gitignore`

---

## Phase 2 - Demo Data Setup

- [ ] Write `seed/seed_demo_data.sql` to create both source and target databases with:
  - `customers (id, name, email, created_at)`
  - `orders (id, customer_id, total, status, created_at)`
  - `order_items (id, order_id, product_id, quantity, price)`
  - `products (id, name, category, price)`
- [ ] Intentionally introduce drift between source and target:
  - A few rows missing from target `orders`
  - A null `email` in `customers` on the source side
  - A duplicate PK in target `order_items` (for validation demo)
- [ ] This gives every tool something real to find

---

## Phase 3 - Connection Layer

- [ ] Build `connections/sqlserver.py` - `pyodbc` connection factory keyed by name (`"source"`, `"target"`)
- [ ] Build `connections/oracle.py` - `python-oracledb` thin client factory (no Instant Client required)
- [ ] Build `config.py` - reads `.env`, returns the right factory based on driver type
- [ ] Connection objects are created fresh per tool call (no persistent pool needed for stdio transport)

---

## Phase 4 - Core Tools

Build in this order - each one is independently testable before moving to the next.

### 4.1 `test_connection(connection_name)`
- Attempts to open a connection and run `SELECT 1`
- Returns success/failure + latency
- **This is the smoke test for the whole pipeline**

### 4.2 `list_tables(connection_name)`
- Returns all user-defined table names in the schema
- Confirms Claude can see the database

### 4.3 `get_row_count(table, connection_name)`
- Returns integer row count for a single table on one connection

### 4.4 `compare_row_counts(table)`
- Runs `get_row_count` on both `source` and `target`
- Returns count for each + the delta
- First tool that demonstrates cross-DB value

### 4.5 `diff_record(table, pk_column, pk_value)`
- Fetches the full row from both source and target by primary key
- Returns a column-level diff showing which fields differ and their values
- Core replication validation tool

### 4.6 `validate_not_null(table, columns, connection_name)`
- Counts null values per specified column
- Returns a summary of which columns have nulls and how many

### 4.7 `validate_pk_uniqueness(table, pk_column, connection_name)`
- Checks for duplicate values in the primary key column
- Returns duplicates with their counts

---

## Phase 5 - MCP Server Wiring

- [ ] Register all tools in `server.py` using the `mcp` SDK
- [ ] Define typed input schemas for each tool (Claude uses these to know what parameters to pass)
- [ ] All tools return plain dicts - MCP serializes them to JSON for Claude automatically
- [ ] Error handling returns clean, readable error messages - **never raw stack traces** (Claude reads the output directly)
- [ ] Example tool registration pattern:
  ```python
  @mcp.tool()
  def compare_row_counts(table: str) -> dict:
      """Compare row counts for a table between source and target databases."""
      ...
  ```

---

## Phase 6 - Claude Desktop Integration

- [ ] Write `claude_desktop_config.json` snippet:
  ```json
  {
    "mcpServers": {
      "data-validator": {
        "command": "python",
        "args": ["C:/Users/YOU/Desktop/Portfolio Projects/MCP/server.py"],
        "env": {}
      }
    }
  }
  ```
- [ ] Document where to paste it on Windows:
  `%APPDATA%\Claude\claude_desktop_config.json`
- [ ] Test each tool through Claude Desktop before moving to Phase 7

---

## Phase 7 - Polish (Portfolio-Ready)

- [ ] Write `README.md` with:
  - Architecture diagram (ASCII or image)
  - Prerequisites and setup steps
  - How to seed the demo data
  - Example Claude prompts and expected responses
  - How to swap in your own database connections
- [ ] Add a `TOOLS.md` documenting every tool, its parameters, and example output
- [ ] Stretch goal: expose connection status as an **MCP Resource** (read-only, no tool call needed)
- [ ] Stretch goal: package with `uvx` so anyone can run it with zero manual install

---

## Example Claude Prompts (End State)

Once the server is running, these should all work in Claude Desktop:

```
"Test the connection to both source and target"
"List all tables in the source database"
"Compare row counts for the orders table"
"Show me any differences in order ID 1042 between source and target"
"Check the customers table for null emails on the source"
"Are there any duplicate primary keys in order_items on the target?"
```

---

## What "Done" Looks Like

You open Claude Desktop, ask a natural language question about your data, and Claude calls your MCP tools, hits your local databases, and returns a real answer - no plugins, no custom UI, no manual SQL. The entire codebase is generic, documented, and safe to share publicly.

CO-AUTHORED BY CLAUDE CODE
