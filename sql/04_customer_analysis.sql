-- =====================================================================
-- 04_customer_analysis.sql
-- Hypothesis 5: New customers are acquired at deep discounts and don't repeat,
--               while a small repeat segment drives most profit.
-- Techniques: multi-step CTEs, NTILE, LAG, FIRST_VALUE, cohort index maths
-- =====================================================================

-- 4A. Customer-level aggregation: CLV, repeat flag, profit decile
WITH cust AS (
    SELECT customer_id,
           MIN(order_date)           AS first_order,
           MAX(order_date)           AS last_order,
           COUNT(DISTINCT order_id)  AS orders,
           SUM(sales)                AS revenue,
           SUM(profit)               AS profit,
           AVG(discount)             AS avg_discount
    FROM orders
    GROUP BY customer_id
)
SELECT customer_id, first_order, last_order, orders,
       ROUND(revenue, 2) AS revenue,
       ROUND(profit, 2)  AS lifetime_profit,
       ROUND(avg_discount * 100, 1) AS avg_discount_pct,
       CASE WHEN orders > 1 THEN 'Repeat' ELSE 'One-time' END AS customer_type,
       NTILE(10) OVER (ORDER BY profit DESC) AS profit_decile
FROM cust
ORDER BY lifetime_profit DESC;


-- 4B. Profit concentration: what share of total profit does each decile generate?
WITH cust AS (
    SELECT customer_id, SUM(profit) AS profit FROM orders GROUP BY customer_id
),
dec AS (
    SELECT *, NTILE(10) OVER (ORDER BY profit DESC) AS decile FROM cust
)
SELECT decile,
       COUNT(*)                                   AS customers,
       ROUND(SUM(profit), 2)                      AS profit,
       ROUND(100.0 * SUM(profit) / SUM(SUM(profit)) OVER (), 2) AS pct_of_total_profit,
       ROUND(100.0 * SUM(SUM(profit)) OVER (ORDER BY decile) / SUM(SUM(profit)) OVER (), 2) AS cumulative_pct
FROM dec
GROUP BY decile
ORDER BY decile;


-- 4C. Repeat vs one-time: value and acquisition discount
WITH first_order AS (
    -- the discount a customer got on their very first order (average over its lines)
    SELECT customer_id, AVG(discount) AS first_order_discount
    FROM (
        SELECT customer_id, discount,
               DENSE_RANK() OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS order_seq
        FROM orders
    ) t
    WHERE order_seq = 1
    GROUP BY customer_id
),
cust AS (
    SELECT customer_id, COUNT(DISTINCT order_id) AS orders,
           SUM(sales) AS revenue, SUM(profit) AS profit
    FROM orders GROUP BY customer_id
)
SELECT CASE WHEN c.orders > 1 THEN 'Repeat' ELSE 'One-time' END AS customer_type,
       COUNT(*)                                              AS customers,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)    AS pct_of_customers,
       ROUND(SUM(c.profit), 2)                               AS profit,
       ROUND(100.0 * SUM(c.profit) / SUM(SUM(c.profit)) OVER (), 2) AS pct_of_profit,
       ROUND(AVG(c.profit), 2)                               AS avg_profit_per_customer,
       ROUND(AVG(f.first_order_discount) * 100, 1)           AS avg_first_order_discount_pct
FROM cust c
JOIN first_order f USING (customer_id)
GROUP BY 1;


-- 4D. Repeat purchase behaviour: days between consecutive orders
WITH o AS (
    SELECT customer_id, order_id, MIN(order_date) AS order_date
    FROM orders GROUP BY customer_id, order_id
),
gaps AS (
    SELECT customer_id, order_date,
           order_date - LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS days_since_prev
    FROM o
)
SELECT COUNT(*)                                                         AS repeat_orders,
       ROUND(AVG(days_since_prev), 1)                                   AS avg_days_between_orders,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_since_prev)     AS median_days_between_orders
FROM gaps
WHERE days_since_prev IS NOT NULL;


-- 4E. New vs returning customers per year (revenue and profit)
WITH first_year AS (
    SELECT customer_id, EXTRACT(YEAR FROM MIN(order_date))::int AS acquisition_year
    FROM orders GROUP BY customer_id
)
SELECT EXTRACT(YEAR FROM o.order_date)::int AS yr,
       CASE WHEN EXTRACT(YEAR FROM o.order_date) = f.acquisition_year THEN 'New' ELSE 'Returning' END AS customer_status,
       COUNT(DISTINCT o.customer_id) AS customers,
       ROUND(SUM(o.sales), 2)        AS revenue,
       ROUND(SUM(o.profit), 2)       AS profit,
       ROUND(100.0 * SUM(o.profit) / SUM(o.sales), 2) AS margin_pct,
       ROUND(AVG(o.discount) * 100, 1) AS avg_discount_pct
FROM orders o
JOIN first_year f USING (customer_id)
GROUP BY 1, 2
ORDER BY 1, 2;


-- 4F. RFM in SQL (scores 1-5 with NTILE; snapshot = day after the last order)
WITH snap AS (
    SELECT MAX(order_date) + 1 AS snapshot_date FROM orders
),
base AS (
    SELECT o.customer_id,
           (s.snapshot_date - MAX(o.order_date))   AS recency_days,
           COUNT(DISTINCT o.order_id)              AS frequency,
           SUM(o.sales)                            AS monetary,
           SUM(o.profit)                           AS profit
    FROM orders o CROSS JOIN snap s
    GROUP BY o.customer_id, s.snapshot_date
),
scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC)            AS r_score,  -- most recent = 5
           NTILE(5) OVER (ORDER BY frequency, customer_id)       AS f_score,
           NTILE(5) OVER (ORDER BY monetary)                     AS m_score
    FROM base
),
segmented AS (
    SELECT *,
           CASE WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
                WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
                WHEN r_score >= 4 AND f_score <= 2 THEN 'New'
                WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
                WHEN r_score <= 2                  THEN 'Lost'
                ELSE 'Needs Attention' END AS segment
    FROM scored
)
SELECT segment,
       COUNT(*)                                             AS customers,
       ROUND(SUM(monetary), 2)                              AS revenue,
       ROUND(SUM(profit), 2)                                AS profit,
       ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 2) AS revenue_share_pct,
       ROUND(100.0 * SUM(profit)   / SUM(SUM(profit))   OVER (), 2) AS profit_share_pct,
       ROUND(100.0 * SUM(profit) / SUM(monetary), 2)        AS margin_pct
FROM segmented
GROUP BY segment
ORDER BY profit DESC;


-- 4G. Monthly cohort retention
WITH first_orders AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(order_date))::date AS cohort_month
    FROM orders GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT o.customer_id, f.cohort_month,
           DATE_TRUNC('month', o.order_date)::date AS activity_month
    FROM orders o
    JOIN first_orders f USING (customer_id)
),
indexed AS (
    SELECT customer_id, cohort_month,
           ((EXTRACT(YEAR  FROM activity_month) - EXTRACT(YEAR  FROM cohort_month)) * 12
          + (EXTRACT(MONTH FROM activity_month) - EXTRACT(MONTH FROM cohort_month)))::int AS period
    FROM activity
)
SELECT cohort_month, period,
       COUNT(DISTINCT customer_id) AS customers,
       ROUND(100.0 * COUNT(DISTINCT customer_id)
             / FIRST_VALUE(COUNT(DISTINCT customer_id)) OVER (PARTITION BY cohort_month ORDER BY period), 2) AS retention_pct
FROM indexed
GROUP BY cohort_month, period
ORDER BY cohort_month, period;
