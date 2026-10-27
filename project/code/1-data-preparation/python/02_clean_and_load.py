"""02: muat raw_union ke DuckDB, jalankan 01_clean.sql, dan tulis log cleaning."""
import sys
from pathlib import Path
import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code"))
from common import RAW_UNION, DB_PATH, SQL_DIR, RES_PREP  # noqa: E402

if DB_PATH.exists():
    DB_PATH.unlink()
con = duckdb.connect(str(DB_PATH))
con.execute(f"CREATE TABLE raw_union AS SELECT * FROM read_parquet('{RAW_UNION.as_posix()}')")
con.execute((SQL_DIR / "01_clean.sql").read_text(encoding="utf-8"))

reason = con.execute(
    "SELECT alasan, jumlah_baris FROM cleaning_reason ORDER BY jumlah_baris DESC, alasan ASC"
).df()
total = int(reason.jumlah_baris.sum())
raw_n = con.execute("SELECT COUNT(*) FROM raw_union").fetchone()[0]
dup_n = raw_n - total
assert int(reason.loc[reason.alasan == "dipakai", "jumlah_baris"].iloc[0]) == con.execute("SELECT COUNT(*) FROM transactions_clean").fetchone()[0]
reason["pct_dari_total_raw"] = (100 * reason.jumlah_baris / raw_n).round(2)
dup_row = {"alasan": "duplikat_persis_dihapus", "jumlah_baris": dup_n, "pct_dari_total_raw": round(100 * dup_n / raw_n, 2)}
log = pd.concat([pd.DataFrame([dup_row]), reason], ignore_index=True)
order = ["duplikat_persis_dihapus", "customer_id_kosong", "retur_atau_batal", "kode_bukan_produk",
         "harga_nol_atau_negatif", "qty_nol_atau_negatif", "dipakai"]
log["urut"] = log.alasan.map({k: i for i, k in enumerate(order)})
log = log.sort_values(["urut", "alasan"]).drop(columns="urut")
log.to_csv(RES_PREP / "cleaning_log.csv", index=False)
print(log.to_string(index=False))
print("raw", raw_n, "dedup", raw_n - dup_n, "dipakai", int(reason.loc[reason.alasan == "dipakai", "jumlah_baris"].iloc[0]))
con.close()
