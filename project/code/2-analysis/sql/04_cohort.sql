-- 04_cohort.sql: retensi kohort bulanan. Hanya bulan yang berakhir sebelum 1 Des 2011 (bulan penuh terakhir = Nov 2011).
CREATE OR REPLACE TABLE cohort_retention AS
WITH active AS (
    SELECT DISTINCT customer_id,
           CAST(date_trunc('month', invoice_ts) AS DATE) AS active_month
    FROM transactions_clean
),
act_cnt AS (
    SELECT c.cohort_month,
           DATE_DIFF('month', c.cohort_month, a.active_month) AS month_index,
           COUNT(DISTINCT a.customer_id) AS active_customers
    FROM active a
    JOIN customers c ON c.customer_id = a.customer_id
    WHERE a.active_month >= c.cohort_month
    GROUP BY 1, 2
),
size AS (
    SELECT cohort_month, COUNT(*) AS cohort_size FROM customers GROUP BY cohort_month
),
grid AS (
    SELECT s.cohort_month, k.month_index
    FROM size s
    CROSS JOIN (SELECT UNNEST(RANGE(0, 24)) AS month_index) k
)
SELECT g.cohort_month,
       g.month_index,
       s.cohort_size,
       COALESCE(a.active_customers, 0) AS active_customers,
       CASE WHEN CAST(g.cohort_month + INTERVAL (g.month_index) MONTH AS DATE) <= DATE '2011-11-01'
            THEN ROUND(COALESCE(a.active_customers, 0) * 1.0 / s.cohort_size, 6)
            ELSE NULL END AS retention_rate
FROM grid g
JOIN size s USING (cohort_month)
LEFT JOIN act_cnt a USING (cohort_month, month_index)
WHERE CAST(g.cohort_month + INTERVAL (g.month_index) MONTH AS DATE) <= DATE '2011-11-01'
ORDER BY g.cohort_month, g.month_index;
