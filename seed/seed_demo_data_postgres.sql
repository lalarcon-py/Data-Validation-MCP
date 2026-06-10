-- Demo seed data for MCP Data Validation Server (PostgreSQL)
-- Run this connected as a superuser, or a user with CREATEDB rights.
-- Intentional drift in demo_target:
--   - order 1005 missing (replication lag)
--   - null email on customer 3 (data quality issue)
--   - duplicate PK on order_items id=3 (botched upsert)

-- Create databases (run these outside a transaction block, i.e. not in psql's BEGIN)
-- CREATE DATABASE demo_source;
-- CREATE DATABASE demo_target;
-- Then connect to each and run the corresponding block below.

-- -----------------------------------------------
-- Run this block connected to demo_source
-- -----------------------------------------------

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(200),
    created_at DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE products (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    category VARCHAR(50)  NOT NULL,
    price    NUMERIC(10,2) NOT NULL
);

CREATE TABLE orders (
    id          SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id),
    total       NUMERIC(10,2) NOT NULL,
    status      VARCHAR(20) NOT NULL,
    created_at  DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INT NOT NULL REFERENCES orders(id),
    product_id INT NOT NULL REFERENCES products(id),
    quantity   INT NOT NULL,
    price      NUMERIC(10,2) NOT NULL
);

INSERT INTO customers (id, name, email, created_at) VALUES
(1, 'Alice Martin', 'alice@example.com', '2024-01-05'),
(2, 'Bob Chen',     'bob@example.com',   '2024-01-12'),
(3, 'Carol Davis',  NULL,                '2024-01-18'),
(4, 'David Kim',    'david@example.com', '2024-02-01'),
(5, 'Eva Rossi',    'eva@example.com',   '2024-02-14');

INSERT INTO products (id, name, category, price) VALUES
(1, 'Wireless Mouse', 'Electronics', 29.99),
(2, 'USB-C Hub',      'Electronics', 49.99),
(3, 'Desk Lamp',      'Office',      34.99),
(4, 'Notebook (A5)',  'Stationery',   8.99),
(5, 'Standing Desk',  'Furniture',  399.00);

INSERT INTO orders (id, customer_id, total, status, created_at) VALUES
(1001, 1, 79.98,  'completed', '2024-03-01'),
(1002, 2, 49.99,  'completed', '2024-03-03'),
(1003, 3, 34.99,  'shipped',   '2024-03-05'),
(1004, 4, 408.99, 'completed', '2024-03-07'),
(1005, 5, 8.99,   'pending',   '2024-03-09');

INSERT INTO order_items (id, order_id, product_id, quantity, price) VALUES
(1, 1001, 1, 1, 29.99),
(2, 1001, 3, 1, 34.99),
(3, 1002, 2, 1, 49.99),
(4, 1003, 3, 1, 34.99),
(5, 1004, 5, 1, 399.00),
(6, 1005, 4, 1,   8.99);


-- -----------------------------------------------
-- Run this block connected to demo_target
-- -----------------------------------------------

-- (same DROP/CREATE DDL as above, then:)

-- order 1005 intentionally missing
INSERT INTO orders (id, customer_id, total, status, created_at) VALUES
(1001, 1, 79.98,  'completed', '2024-03-01'),
(1002, 2, 49.99,  'completed', '2024-03-03'),
(1003, 3, 34.99,  'shipped',   '2024-03-05'),
(1004, 4, 408.99, 'completed', '2024-03-07');

-- id=3 duplicated to simulate botched upsert
-- Note: you need to drop the PK constraint on order_items in demo_target first
-- ALTER TABLE order_items DROP CONSTRAINT order_items_pkey;
INSERT INTO order_items (id, order_id, product_id, quantity, price) VALUES
(1, 1001, 1, 1, 29.99),
(2, 1001, 3, 1, 34.99),
(3, 1002, 2, 1, 49.99),
(3, 1002, 2, 1, 49.99),
(4, 1003, 3, 1, 34.99),
(5, 1004, 5, 1, 399.00);
