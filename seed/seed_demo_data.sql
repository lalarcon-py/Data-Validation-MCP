-- Demo seed data for MCP Data Validation Server (Oracle)
-- Run this connected as SYS with SYSDBA role against orclpdb.
-- Assumes demo_source and demo_target users already exist.
--
-- Intentional drift in target:
--   - order 1005 missing (replication lag)
--   - null email on customer 3 (data quality issue)
--   - duplicate PK on order_items id=3 (botched upsert)

-- -----------------------------------------------
-- Drop existing tables (reverse FK order)
-- -----------------------------------------------
BEGIN EXECUTE IMMEDIATE 'DROP TABLE demo_source.order_items'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE demo_source.orders';      EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE demo_source.products';    EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE demo_source.customers';   EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE demo_target.order_items'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE demo_target.orders';      EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE demo_target.products';    EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE demo_target.customers';   EXCEPTION WHEN OTHERS THEN NULL; END;
/

-- -----------------------------------------------
-- SOURCE tables
-- -----------------------------------------------
CREATE TABLE demo_source.customers (
    id         NUMBER PRIMARY KEY,
    name       VARCHAR2(100) NOT NULL,
    email      VARCHAR2(200),
    created_at DATE DEFAULT SYSDATE NOT NULL
);

CREATE TABLE demo_source.products (
    id       NUMBER PRIMARY KEY,
    name     VARCHAR2(100) NOT NULL,
    category VARCHAR2(50)  NOT NULL,
    price    NUMBER(10,2)  NOT NULL
);

CREATE TABLE demo_source.orders (
    id          NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL REFERENCES demo_source.customers(id),
    total       NUMBER(10,2) NOT NULL,
    status      VARCHAR2(20) NOT NULL,
    created_at  DATE DEFAULT SYSDATE NOT NULL
);

CREATE TABLE demo_source.order_items (
    id         NUMBER PRIMARY KEY,
    order_id   NUMBER NOT NULL REFERENCES demo_source.orders(id),
    product_id NUMBER NOT NULL REFERENCES demo_source.products(id),
    quantity   NUMBER NOT NULL,
    price      NUMBER(10,2) NOT NULL
);

-- -----------------------------------------------
-- SOURCE data
-- -----------------------------------------------
INSERT INTO demo_source.customers VALUES (1, 'Alice Martin', 'alice@example.com', DATE '2024-01-05');
INSERT INTO demo_source.customers VALUES (2, 'Bob Chen',     'bob@example.com',   DATE '2024-01-12');
INSERT INTO demo_source.customers VALUES (3, 'Carol Davis',  NULL,                DATE '2024-01-18');
INSERT INTO demo_source.customers VALUES (4, 'David Kim',    'david@example.com', DATE '2024-02-01');
INSERT INTO demo_source.customers VALUES (5, 'Eva Rossi',    'eva@example.com',   DATE '2024-02-14');

INSERT INTO demo_source.products VALUES (1, 'Wireless Mouse', 'Electronics', 29.99);
INSERT INTO demo_source.products VALUES (2, 'USB-C Hub',      'Electronics', 49.99);
INSERT INTO demo_source.products VALUES (3, 'Desk Lamp',      'Office',      34.99);
INSERT INTO demo_source.products VALUES (4, 'Notebook (A5)',  'Stationery',   8.99);
INSERT INTO demo_source.products VALUES (5, 'Standing Desk',  'Furniture',  399.00);

INSERT INTO demo_source.orders VALUES (1001, 1, 79.98,  'completed', DATE '2024-03-01');
INSERT INTO demo_source.orders VALUES (1002, 2, 49.99,  'completed', DATE '2024-03-03');
INSERT INTO demo_source.orders VALUES (1003, 3, 34.99,  'shipped',   DATE '2024-03-05');
INSERT INTO demo_source.orders VALUES (1004, 4, 408.99, 'completed', DATE '2024-03-07');
INSERT INTO demo_source.orders VALUES (1005, 5, 8.99,   'pending',   DATE '2024-03-09');

