"""05: analisis Q1–Q12, hipotesis H1–H5, dan KPI. Semua hasil ditulis ke results/2-analysis/*.csv."""
import sys
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy import stats
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "code"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RES_ANALYSIS, DB_PATH, RAW_UNION  # noqa: E402
from rfm_lib import load_clean, rfm_frame, segment_of, SEG_ORDER, ACTION  # noqa: E402

OUT = RES_ANALYSIS
LAST_FULL = pd.Timestamp("2011-11-01")  # bulan penuh terakhir
REF = "2011-12-10"


def wilson(k, n, z=1.96):
    if n == 0 or k is None or (isinstance(k, float) and math.isnan(k)):
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 4), round(c + h, 4))


clean = load_clean()
cust = rfm_frame(clean, REF)
cust["segment"] = [segment_of(r, f) for r, f in zip(cust.r_score, cust.f_score)]
cust.index.name = "customer_id"
assert len(clean) == 776583 and len(cust) == 5852

# ---------- retensi kohort (dari SQL, sudah dicek silang) ----------
ret = pd.read_csv(OUT / "cohort_retention.csv", parse_dates=["cohort_month"])
ret_piv = ret.pivot(index="cohort_month", columns="month_index", values="retention_rate")
size = ret.groupby("cohort_month").cohort_size.first()
act = ret.pivot(index="cohort_month", columns="month_index", values="active_customers")

# ---------- Q1 ----------
q1 = []
for c in ret_piv.index:
    row = {"cohort_month": c.strftime("%Y-%m"), "cohort_size": int(size[c])}
    for k in (1, 3, 6):
        r = ret_piv.loc[c, k]
        if pd.isna(r):
            row[f"ret_bulan_{k}"] = np.nan; row[f"ci_bawah_{k}"] = np.nan; row[f"ci_atas_{k}"] = np.nan
        else:
            a = int(act.loc[c, k]); lo, hi = wilson(a, int(size[c]))
            row[f"ret_bulan_{k}"] = round(r, 4); row[f"ci_bawah_{k}"] = lo; row[f"ci_atas_{k}"] = hi
    q1.append(row)
q1 = pd.DataFrame(q1)
q1.to_csv(OUT / "q1_retention_by_cohort.csv", index=False)

# ---------- Q2: peringkat kohort + pola kalender ----------
q2 = q1[["cohort_month", "cohort_size", "ret_bulan_1", "ret_bulan_3", "ret_bulan_6"]].copy()
q2["peringkat_bulan_1"] = q2.ret_bulan_1.rank(ascending=False, method="min")
q2["bulan_kalender"] = q2.cohort_month.str[5:7]
q2.to_csv(OUT / "q2_cohort_ranking.csv", index=False)

# ---------- Q3: nilai pembelian pertama (kuartil) vs retensi ----------
cust["fi_quartile"] = pd.qcut(cust.first_invoice_value.rank(method="first"), 4, labels=["Q1 terendah", "Q2", "Q3", "Q4 tertinggi"])
cs = cust.reset_index()
def active_in(month_offset):
    tgt = (cs.cohort_month + pd.DateOffset(months=month_offset)).values.astype("datetime64[M]")
    am = clean.assign(am=clean.invoice_date.values.astype("datetime64[M]")).groupby("customer_id").am.apply(set)
    return np.array([t in am.get(cid, set()) for cid, t in zip(cs.customer_id, tgt)])
rows = []
for k, last in ((1, pd.Timestamp("2011-10-01")), (3, pd.Timestamp("2011-08-01"))):
    elig = cs[cs.cohort_month <= last].copy()
    elig_idx = elig.index
    a_all = active_in(k)
    elig["active"] = a_all[elig_idx]
    for qname, g in elig.groupby("fi_quartile", observed=True):
        n = len(g); kk = int(g.active.sum()); lo, hi = wilson(kk, n)
        rows.append({"bulan": k, "kuartil_nilai_pertama": qname, "pelanggan_memenuhi": n,
                     "kembali": kk, "retensi": round(kk / n, 4), "ci_bawah": lo, "ci_atas": hi})
