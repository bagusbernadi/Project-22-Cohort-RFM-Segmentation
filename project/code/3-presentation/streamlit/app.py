"""Dashboard Project 22: Cohort & RFM Segmentation. Membaca CSV di results/3-presentation."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

RES = Path(__file__).resolve().parents[3] / "results" / "3-presentation"
st.set_page_config(page_title="Project 22: Cohort & RFM Segmentation", layout="wide")


@st.cache_data
def load():
    return (pd.read_csv(RES / "dashboard_retention.csv", parse_dates=["cohort_month"]),
            pd.read_csv(RES / "dashboard_customers.csv"),
            pd.read_csv(RES / "dashboard_segments.csv"),
            pd.read_csv(RES / "dashboard_kpi.csv"))


ret, cust, seg, kpi = load()
k = dict(zip(kpi.kpi, kpi.nilai))

page = st.sidebar.radio("Halaman", ["Ringkasan", "Retensi Kohort", "Segmen RFM"])
negara = st.sidebar.selectbox("Negara", ["Semua", "Inggris", "Luar Inggris"])
st.sidebar.caption("Data: Online Retail II (UCI), CC BY 4.0. Data 1 Des 2009 sampai 9 Des 2011.")

if page == "Ringkasan":
    st.title("Ringkasan")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pelanggan unik", f"{int(k['pelanggan_unik']):,}".replace(",", "."))
    c2.metric("Retensi bulan 1 (tertimbang)", f"{100*k['retention_rate_bulan_1_tertimbang']:.1f}%")
    c3.metric("Repeat purchase rate", f"{100*k['repeat_purchase_rate']:.1f}%")
    c4.metric("Revenue per pelanggan", f"£{k['revenue_per_pelanggan']:,.0f}")
    st.caption("Angka dari results/2-analysis/kpi.csv.")
    st.subheader("Segmen paling bernilai dan paling berisiko")
    st.dataframe(seg[["segment", "pelanggan", "pct_revenue", "revenue_per_pelanggan", "median_recency_hari", "aksi"]],
                 hide_index=True, width="stretch")
    st.caption("Pertanyaan utama: strategi apa untuk tiap segmen? Lihat halaman Segmen RFM.")

elif page == "Retensi Kohort":
    st.title("Retensi Kohort")
    r = ret.copy()
    piv = r.pivot(index="cohort", columns="month_index", values="retention_rate")
    fig = px.imshow(piv, color_continuous_scale="Blues", aspect="auto", zmin=0, zmax=1,
                    labels=dict(x="Bulan ke-", y="Kohort", color="Retensi"), text_auto=".0%")
    fig.update_layout(height=620)
    st.plotly_chart(fig, width="stretch")
    st.caption("Retensi = pelanggan aktif di bulan ke-k dibagi ukuran kohort. Kosong = bulan belum lengkap. Desember 2009 bisa berisi pelanggan lama.")

else:
    st.title("Segmen RFM")
    c = cust if negara == "Semua" else cust[cust.grup_negara == negara]
    st.caption(f"Pelanggan: {len(c):,} (filter negara: {negara})".replace(",", "."))
    agg = c.groupby("segment").agg(pelanggan=("customer_id", "count"), revenue=("monetary", "sum")).reset_index()
    agg["pct_revenue"] = 100 * agg.revenue / agg.revenue.sum()
    agg = agg.merge(seg[["segment", "aksi"]], on="segment", how="left")
    fig = px.bar(agg, x="segment", y="pct_revenue", color="aksi",
                 labels={"pct_revenue": "% revenue", "segment": "Segmen"},
                 category_orders={"segment": seg.segment.tolist()})
    st.plotly_chart(fig, width="stretch")
    st.dataframe(agg[["segment", "pelanggan", "revenue", "pct_revenue", "aksi"]].round(2),
                 hide_index=True, width="stretch")
    st.caption("Segmen menunjukkan perilaku, bukan penyebab berhenti belanja.")