INSERT INTO demo_source.order_items VALUES (1, 1001, 1, 1, 29.99);
INSERT INTO demo_source.order_items VALUES (2, 1001, 3, 1, 34.99);
INSERT INTO demo_source.order_items VALUES (3, 1002, 2, 1, 49.99);
INSERT INTO demo_source.order_items VALUES (4, 1003, 3, 1, 34.99);
INSERT INTO demo_source.order_items VALUES (5, 1004, 5, 1, 399.00);
INSERT INTO demo_source.order_items VALUES (6, 1005, 4, 1,   8.99);

COMMIT;

-- -----------------------------------------------
-- TARGET tables
-- -----------------------------------------------
CREATE TABLE demo_target.customers (
    id         NUMBER PRIMARY KEY,
    name       VARCHAR2(100) NOT NULL,
    email      VARCHAR2(200),
    created_at DATE DEFAULT SYSDATE NOT NULL
);

CREATE TABLE demo_target.products (
    id       NUMBER PRIMARY KEY,
    name     VARCHAR2(100) NOT NULL,
    category VARCHAR2(50)  NOT NULL,
    price    NUMBER(10,2)  NOT NULL
);

CREATE TABLE demo_target.orders (
    id          NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL REFERENCES demo_target.customers(id),
    total       NUMBER(10,2) NOT NULL,
    status      VARCHAR2(20) NOT NULL,
    created_at  DATE DEFAULT SYSDATE NOT NULL
);

-- No PK constraint — allows duplicate id to simulate botched upsert
CREATE TABLE demo_target.order_items (
    id         NUMBER NOT NULL,
    order_id   NUMBER NOT NULL,
    product_id NUMBER NOT NULL,
    quantity   NUMBER NOT NULL,
    price      NUMBER(10,2) NOT NULL
);

-- -----------------------------------------------
-- TARGET data (with drift)
-- -----------------------------------------------
INSERT INTO demo_target.customers VALUES (1, 'Alice Martin', 'alice@example.com', DATE '2024-01-05');
INSERT INTO demo_target.customers VALUES (2, 'Bob Chen',     'bob@example.com',   DATE '2024-01-12');
INSERT INTO demo_target.customers VALUES (3, 'Carol Davis',  NULL,                DATE '2024-01-18');
INSERT INTO demo_target.customers VALUES (4, 'David Kim',    'david@example.com', DATE '2024-02-01');
INSERT INTO demo_target.customers VALUES (5, 'Eva Rossi',    'eva@example.com',   DATE '2024-02-14');

INSERT INTO demo_target.products VALUES (1, 'Wireless Mouse', 'Electronics', 29.99);
INSERT INTO demo_target.products VALUES (2, 'USB-C Hub',      'Electronics', 49.99);
INSERT INTO demo_target.products VALUES (3, 'Desk Lamp',      'Office',      34.99);
INSERT INTO demo_target.products VALUES (4, 'Notebook (A5)',  'Stationery',   8.99);
INSERT INTO demo_target.products VALUES (5, 'Standing Desk',  'Furniture',  399.00);

-- order 1005 intentionally missing
INSERT INTO demo_target.orders VALUES (1001, 1, 79.98,  'completed', DATE '2024-03-01');
INSERT INTO demo_target.orders VALUES (1002, 2, 49.99,  'completed', DATE '2024-03-03');
INSERT INTO demo_target.orders VALUES (1003, 3, 34.99,  'shipped',   DATE '2024-03-05');
INSERT INTO demo_target.orders VALUES (1004, 4, 408.99, 'completed', DATE '2024-03-07');

-- id=3 duplicated to simulate botched upsert
INSERT INTO demo_target.order_items VALUES (1, 1001, 1, 1, 29.99);
INSERT INTO demo_target.order_items VALUES (2, 1001, 3, 1, 34.99);
INSERT INTO demo_target.order_items VALUES (3, 1002, 2, 1, 49.99);
INSERT INTO demo_target.order_items VALUES (3, 1002, 2, 1, 49.99);
INSERT INTO demo_target.order_items VALUES (4, 1003, 3, 1, 34.99);
INSERT INTO demo_target.order_items VALUES (5, 1004, 5, 1, 399.00);

COMMIT;
