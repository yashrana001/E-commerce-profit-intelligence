-- =====================================================================
-- 05_returns_and_regions.sql
-- Hypothesis 3: Some products/regions have return rates that eat margin.
-- Hypothesis 4: Some regions/states grow revenue but lose money.
-- Techniques: LEFT JOIN, distinct-count rates, window ranking, HAVING
-- =====================================================================

-- 5A. Return rate by category and region (order-level rate, via LEFT JOIN)
SELECT o.category, o.region,
       COUNT(DISTINCT o.order_id)                                            AS orders,
       COUNT(DISTINCT r.order_id)                                            AS returned_orders,
       ROUND(100.0 * COUNT(DISTINCT r.order_id) / COUNT(DISTINCT o.order_id), 2) AS return_rate_pct,
       ROUND(SUM(o.sales) FILTER (WHERE r.order_id IS NOT NULL), 2)          AS returned_revenue,
       ROUND(100.0 * SUM(o.sales) FILTER (WHERE r.order_id IS NOT NULL) / SUM(o.sales), 2) AS returned_revenue_pct
FROM orders o
LEFT JOIN returns r ON r.order_id = o.order_id
GROUP BY o.category, o.region
ORDER BY return_rate_pct DESC;


-- 5B. Return rate by sub-category, ranked
SELECT o.category, o.sub_category,
       ROUND(100.0 * COUNT(DISTINCT r.order_id) / COUNT(DISTINCT o.order_id), 2) AS return_rate_pct,
       ROUND(SUM(o.sales)  FILTER (WHERE r.order_id IS NOT NULL), 2)  AS returned_revenue,
       ROUND(SUM(o.profit) FILTER (WHERE r.order_id IS NOT NULL), 2)  AS profit_on_returned_orders,
       RANK() OVER (ORDER BY COUNT(DISTINCT r.order_id)::numeric / COUNT(DISTINCT o.order_id) DESC) AS return_rank
FROM orders o
LEFT JOIN returns r ON r.order_id = o.order_id
GROUP BY o.category, o.sub_category
ORDER BY return_rank;


-- 5C. Do returns concentrate among heavily discounted orders?
SELECT CASE WHEN o.discount = 0 THEN '0%'
            WHEN o.discount <= 0.20 THEN '1-20%'
            WHEN o.discount <= 0.40 THEN '21-40%'
            ELSE '40%+' END AS discount_band,
       ROUND(100.0 * COUNT(DISTINCT r.order_id) / COUNT(DISTINCT o.order_id), 2) AS return_rate_pct
FROM orders o
LEFT JOIN returns r ON r.order_id = o.order_id
GROUP BY 1
ORDER BY MIN(o.discount);


-- 5D. Regional performance, with year-over-year growth in revenue and profit
WITH reg AS (
    SELECT region, EXTRACT(YEAR FROM order_date)::int AS yr,
           SUM(sales) AS revenue, SUM(profit) AS profit
    FROM orders GROUP BY 1, 2
)
SELECT region, yr,
       ROUND(revenue, 2) AS revenue,
       ROUND(profit, 2)  AS profit,
       ROUND(100.0 * profit / revenue, 2) AS margin_pct,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (PARTITION BY region ORDER BY yr))
             / LAG(revenue) OVER (PARTITION BY region ORDER BY yr), 2) AS rev_yoy_pct,
       ROUND(100.0 * (profit - LAG(profit) OVER (PARTITION BY region ORDER BY yr))
             / NULLIF(ABS(LAG(profit) OVER (PARTITION BY region ORDER BY yr)), 0), 2) AS profit_yoy_pct
FROM reg
ORDER BY region, yr;


-- 5E. States that lose money, ranked within their region (regional drag)
SELECT region, state,
       ROUND(SUM(sales), 2)  AS revenue,
       ROUND(SUM(profit), 2) AS profit,
       ROUND(100.0 * SUM(profit) / SUM(sales), 2) AS margin_pct,
       ROUND(AVG(discount) * 100, 1)              AS avg_discount_pct,
       RANK() OVER (PARTITION BY region ORDER BY SUM(profit))  AS worst_in_region
FROM orders
GROUP BY region, state
HAVING SUM(profit) < 0
ORDER BY profit;


-- 5F. Growing revenue but shrinking profit: states where revenue rose and profit fell, latest year vs prior
WITH st AS (
    SELECT state, EXTRACT(YEAR FROM order_date)::int AS yr,
           SUM(sales) AS revenue, SUM(profit) AS profit
    FROM orders GROUP BY 1, 2
),
latest AS (SELECT MAX(yr) AS y FROM st)
SELECT cur.state,
       ROUND(cur.revenue - prev.revenue, 2) AS delta_revenue,
       ROUND(cur.profit  - prev.profit, 2)  AS delta_profit,
       ROUND(100.0 * cur.profit / cur.revenue, 2)   AS margin_now_pct,
       ROUND(100.0 * prev.profit / prev.revenue, 2) AS margin_prev_pct
FROM st cur
JOIN st prev ON prev.state = cur.state AND prev.yr = cur.yr - 1
JOIN latest l ON cur.yr = l.y
WHERE cur.revenue > prev.revenue AND cur.profit < prev.profit
ORDER BY delta_profit;


-- 5G. Segment x shipping mode profitability (does a service tier hurt margin?)
SELECT segment, ship_mode,
       ROUND(SUM(sales), 2)  AS revenue,
       ROUND(SUM(profit), 2) AS profit,
       ROUND(100.0 * SUM(profit) / SUM(sales), 2) AS margin_pct
FROM orders
GROUP BY segment, ship_mode
ORDER BY segment, margin_pct DESC;
