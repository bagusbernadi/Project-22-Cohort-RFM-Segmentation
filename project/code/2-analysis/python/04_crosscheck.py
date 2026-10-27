"""04: cek silang (Q11). Hitung ulang dengan pandas dari raw_union, bandingkan dengan hasil SQL."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code"))
from common import RAW_UNION, RES_ANALYSIS, NON_PRODUCT_CODES  # noqa: E402


def ntile(values: np.ndarray, k: int = 5) -> np.ndarray:
    """Meniru NTILE(k): baris diurutkan dulu; q+1 baris di awal, lalu q baris."""
    n = len(values)
    order = np.argsort(values, kind="stable")    # urut nilai, tie-breaker = urutan indeks (customer_id naik)
    q, r = divmod(n, k)
    tile_of_pos = np.empty(n, dtype=int)
    for i in range(n):
        tile_of_pos[i] = i // (q + 1) + 1 if i < r * (q + 1) else r + (i - r * (q + 1)) // q + 1
    out = np.empty(n, dtype=int)
    out[order] = tile_of_pos
    return out


raw = pd.read_parquet(RAW_UNION)
df = pd.DataFrame({
    "invoice": raw.Invoice, "stock_code": raw.StockCode, "description": raw.Description.astype("string"),
    "quantity": raw.Quantity.astype(int),
    "invoice_ts": raw.InvoiceDate, "price": raw.Price.astype(float),
    "customer_id": raw["Customer ID"], "country": raw.Country,
}).drop_duplicates(subset=["invoice", "stock_code", "description", "quantity", "invoice_ts", "price", "customer_id", "country"], keep="first")
is_ret = df.invoice.str.startswith("C")
keep = (~is_ret) & df.customer_id.notna() & (~df.stock_code.isin(NON_PRODUCT_CODES)) & (df.price > 0) & (df.quantity > 0)
clean = df[keep].copy()
clean["line_revenue"] = clean.quantity * clean.price
clean["invoice_date"] = clean.invoice_ts.dt.normalize()
assert len(clean) == 776583, len(clean)

# RFM pandas
ref = clean.invoice_date.max() + pd.Timedelta(days=1)
g = clean.groupby("customer_id")
cust = pd.DataFrame({
    "first_purchase": g.invoice_ts.min().dt.normalize(),
    "last_purchase": g.invoice_ts.max().dt.normalize(),
    "frequency": g.invoice.nunique(),
    "monetary": g.line_revenue.sum(),
})
cust["cohort_month"] = cust.first_purchase.values.astype("datetime64[M]")
cust["recency_days"] = (ref - cust.last_purchase).dt.days
cust = cust.sort_index()
ids = cust.index.to_numpy()
r_tile = ntile(cust.recency_days.to_numpy(), 5)
cust["r_score"] = 6 - r_tile
cust["f_score"] = ntile(cust.frequency.to_numpy(), 5)  # tie-breaker: index (customer_id) via lexsort order
cust["m_score"] = ntile(cust.monetary.to_numpy(), 5)

sql_c = pd.read_csv(RES_ANALYSIS / "customers_rfm.csv", parse_dates=["first_purchase", "last_purchase", "cohort_month"])
sql_c = sql_c.set_index("customer_id").sort_index()
rows = []
def add(name, n_cmp, n_match):
    rows.append({"cek": name, "dibandingkan": n_cmp, "cocok": n_match, "status": "PASS" if n_cmp == n_match else "FAIL"})

add("pelanggan_jumlah", len(sql_c), int(len(sql_c) == len(cust)) * len(sql_c))
add("pelanggan_id_sama", len(ids), int((sql_c.index.to_numpy() == ids).sum()))
for col in ["frequency", "recency_days", "r_score", "f_score", "m_score"]:
    add(f"{col}_per_pelanggan", len(ids), int((sql_c[col].to_numpy() == cust[col].to_numpy()).sum()))
add("monetary_per_pelanggan_selisih<0.01", len(ids), int((np.abs(sql_c.monetary.to_numpy() - cust.monetary.to_numpy()) < 0.01).sum()))
add("cohort_month_per_pelanggan", len(ids), int((sql_c.cohort_month.values == cust.cohort_month.values).sum()))

# Retensi kohort pandas
act = clean.assign(am=clean.invoice_date.values.astype("datetime64[M]")).groupby(["customer_id", "am"]).size().reset_index()
act = act.merge(cust[["cohort_month"]], left_on="customer_id", right_index=True)
act["k"] = ((act.am.dt.year - act.cohort_month.dt.year) * 12 + (act.am.dt.month - act.cohort_month.dt.month))
cnt = act.groupby(["cohort_month", "k"]).customer_id.nunique().rename("active").reset_index()
size = cust.groupby("cohort_month").size().rename("cohort_size").reset_index()
sql_r = pd.read_csv(RES_ANALYSIS / "cohort_retention.csv", parse_dates=["cohort_month"])
m = sql_r.merge(size, on="cohort_month", how="left", suffixes=("", "_p")).merge(
    cnt.rename(columns={"k": "month_index"}), on=["cohort_month", "month_index"], how="left")
m["active"] = m.active.fillna(0)
m_ok = m[m.retention_rate.notna()]
rate_pd = (m_ok.active / m_ok.cohort_size).round(6)
add("retensi_kohort_baris", len(sql_r), int(len(sql_r)))
add("retensi_kohort_jumlah_aktif_cocok", len(m), int((m.active_customers == m.active).sum()))
add("retensi_kohort_rate_selisih<1e-6", len(m_ok), int((np.abs(rate_pd - m_ok.retention_rate) < 1e-6).sum()))
add("cohort_size_cocok", len(m), int((m.cohort_size_p == m.cohort_size).sum()))

out = pd.DataFrame(rows)
out.to_csv(RES_ANALYSIS / "crosscheck.csv", index=False)
print(out.to_string(index=False))
assert (out.status == "PASS").all(), "cek silang gagal"
