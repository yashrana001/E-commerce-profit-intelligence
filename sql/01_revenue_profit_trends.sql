-- =====================================================================
-- 01_revenue_profit_trends.sql
-- Question: Is revenue growing faster than profit, and when did it start?
-- Techniques: CTEs, LAG, rolling window frames
-- =====================================================================

-- 1A. Monthly revenue, profit, margin and growth rates
WITH monthly AS (
    SELECT DATE_TRUNC('month', order_date)::date AS month,
           SUM(sales)  AS revenue,
           SUM(profit) AS profit
    FROM orders
    GROUP BY 1
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(profit, 2)  AS profit,
       ROUND(100.0 * profit / NULLIF(revenue, 0), 2) AS margin_pct,
       ROUND(100.0 * (revenue - LAG(revenue) OVER w) / NULLIF(LAG(revenue) OVER w, 0), 2) AS rev_growth_pct,
       ROUND(100.0 * (profit  - LAG(profit)  OVER w) / NULLIF(ABS(LAG(profit) OVER w), 0), 2) AS profit_growth_pct
FROM monthly
WINDOW w AS (ORDER BY month)
ORDER BY month;


-- 1B. Year-over-year view with the gap between revenue growth and profit growth
WITH yearly AS (
    SELECT EXTRACT(YEAR FROM order_date)::int AS yr,
           SUM(sales)  AS revenue,
           SUM(profit) AS profit
    FROM orders
    GROUP BY 1
)
SELECT yr,
       ROUND(revenue, 2) AS revenue,
       ROUND(profit, 2)  AS profit,
       ROUND(100.0 * profit / revenue, 2) AS margin_pct,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY yr)) / LAG(revenue) OVER (ORDER BY yr), 2) AS rev_yoy_pct,
       ROUND(100.0 * (profit  - LAG(profit)  OVER (ORDER BY yr)) / NULLIF(ABS(LAG(profit) OVER (ORDER BY yr)), 0), 2) AS profit_yoy_pct,
       ROUND(100.0 * profit / revenue
             - 100.0 * LAG(profit) OVER (ORDER BY yr) / LAG(revenue) OVER (ORDER BY yr), 2) AS margin_change_pts
FROM yearly
ORDER BY yr;


-- 1C. Rolling 3-month margin (smooths seasonality so the trend is visible)
WITH monthly AS (
    SELECT DATE_TRUNC('month', order_date)::date AS month,
           SUM(sales) AS revenue, SUM(profit) AS profit
    FROM orders GROUP BY 1
)
SELECT month,
       ROUND(100.0 * SUM(profit)  OVER r3 / NULLIF(SUM(revenue) OVER r3, 0), 2) AS rolling_3m_margin_pct,
       ROUND(SUM(revenue) OVER r3, 2) AS rolling_3m_revenue
FROM monthly
WINDOW r3 AS (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
ORDER BY month;


-- 1D. Seasonality: which calendar months carry the weakest margin?
SELECT EXTRACT(MONTH FROM order_date)::int AS month_num,
       TO_CHAR(order_date, 'Mon')           AS month_name,
       ROUND(SUM(sales), 2)                 AS revenue,
       ROUND(SUM(profit), 2)                AS profit,
       ROUND(100.0 * SUM(profit) / SUM(sales), 2) AS margin_pct
FROM orders
GROUP BY 1, 2
ORDER BY 1;
