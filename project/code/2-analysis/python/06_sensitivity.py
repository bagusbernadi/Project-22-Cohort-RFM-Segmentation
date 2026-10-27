"""06: uji sensitivitas definisi yang ditetapkan sendiri (lihat docs/definitions.md)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RES_ANALYSIS  # noqa: E402
from rfm_lib import load_clean, rfm_frame, segment_of, SEG_ORDER  # noqa: E402

rows = []
clean = load_clean()
clean["am"] = clean.invoice_date.values.astype("datetime64[M]")


def retention(min_inv):
    """Retensi tertimbang bulan 1, 3, 6 (kohort yang bulan itu sudah penuh). min_inv = invoice minimum per bulan."""
    cust = rfm_frame(clean, "2011-12-10")
    per = clean.groupby(["customer_id", "am"]).invoice.nunique().reset_index()
    per = per[per.invoice >= min_inv]
    per = per.merge(cust[["cohort_month"]], left_on="customer_id", right_index=True)
    per["k"] = (per.am.dt.year - per.cohort_month.dt.year) * 12 + (per.am.dt.month - per.cohort_month.dt.month)
    out = {}
    for k in (1, 3, 6):
        last = pd.Timestamp("2011-11-01") - pd.DateOffset(months=k)
        sz = cust[cust.cohort_month <= last].groupby("cohort_month").size()
        ac = per[(per.k == k) & (per.cohort_month <= last)].groupby("cohort_month").customer_id.nunique()
        out[k] = float((ac.reindex(sz.index).fillna(0) / sz).mean())
    return out


base = retention(1)
alt = retention(2)
for k in (1, 3, 6):
    rows.append({"definisi": "aktif", "varian": f"aktif = >=2 invoice per bulan (bulan {k}, rata-rata antar kohort)",
                 "baseline": round(base[k], 4), "alternatif": round(alt[k], 4),
                 "selisih_poin": round(100 * (alt[k] - base[k]), 2)})

# Tanggal acuan recency: +1 hari (baseline) vs +31 hari
cust0 = rfm_frame(clean, "2011-12-10")
cust1 = rfm_frame(clean, "2012-01-09")
for name, c in (("baseline (+1 hari)", cust0), ("alternatif (+31 hari)", cust1)):
    c["segment"] = [segment_of(r, f) for r, f in zip(c.r_score, c.f_score)]
share = lambda c, s: 100 * (c.segment == s).mean()
for s in ("Champions", "At Risk"):
    rows.append({"definisi": "tanggal acuan recency", "varian": f"pelanggan segmen {s} (%)",
                 "baseline": round(share(cust0, s), 2), "alternatif": round(share(cust1, s), 2),
                 "selisih_poin": round(share(cust1, s) - share(cust0, s), 2)})

# Cohort Desember 2009 dikeluarkan (pelanggan lama sebelum periode data)
c_no = clean[clean.invoice_date >= pd.Timestamp("2010-01-01")]
cn = rfm_frame(c_no, "2011-12-10")
top_base = clean.groupby("customer_id").line_revenue.sum().sort_values(ascending=False)
top_base_share = top_base.iloc[: int(round(0.2 * len(top_base)))].sum() / top_base.sum()
top_alt = c_no.groupby("customer_id").line_revenue.sum().sort_values(ascending=False)
top_alt_share = top_alt.iloc[: int(round(0.2 * len(top_alt)))].sum() / top_alt.sum()
rows.append({"definisi": "H1 porsi revenue 20% teratas", "varian": "tanpa data Des 2009 (dimulai 1 Jan 2010)",
             "baseline": round(100 * top_base_share, 2), "alternatif": round(100 * top_alt_share, 2),
             "selisih_poin": round(100 * (top_alt_share - top_base_share), 2)})

# Nilai revenue per pelanggan aktif bulan: baseline data vs ilustrasi rancangan (GBP 250)
meta = pd.read_csv(RES_ANALYSIS / "analysis_meta.csv", index_col=0).nilai
period_years = float(meta["period_years"])
q9 = pd.read_csv(RES_ANALYSIS / "q9_uplift_scenarios.csv")
for _, r in q9.iterrows():
    alt_per_year = r.tambahan_pelanggan_bulan_total * 250 / period_years   # GBP 250 per pelanggan aktif per bulan (ilustrasi rancangan)
    rows.append({"definisi": "Q9 uplift: revenue per pelanggan aktif per bulan",
                 "varian": f"+{int(r.kenaikan_retensi_bulan_1_poin)} poin: data (GBP {round(r.revenue_per_pelanggan_aktif_bulan,0):.0f}) vs ilustrasi rancangan (GBP 250)",
                 "baseline": round(r.tambahan_revenue_per_tahun_estimated, 2),
                 "alternatif": round(alt_per_year, 2),
                 "selisih_poin": np.nan})

out = pd.DataFrame(rows)
out.to_csv(RES_ANALYSIS / "sensitivity.csv", index=False)
print(out.to_string(index=False))