q3 = pd.DataFrame(rows)
q3.to_csv(OUT / "q3_first_value_quartile.csv", index=False)

# ---------- Q4 dan Q5: segmen ----------
tot_rev = cust.monetary.sum()
q45 = []
for s in SEG_ORDER:
    g = cust[cust.segment == s]
    q45.append({"segment": s, "pelanggan": len(g), "pct_pelanggan": round(100 * len(g) / len(cust), 2),
                "revenue": round(g.monetary.sum(), 2), "pct_revenue": round(100 * g.monetary.sum() / tot_rev, 2),
                "revenue_per_pelanggan": round(g.monetary.mean(), 2),
                "median_recency_hari": float(g.recency_days.median()), "aksi": ACTION[s]})
q45 = pd.DataFrame(q45)
q45.to_csv(OUT / "q4_q5_segments.csv", index=False)

# ---------- Q6: Inggris vs luar Inggris ----------
cust["grup_negara"] = np.where(cust.country == "United Kingdom", "Inggris", "Luar Inggris")
ct = pd.crosstab(cust.grup_negara, cust.segment).reindex(columns=SEG_ORDER, fill_value=0)
chi2, p, dof, _ = stats.chi2_contingency(ct.values)
p_text = "< 0.000001" if p < 1e-6 else round(p, 6)
q6 = (ct.div(ct.sum(axis=1), axis=0) * 100).round(2).reset_index()
q6.insert(1, "pelanggan", ct.sum(axis=1).values)
q6.to_csv(OUT / "q6_country_segments.csv", index=False)
q6_p = {"chi2": round(chi2, 3), "p_value": p_text, "dof": int(dof), "n_pelanggan": int(len(cust))}

# ---------- Q7: produk teratas per kelompok (dari DuckDB) ----------
con = duckdb.connect(str(DB_PATH), read_only=True)
seg_map = cust.reset_index()[["customer_id", "segment"]]
con.register("seg_map", seg_map)
prod = con.sql("""
    SELECT CASE WHEN s.segment IN ('Champions','Loyal') THEN 'Nilai tinggi (Champions, Loyal)'
                WHEN s.segment IN ('At Risk','Lost','Hibernating') THEN 'Berisiko (At Risk, Lost, Hibernating)'
                ELSE NULL END AS kelompok,
           t.description, SUM(t.line_revenue) AS revenue, SUM(t.quantity) AS qty,
           COUNT(DISTINCT t.customer_id) AS pelanggan
    FROM transactions_clean t JOIN seg_map s USING (customer_id)
    WHERE s.segment IN ('Champions','Loyal','At Risk','Lost','Hibernating')
    GROUP BY 1, 2
""").df()
prod = prod.sort_values(["kelompok", "revenue", "description"], ascending=[True, False, True])
prod["peringkat"] = prod.groupby("kelompok").cumcount() + 1
q7 = prod[prod.peringkat <= 5].copy()
q7["revenue"] = q7.revenue.round(2)
q7[["kelompok", "peringkat", "description", "revenue", "qty", "pelanggan"]].to_csv(OUT / "q7_top_products.csv", index=False)
con.close()

# ---------- Q8: jarak antar pembelian ----------
days = clean.groupby(["customer_id", "invoice_date"]).size().reset_index()[["customer_id", "invoice_date"]].drop_duplicates()
days = days.sort_values(["customer_id", "invoice_date"])
days["gap"] = days.groupby("customer_id").invoice_date.diff().dt.days
gap_c = days.groupby("customer_id").gap.mean().rename("rata_gap")
cust = cust.join(gap_c)
q8 = []
for s in SEG_ORDER:
    g = cust[(cust.segment == s) & cust.rata_gap.notna()]
    q8.append({"segment": s, "pelanggan_2plus_hari_beli": len(g),
               "median_jarak_hari": round(float(g.rata_gap.median()), 1) if len(g) else np.nan,
               "rata_jarak_hari": round(float(g.rata_gap.mean()), 1) if len(g) else np.nan})
pd.DataFrame(q8).to_csv(OUT / "q8_purchase_gap.csv", index=False)

