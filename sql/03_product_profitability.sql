-- =====================================================================
-- 03_product_profitability.sql
-- Hypothesis 2: Growth comes from low-margin categories / sub-categories (mix shift).
-- Techniques: RANK / ROW_NUMBER, running totals, PARTITION BY, self-comparison by year
-- =====================================================================

-- 3A. Rank sub-categories by profit within each category
SELECT category, sub_category,
       ROUND(SUM(sales), 2)  AS revenue,
       ROUND(SUM(profit), 2) AS profit,
       ROUND(100.0 * SUM(profit) / SUM(sales), 2) AS margin_pct,
       RANK() OVER (PARTITION BY category ORDER BY SUM(profit) DESC) AS rank_in_category,
       RANK() OVER (ORDER BY SUM(profit) DESC)                       AS rank_overall
FROM orders
GROUP BY category, sub_category
ORDER BY category, rank_in_category;


-- 3B. Mix shift: each sub-category's share of revenue vs share of profit, by year
WITH yr AS (
    SELECT EXTRACT(YEAR FROM order_date)::int AS yr, category, sub_category,
           SUM(sales) AS revenue, SUM(profit) AS profit
    FROM orders GROUP BY 1, 2, 3
)
SELECT yr, category, sub_category,
       ROUND(100.0 * revenue / SUM(revenue) OVER (PARTITION BY yr), 2)               AS revenue_share_pct,
       ROUND(100.0 * profit  / NULLIF(SUM(profit) OVER (PARTITION BY yr), 0), 2)     AS profit_share_pct,
       ROUND(100.0 * profit / revenue, 2)                                            AS margin_pct
FROM yr
ORDER BY yr, revenue_share_pct DESC;


-- 3C. Which sub-categories contributed most of the revenue GROWTH, and at what margin?
WITH yr AS (
    SELECT EXTRACT(YEAR FROM order_date)::int AS yr, category, sub_category,
           SUM(sales) AS revenue, SUM(profit) AS profit
    FROM orders GROUP BY 1, 2, 3
),
chg AS (
    SELECT yr, category, sub_category, revenue, profit,
           revenue - LAG(revenue) OVER (PARTITION BY sub_category ORDER BY yr) AS delta_revenue,
           profit  - LAG(profit)  OVER (PARTITION BY sub_category ORDER BY yr) AS delta_profit
    FROM yr
)
SELECT yr, category, sub_category,
       ROUND(delta_revenue, 2) AS delta_revenue,
       ROUND(delta_profit, 2)  AS delta_profit,
       ROUND(100.0 * profit / revenue, 2) AS current_margin_pct,
       ROUND(100.0 * delta_revenue / NULLIF(SUM(delta_revenue) OVER (PARTITION BY yr), 0), 2) AS share_of_revenue_growth_pct
FROM chg
WHERE delta_revenue IS NOT NULL
ORDER BY yr, delta_revenue DESC;


-- 3D. Pareto: how few products make most of the profit? (running share of positive profit)
WITH prod AS (
    SELECT product_id, MAX(product_name) AS product_name,
           SUM(sales) AS revenue, SUM(profit) AS profit
    FROM orders GROUP BY product_id
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY profit DESC) AS rn,
           SUM(profit) FILTER (WHERE profit > 0) OVER () AS total_positive_profit
    FROM prod
)
SELECT rn, product_id, product_name,
       ROUND(revenue, 2) AS revenue, ROUND(profit, 2) AS profit,
       ROUND(100.0 * SUM(GREATEST(profit, 0)) OVER (ORDER BY rn) / total_positive_profit, 2) AS cumulative_pct_of_positive_profit
FROM ranked
ORDER BY rn;


-- 3E. Top 10 and bottom 10 products by profit
(SELECT 'Top 10' AS list, product_id, MAX(product_name) AS product_name, category, sub_category,
        ROUND(SUM(sales), 2) AS revenue, ROUND(SUM(profit), 2) AS profit
 FROM orders GROUP BY product_id, category, sub_category
 ORDER BY SUM(profit) DESC LIMIT 10)
UNION ALL
(SELECT 'Bottom 10', product_id, MAX(product_name), category, sub_category,
        ROUND(SUM(sales), 2), ROUND(SUM(profit), 2)
 FROM orders GROUP BY product_id, category, sub_category
 ORDER BY SUM(profit) ASC LIMIT 10);


-- 3F. Products that sell well but lose money (high revenue rank, negative profit)
WITH prod AS (
    SELECT product_id, MAX(product_name) AS product_name, category, sub_category,
           SUM(sales) AS revenue, SUM(profit) AS profit, AVG(discount) AS avg_discount
    FROM orders GROUP BY product_id, category, sub_category
)
SELECT *, RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM prod
WHERE profit < 0
ORDER BY revenue DESC
LIMIT 25;
