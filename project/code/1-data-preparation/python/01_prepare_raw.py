"""01: baca dua sheet xlsx, gabung, dan catat profil awal (Q10)."""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code"))
from common import RAW_XLSX, RAW_UNION, RES_PREP  # noqa: E402

SHEETS = ["Year 2009-2010", "Year 2010-2011"]
COLS = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate",
        "Price", "Customer ID", "Country"]

frames = []
for s in SHEETS:
    df = pd.read_excel(RAW_XLSX, sheet_name=s, dtype={"Invoice": str, "StockCode": str})
    df["source_sheet"] = s
    frames.append(df)
raw = pd.concat(frames, ignore_index=True)
raw["Description"] = raw["Description"].astype("string")  # sebagian deskripsi berupa angka di xlsx
assert list(raw.columns[:8]) == COLS, raw.columns
raw.to_parquet(RAW_UNION, index=False)

# Profil awal: jumlah baris per sheet, rentang tanggal, dan porsi kondisi khusus.
a, b = frames
ov_lo, ov_hi = b.InvoiceDate.min(), a.InvoiceDate.max()
prof = [
    ("baris_total", len(raw)),
    ("baris_sheet_2009_2010", len(a)),
    ("baris_sheet_2010_2011", len(b)),
    ("tanggal_min", raw.InvoiceDate.min().strftime("%Y-%m-%d %H:%M")),
    ("tanggal_max", raw.InvoiceDate.max().strftime("%Y-%m-%d %H:%M")),
    ("overlap_mulai", ov_lo.strftime("%Y-%m-%d %H:%M")),
    ("overlap_selesai", ov_hi.strftime("%Y-%m-%d %H:%M")),
    ("baris_di_periode_overlap_sheet_2009_2010", int((a.InvoiceDate >= ov_lo).sum())),
    ("baris_di_periode_overlap_sheet_2010_2011", int((b.InvoiceDate <= ov_hi).sum())),
    ("baris_duplikat_persis_total", int(raw[COLS].duplicated().sum())),
    ("customer_id_kosong", int(raw["Customer ID"].isna().sum())),
    ("customer_id_kosong_pct", round(100 * raw["Customer ID"].isna().mean(), 2)),
    ("invoice_berawalan_C", int(raw.Invoice.str.startswith("C").sum())),
    ("harga_nol_atau_negatif", int((raw.Price <= 0).sum())),
    ("qty_nol_atau_negatif_bukan_retur", int(((raw.Quantity <= 0) & ~raw.Invoice.str.startswith("C")).sum())),
    ("customer_unik_raw", int(raw["Customer ID"].nunique())),
    ("negara_unik", int(raw.Country.nunique())),
]
out = pd.DataFrame(prof, columns=["metrik", "nilai"])
out.to_csv(RES_PREP / "data_profile.csv", index=False)
print(out.to_string(index=False))