# ---------- Q9: skenario uplift retensi bulan 1 ----------
am_all = clean.assign(am=clean.invoice_date.values.astype("datetime64[M]")).groupby(["customer_id", "am"]).size()
cust_month_total = len(am_all)
rev_per_cm = clean.line_revenue.sum() / cust_month_total
period_years = (pd.Timestamp("2011-11-30") - pd.Timestamp("2009-12-01")).days / 365.25
q9 = []
for d in (0.02, 0.05, 0.10):
    added = 0.0
    for c in ret_piv.index:
        r1 = ret_piv.loc[c, 1]
        if pd.isna(r1) or r1 == 0:
            continue
        for k in range(1, 24):
            rk = ret_piv.loc[c, k]
            if pd.isna(rk):
                continue
            new = rk * (r1 + d) / r1
            added += size[c] * (new - rk)
    rev = added * rev_per_cm
    q9.append({"kenaikan_retensi_bulan_1_poin": int(round(d * 100)), "tambahan_pelanggan_bulan_total": round(added, 1),
               "tambahan_revenue_periode_estimated": round(rev, 2),
               "tambahan_revenue_per_tahun_estimated": round(rev / period_years, 2),
               "revenue_per_pelanggan_aktif_bulan": round(rev_per_cm, 2), "label": "estimated"})
q9 = pd.DataFrame(q9)
q9.to_csv(OUT / "q9_uplift_scenarios.csv", index=False)

# ---------- Q12: stabilitas segmen ----------
c10 = load_clean(cutoff="2010-12-09")
cu10 = rfm_frame(c10, "2010-12-10")
cu10["segment"] = [segment_of(r, f) for r, f in zip(cu10.r_score, cu10.f_score)]
common = cu10.index.intersection(cust.index)
agree = (cu10.loc[common, "segment"] == cust.loc[common, "segment"]).mean()
ct12 = pd.crosstab(cu10.loc[common, "segment"], cust.loc[common, "segment"]).reindex(index=SEG_ORDER, columns=SEG_ORDER, fill_value=0)
q12 = ct12.reset_index().rename(columns={"segment": "segmen_2010_baris_2011_kolom"})
q12.to_csv(OUT / "q12_segment_stability.csv", index=False)
q12_summary = {"pelanggan_dibandingkan": len(common), "segmen_sama_pct": round(100 * agree, 2),
               "pelanggan_snapshot_2010": len(cu10)}

# ---------- H1–H5 ----------
hyp = []
s = cust.monetary.sort_values(ascending=False)
top20 = s.iloc[: int(round(0.2 * len(s)))].sum() / s.sum()
v1 = "Terbukti" if top20 >= 0.5 else ("Sebagian" if top20 >= 0.2 else "Tidak terbukti")
hyp.append({"hipotesis": "H1", "metrik": "porsi revenue dari 20% pelanggan teratas", "nilai": round(100 * top20, 2),
            "satuan": "%", "verdict": v1, "bukti": "ambang: >= 50% = Terbukti (asumsi)"})

drop01 = (ret_piv[0] - ret_piv[1]).mean()
later = np.mean([(ret_piv[k - 1] - ret_piv[k]).mean() for k in range(2, 7)])
v2 = "Terbukti" if drop01 > later and drop01 >= 2 * later else ("Sebagian" if drop01 > later else "Tidak terbukti")
hyp.append({"hipotesis": "H2", "metrik": "penurunan 0->1 dibanding rata-rata penurunan lanjutan (poin)",
            "nilai": round(100 * drop01, 2), "satuan": f"% (lanjutan {round(100*later,2)})", "verdict": v2,
            "bukti": "rata-rata antar kohort; lihat q1_retention_by_cohort.csv"})

dec = ret_piv.index[0]
cmp_rows = []
for k in (1, 3, 6):
    others = ret_piv.drop(dec)[k].dropna()
    cmp_rows.append(ret_piv.loc[dec, k] > others.mean())
