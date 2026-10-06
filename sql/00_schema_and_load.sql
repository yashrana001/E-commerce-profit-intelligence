-- =====================================================================
-- 00_schema_and_load.sql  (PostgreSQL 13+)
-- Creates tables and loads the CSVs produced by python/01_clean_eda.py
--
-- Run from the repo root so the relative paths below resolve:
--   createdb superstore
--   psql -d superstore -f sql/00_schema_and_load.sql
-- =====================================================================

DROP TABLE IF EXISTS returns;
DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
    row_id        INTEGER,
    order_id      TEXT        NOT NULL,
    order_date    DATE        NOT NULL,
    ship_date     DATE,
    ship_mode     TEXT,
    customer_id   TEXT        NOT NULL,
    customer_name TEXT,
    segment       TEXT,
    country       TEXT,
    city          TEXT,
    state         TEXT,
    postal_code   TEXT,
    region        TEXT,
    product_id    TEXT,
    category      TEXT,
    sub_category  TEXT,
    product_name  TEXT,
    sales         NUMERIC(12,2),
    quantity      INTEGER,
    discount      NUMERIC(4,2),
    profit        NUMERIC(12,2)
);

CREATE TABLE returns (
    order_id TEXT PRIMARY KEY
);

-- \copy is a psql client command (reads the file from your machine)
\copy orders  FROM 'data/processed/orders_for_sql.csv'  WITH (FORMAT csv, HEADER true)
\copy returns FROM 'data/processed/returns_for_sql.csv' WITH (FORMAT csv, HEADER true)

CREATE INDEX idx_orders_order_id    ON orders (order_id);
CREATE INDEX idx_orders_customer_id ON orders (customer_id);
CREATE INDEX idx_orders_order_date  ON orders (order_date);

-- Convenience view: one derived discount band, used by several queries
CREATE OR REPLACE VIEW v_orders AS
SELECT o.*,
       CASE WHEN discount = 0    THEN '0%'
            WHEN discount <= 0.20 THEN '1-20%'
            WHEN discount <= 0.40 THEN '21-40%'
            ELSE '40%+' END                     AS discount_band,
       (profit < 0)                              AS loss_making,
       (r.order_id IS NOT NULL)                  AS returned
FROM orders o
LEFT JOIN returns r ON r.order_id = o.order_id;

-- Sanity checks
SELECT COUNT(*)                         AS order_lines,
       COUNT(DISTINCT order_id)         AS orders,
       COUNT(DISTINCT customer_id)      AS customers,
       MIN(order_date)                  AS first_date,
       MAX(order_date)                  AS last_date,
       ROUND(SUM(sales), 2)             AS total_sales,
       ROUND(SUM(profit), 2)            AS total_profit
FROM orders;
