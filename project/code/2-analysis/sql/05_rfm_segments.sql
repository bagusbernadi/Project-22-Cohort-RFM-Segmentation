-- 05_rfm_segments.sql: aturan segmen (dim_segment) dan segmen tiap pelanggan. Urutan CASE = prioritas (lihat docs/definitions.md).
CREATE OR REPLACE TABLE dim_segment AS
SELECT * FROM (VALUES
    (1, 'Champions',       'R 4-5, F 4-5',           'pertahankan'),
    (2, 'Loyal',           'R 3-5, F 3-5 (selain Champions)', 'pertahankan'),
    (3, 'New',             'R 5, F 1',               'pertahankan'),
    (4, 'Potential Loyalist', 'R 4-5, F 1-2 (selain New)', 'pertahankan'),
    (5, 'Need Attention',  'R 3, F 1-2',             'aktifkan kembali'),
    (6, 'At Risk',         'R 1-2, F 3-5',           'aktifkan kembali'),
    (7, 'Lost',            'R 1, F 1',               'biarkan'),
    (8, 'Hibernating',     'R 1-2, F 1-2 (selain Lost)', 'biarkan')
) AS t(urut, segment, rule_ringkas, suggested_action);

CREATE OR REPLACE TABLE customers_seg AS
SELECT c.*,
       CASE
           WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
           WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
           WHEN r_score = 5 AND f_score = 1   THEN 'New'
           WHEN r_score >= 4                  THEN 'Potential Loyalist'
           WHEN r_score = 3                   THEN 'Need Attention'
           WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
           WHEN r_score = 1 AND f_score = 1   THEN 'Lost'
           ELSE 'Hibernating'
       END AS segment
FROM customers c
ORDER BY customer_id;
