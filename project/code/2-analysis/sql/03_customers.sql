-- 03_customers.sql: satu baris per pelanggan + skor RFM. Tanggal acuan = hari setelah transaksi terakhir.
CREATE OR REPLACE TABLE customers AS
WITH ref AS (
    SELECT CAST(MAX(invoice_date) AS DATE) + INTERVAL 1 DAY AS ref_date FROM transactions_clean
),
per_cust AS (
    SELECT customer_id,
           MIN(invoice_ts)                         AS first_purchase_ts,
           MAX(invoice_ts)                         AS last_purchase_ts,
           COUNT(DISTINCT invoice)                 AS frequency,
           ROUND(SUM(line_revenue), 4)             AS monetary,
           COUNT(DISTINCT stock_code)              AS distinct_products,
           COUNT(DISTINCT country)                 AS distinct_countries
    FROM transactions_clean
    GROUP BY customer_id
),
first_inv AS (
    -- nilai invoice pertama tiap pelanggan (untuk Q3)
    SELECT t.customer_id, ROUND(SUM(t.line_revenue), 4) AS first_invoice_value
    FROM transactions_clean t
    JOIN (SELECT customer_id, MIN(invoice_ts) AS mn FROM transactions_clean GROUP BY customer_id) f
      ON t.customer_id = f.customer_id AND t.invoice_ts = f.mn
    GROUP BY t.customer_id
),
home AS (
    -- negara utama (negara pada invoice pertama, tie-breaker alfabet)
    SELECT customer_id, arg_min(country, invoice_ts) AS country_first
    FROM transactions_clean GROUP BY customer_id
),
base AS (
    SELECT p.customer_id,
           CAST(p.first_purchase_ts AS DATE)                         AS first_purchase,
           CAST(date_trunc('month', p.first_purchase_ts) AS DATE)    AS cohort_month,
           CAST(p.last_purchase_ts AS DATE)                          AS last_purchase,
           DATE_DIFF('day', CAST(p.last_purchase_ts AS DATE), r.ref_date) AS recency_days,
           p.frequency, p.monetary, p.distinct_products,
           fi.first_invoice_value,
           h.country_first AS country
    FROM per_cust p
    CROSS JOIN ref r
    JOIN first_inv fi ON fi.customer_id = p.customer_id
    JOIN home h ON h.customer_id = p.customer_id
)
SELECT b.*,
       6 - NTILE(5) OVER (ORDER BY recency_days ASC, customer_id) AS r_score,
           NTILE(5) OVER (ORDER BY frequency ASC, customer_id)     AS f_score,
           NTILE(5) OVER (ORDER BY monetary ASC, customer_id)      AS m_score
FROM base b
ORDER BY customer_id;
