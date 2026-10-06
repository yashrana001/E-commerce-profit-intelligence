-- =====================================================================
-- 02_discount_analysis.sql
-- Hypothesis 1: Higher discounts push line items into negative profit.
-- Techniques: CASE bands, conditional aggregation, window shares
-- =====================================================================

-- 2A. Margin by discount band
SELECT CASE WHEN discount = 0     THEN '0%'
            WHEN discount <= 0.20 THEN '1-20%'
            WHEN discount <= 0.40 THEN '21-40%'
            ELSE '40%+' END AS discount_band,
       COUNT(*)                                         AS lines,
       ROUND(SUM(sales), 2)                             AS revenue,
       ROUND(SUM(profit), 2)                            AS profit,
       ROUND(100.0 * SUM(profit) / SUM(sales), 2)       AS margin_pct,
       ROUND(100.0 * AVG((profit < 0)::int), 2)         AS pct_lines_loss_making
FROM orders
GROUP BY 1
ORDER BY MIN(discount);


-- 2B. Is high-discount revenue growing as a share of the total? (the "growth is bought" test)
WITH banded AS (
    SELECT EXTRACT(YEAR FROM order_date)::int AS yr,
           CASE WHEN discount > 0.20 THEN 'High (>20%)' ELSE 'Low (<=20%)' END AS bucket,
           SUM(sales)  AS revenue,
           SUM(profit) AS profit
    FROM orders
    GROUP BY 1, 2
)
SELECT yr, bucket,
       ROUND(revenue, 2) AS revenue,
       ROUND(profit, 2)  AS profit,
       ROUND(100.0 * revenue / SUM(revenue) OVER (PARTITION BY yr), 2) AS share_of_year_revenue_pct,
       ROUND(100.0 * profit / revenue, 2) AS margin_pct
FROM banded
ORDER BY yr, bucket;


-- 2C. Which sub-categories are discounted hardest, and what does it cost?
SELECT category, sub_category,
       ROUND(AVG(discount) * 100, 1)                          AS avg_discount_pct,
       ROUND(100.0 * AVG((discount > 0.20)::int), 1)          AS pct_lines_above_20,
       ROUND(SUM(profit), 2)                                  AS profit,
       ROUND(SUM(profit) FILTER (WHERE discount >  0.20), 2)  AS profit_high_discount,
       ROUND(SUM(profit) FILTER (WHERE discount <= 0.20), 2)  AS profit_low_discount
FROM orders
GROUP BY category, sub_category
ORDER BY avg_discount_pct DESC;


-- 2D. Break-even discount: average discount where margin crosses zero, per category
SELECT category,
       ROUND(discount * 100)::int AS discount_pct,
       COUNT(*)                   AS lines,
       ROUND(100.0 * SUM(profit) / SUM(sales), 2) AS margin_pct
FROM orders
GROUP BY category, discount
HAVING COUNT(*) >= 20      -- ignore thin buckets
ORDER BY category, discount;


-- 2E. How much profit do loss-making lines destroy, and what would margin be without them?
SELECT ROUND(SUM(profit), 2)                                         AS total_profit,
       ROUND(SUM(profit) FILTER (WHERE profit < 0), 2)               AS profit_destroyed_by_loss_lines,
       ROUND(SUM(profit) FILTER (WHERE profit >= 0), 2)              AS profit_from_profitable_lines,
       ROUND(100.0 * SUM(profit) / SUM(sales), 2)                    AS margin_pct,
       ROUND(100.0 * SUM(profit) FILTER (WHERE profit >= 0)
             / SUM(sales) FILTER (WHERE profit >= 0), 2)             AS margin_pct_profitable_lines_only
FROM orders;
