"""Fungsi bersama analisis pandas: muat data bersih, NTILE, dan aturan segmen (mengikuti docs/definitions.md)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code"))
from common import RAW_UNION, NON_PRODUCT_CODES  # noqa: E402


def load_clean(cutoff=None):
    """Baris bersih (aturan sama dengan 01_clean.sql). cutoff: ambil data sampai tanggal ini (inklusif)."""
    raw = pd.read_parquet(RAW_UNION)
    df = pd.DataFrame({
        "invoice": raw.Invoice, "stock_code": raw.StockCode, "description": raw.Description.astype("string"),
        "quantity": raw.Quantity.astype(int), "invoice_ts": raw.InvoiceDate, "price": raw.Price.astype(float),
        "customer_id": raw["Customer ID"], "country": raw.Country,
    }).drop_duplicates(subset=["invoice", "stock_code", "description", "quantity", "invoice_ts",
                               "price", "customer_id", "country"], keep="first")
    keep = (~df.invoice.str.startswith("C")) & df.customer_id.notna() & (~df.stock_code.isin(NON_PRODUCT_CODES)) \
        & (df.price > 0) & (df.quantity > 0)
    clean = df[keep].copy()
    clean["line_revenue"] = clean.quantity * clean.price
    clean["invoice_date"] = clean.invoice_ts.dt.normalize()
    clean["customer_id"] = clean.customer_id.astype("int64")
    if cutoff is not None:
        clean = clean[clean.invoice_date <= pd.Timestamp(cutoff)]
    return clean.reset_index(drop=True)


def ntile(values, k=5):
    """Meniru NTILE(k) SQL. Urutan: nilai naik, tie-breaker = urutan posisi (input harus sudah urut customer_id)."""
    values = np.asarray(values)
    n = len(values)
    order = np.argsort(values, kind="stable")
    q, r = divmod(n, k)
    tile_of_pos = np.empty(n, dtype=int)
    for i in range(n):
        tile_of_pos[i] = i // (q + 1) + 1 if i < r * (q + 1) else r + (i - r * (q + 1)) // q + 1
    out = np.empty(n, dtype=int)
    out[order] = tile_of_pos
    return out


def rfm_frame(clean, ref_date):
    g = clean.groupby("customer_id")
    cust = pd.DataFrame({
        "first_purchase": g.invoice_ts.min().dt.normalize(),
        "last_purchase": g.invoice_ts.max().dt.normalize(),
        "frequency": g.invoice.nunique(),
        "monetary": g.line_revenue.sum(),
        "first_invoice_value": None,
        "country": g.country.first(),
    }).sort_index()
    first_ts = clean.groupby("customer_id").invoice_ts.transform("min")
    fi = clean[clean.invoice_ts == first_ts].groupby("customer_id").line_revenue.sum()
    cust["first_invoice_value"] = fi.reindex(cust.index).astype(float)
    cust["cohort_month"] = cust.first_purchase.values.astype("datetime64[M]")
    cust["recency_days"] = (pd.Timestamp(ref_date) - cust.last_purchase).dt.days
    cust["r_score"] = 6 - ntile(cust.recency_days.to_numpy(), 5)
    cust["f_score"] = ntile(cust.frequency.to_numpy(), 5)
    cust["m_score"] = ntile(cust.monetary.to_numpy(), 5)
    return cust


def segment_of(r, f):
    if r >= 4 and f >= 4: return "Champions"
    if r >= 3 and f >= 3: return "Loyal"
    if r == 5 and f == 1: return "New"
    if r >= 4: return "Potential Loyalist"
    if r == 3: return "Need Attention"
    if r <= 2 and f >= 3: return "At Risk"
    if r == 1 and f == 1: return "Lost"
    return "Hibernating"


SEG_ORDER = ["Champions", "Loyal", "Potential Loyalist", "New", "Need Attention", "At Risk", "Lost", "Hibernating"]
ACTION = {"Champions": "pertahankan", "Loyal": "pertahankan", "Potential Loyalist": "pertahankan", "New": "pertahankan",
          "Need Attention": "aktifkan kembali", "At Risk": "aktifkan kembali",
          "Hibernating": "biarkan", "Lost": "biarkan"}
