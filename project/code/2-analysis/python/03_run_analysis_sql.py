"""03: jalankan SQL analisis (pelanggan, kohort, segmen RFM) dan tulis CSV hasil."""
import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code"))
from common import DB_PATH, SQL_ANALYSIS, RES_ANALYSIS  # noqa: E402

con = duckdb.connect(str(DB_PATH))
for f in ["03_customers.sql", "04_cohort.sql", "05_rfm_segments.sql"]:
    con.execute((SQL_ANALYSIS / f).read_text(encoding="utf-8"))
    print("ok", f)

con.execute(f"COPY (SELECT * FROM cohort_retention ORDER BY cohort_month, month_index) "
            f"TO '{(RES_ANALYSIS / 'cohort_retention.csv').as_posix()}' (HEADER, DELIMITER ',')")
con.execute(f"COPY (SELECT customer_id, first_purchase, cohort_month, last_purchase, recency_days, "
            f"frequency, ROUND(monetary, 4) AS monetary, first_invoice_value, country, "
            f"r_score, f_score, m_score, segment FROM customers_seg ORDER BY customer_id) "
            f"TO '{(RES_ANALYSIS / 'customers_rfm.csv').as_posix()}' (HEADER, DELIMITER ',')")
con.execute(f"COPY (SELECT * FROM dim_segment ORDER BY urut) "
            f"TO '{(RES_ANALYSIS / 'dim_segment.csv').as_posix()}' (HEADER, DELIMITER ',')")
con.close()
print("csv tertulis")