v3 = "Terbukti" if all(cmp_rows) else ("Sebagian" if any(cmp_rows) else "Tidak terbukti")
hyp.append({"hipotesis": "H3", "metrik": "retensi Des 2009 bulan 1/3/6 vs rata-rata kohort lain (lebih tinggi?)",
            "nilai": f"{round(100*ret_piv.loc[dec,1],2)}/{round(100*ret_piv.loc[dec,3],2)}/{round(100*ret_piv.loc[dec,6],2)}",
            "satuan": "%", "verdict": v3, "bukti": f"lebih tinggi di {sum(cmp_rows)} dari 3 bulan (kohort {dec:%Y-%m}, n={int(size[dec])})"})

nonuk = cust[cust.grup_negara == "Luar Inggris"]; uk = cust[cust.grup_negara == "Inggris"]
freq_u, freq_n = uk.frequency.mean(), nonuk.frequency.mean()
val_u = clean[clean.country == "United Kingdom"].line_revenue.sum() / clean[clean.country == "United Kingdom"].invoice.nunique()
val_n = clean[clean.country != "United Kingdom"].line_revenue.sum() / clean[clean.country != "United Kingdom"].invoice.nunique()
u_p = stats.mannwhitneyu(nonuk.frequency, uk.frequency).pvalue
ok_freq = freq_n < freq_u; ok_val = val_n > val_u
v4 = "Terbukti" if ok_freq and ok_val else ("Sebagian" if (ok_freq or ok_val) else "Tidak terbukti")
hyp.append({"hipotesis": "H4", "metrik": "rata-rata invoice per pelanggan (luar vs Inggris)",
            "nilai": f"{round(freq_n,2)} vs {round(freq_u,2)}", "satuan": "invoice",
            "verdict": v4, "bukti": f"selisih frekuensi kecil; nilai per invoice luar {round(val_n,2)} vs Inggris {round(val_u,2)}; Mann-Whitney frekuensi p={round(u_p,4)}"})

raw_null = pd.read_parquet(RAW_UNION, columns=["Customer ID"])["Customer ID"].isna().mean() * 100
v5 = "Terbukti" if 20 <= raw_null <= 25 else "Tidak terbukti"
hyp.append({"hipotesis": "H5", "metrik": "persen baris tanpa Customer ID (raw)", "nilai": round(raw_null, 2),
            "satuan": "%", "verdict": v5, "bukti": "rentang 20-25% (rancangan)"})
hyp = pd.DataFrame(hyp)
hyp.to_csv(OUT / "hypotheses.csv", index=False)

# ---------- KPI ----------
ret_obs = ret[ret.retention_rate.notna()]
kpi = pd.DataFrame([
    {"kpi": "retention_rate_bulan_1_tertimbang", "nilai": round(ret_obs[ret_obs.month_index == 1].active_customers.sum() / ret_obs[ret_obs.month_index == 1].cohort_size.sum(), 4)},
    {"kpi": "repeat_purchase_rate", "nilai": round((cust.frequency >= 2).mean(), 4)},
    {"kpi": "revenue_per_pelanggan", "nilai": round(cust.monetary.mean(), 2)},
    {"kpi": "pelanggan_unik", "nilai": len(cust)},
    {"kpi": "total_revenue", "nilai": round(tot_rev, 2)},
])
kpi.to_csv(OUT / "kpi.csv", index=False)

pd.Series({**q6_p, **q12_summary, "rev_per_cm": round(rev_per_cm, 4), "period_years": round(period_years, 4),
           "raw_null_pct": round(raw_null, 2)}).to_csv(OUT / "analysis_meta.csv", header=["nilai"])
cust.reset_index()[["customer_id", "segment", "grup_negara", "fi_quartile", "rata_gap"]].to_csv(OUT / "customers_flags.csv", index=False)
print(q45.to_string(index=False)); print(q6.to_string(index=False)); print(hyp.to_string(index=False))
print(q9.to_string(index=False)); print(q12_summary); print(q6_p); print(kpi.to_string(index=False))
print(q3.to_string(index=False)); print(pd.DataFrame(q8).to_string(index=False)); print(q7.head(10).to_string(index=False))
