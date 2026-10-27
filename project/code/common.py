"""Path dan konstanta bersama. Dipanggil dari semua skrip pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # folder project/

RAW_XLSX = ROOT / "data" / "raw" / "online_retail_II.xlsx"   # tidak di-commit
CLEAN_DIR = ROOT / "data" / "clean"                          # tidak di-commit
RAW_UNION = CLEAN_DIR / "raw_union.parquet"
DB_PATH = ROOT / "retail.duckdb"                             # tidak di-commit

SQL_DIR = ROOT / "code" / "1-data-preparation" / "sql"
SQL_ANALYSIS = ROOT / "code" / "2-analysis" / "sql"
RES_PREP = ROOT / "results" / "1-data-preparation"
RES_ANALYSIS = ROOT / "results" / "2-analysis"
RES_PRESENT = ROOT / "results" / "3-presentation"
DOCS_DIR = ROOT / "docs"

for d in (CLEAN_DIR, RES_PREP, RES_ANALYSIS, RES_PRESENT):
    d.mkdir(parents=True, exist_ok=True)

# Kode di StockCode yang bukan produk (ongkos kirim, biaya bank, penyesuaian, uji).
NON_PRODUCT_CODES = [
    "POST", "DOT", "M", "D", "S", "B", "m", "C2", "BANK CHARGES",
    "ADJUST", "AMAZONFEE", "PADS", "CRUK", "TEST001",
]

# Tanggal acuan recency = hari setelah transaksi terakhir di data (lihat docs/definitions.md).
SEED = 20260101
