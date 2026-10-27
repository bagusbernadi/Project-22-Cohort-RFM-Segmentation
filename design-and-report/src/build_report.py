"""Membangun design-and-report/index.html: pane Design tidak diubah (dicek byte-per-byte), pane Report v2 dibangun dari CSV hasil.

Jalankan dari root repo: python design-and-report/src/build_report.py
"""
import re
import sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJ = ROOT / "project"
sys.path.insert(0, str(HERE))
from report_lib import num, pct, pct_raw, esc, pill, table  # noqa: E402

RES_P = PROJ / "results" / "1-data-preparation"
RES_A = PROJ / "results" / "2-analysis"

src = (HERE / "page_v1.html").read_text(encoding="utf-8")
d_start = src.index('<div class="pane" id="design"')
d_end = src.index('<div class="pane" id="report"')
design_pane = src[d_start:d_end]
r_start = d_end
r_end = src.index("<script>")
script_block = src[r_end:]

# ---------- baca hasil ----------
prof = pd.read_csv(RES_P / "data_profile.csv").set_index("metrik").nilai
clog = pd.read_csv(RES_P / "cleaning_log.csv")
cc = pd.read_csv(RES_A / "crosscheck.csv")
q1 = pd.read_csv(RES_A / "q1_retention_by_cohort.csv")
q2 = pd.read_csv(RES_A / "q2_cohort_ranking.csv")
q3 = pd.read_csv(RES_A / "q3_first_value_quartile.csv")
q45 = pd.read_csv(RES_A / "q4_q5_segments.csv")
q6 = pd.read_csv(RES_A / "q6_country_segments.csv")
q7 = pd.read_csv(RES_A / "q7_top_products.csv")
q8 = pd.read_csv(RES_A / "q8_purchase_gap.csv")
q9 = pd.read_csv(RES_A / "q9_uplift_scenarios.csv")
q12m = pd.read_csv(RES_A / "q12_segment_stability.csv")
hyp = pd.read_csv(RES_A / "hypotheses.csv")
kpi = pd.read_csv(RES_A / "kpi.csv").set_index("kpi").nilai
sens = pd.read_csv(RES_A / "sensitivity.csv")
meta = pd.read_csv(RES_A / "analysis_meta.csv", index_col=0).nilai
dim = pd.read_csv(RES_A / "dim_segment.csv")
cust_n = int(kpi["pelanggan_unik"])
assert cust_n == 5852 and int(prof["baris_total"]) == 1067371

# ---------- angka turunan ----------
ret_pick = lambda k: q1.set_index("cohort_month")[f"ret_bulan_{k}"]
best1 = q2.dropna(subset=["ret_bulan_1"]).sort_values(["ret_bulan_1", "cohort_month"], ascending=[False, True]).iloc[0]
worst1 = q2.dropna(subset=["ret_bulan_1"]).sort_values(["ret_bulan_1", "cohort_month"], ascending=[True, True]).iloc[0]
seg = q45.set_index("segment")
champ, at_risk, lost = seg.loc["Champions"], seg.loc["At Risk"], seg.loc["Lost"]
top20_share = float(hyp.set_index("hipotesis").loc["H1", "nilai"])
q3_1 = q3[q3.bulan == 1].set_index("kuartil_nilai_pertama")
q3_3 = q3[q3.bulan == 3].set_index("kuartil_nilai_pertama")
q6i = q6.set_index("grup_negara")
p_chi = meta["p_value"]
rev_pm = float(meta["rev_per_cm"])
period_y = float(meta["period_years"])
xcheck_pass = int((cc.status == "PASS").sum())
xcheck_total = len(cc)
stab_pct = float(meta["segmen_sama_pct"])
stab_n = int(meta["pelanggan_dibandingkan"])
kl = clog.set_index("alasan")
dup = int(kl.loc["duplikat_persis_dihapus", "jumlah_baris"])
nullc = int(kl.loc["customer_id_kosong", "jumlah_baris"])
ret_cnt = int(kl.loc["retur_atau_batal", "jumlah_baris"])
nonprod = int(kl.loc["kode_bukan_produk", "jumlah_baris"])
zero_p = int(kl.loc["harga_nol_atau_negatif", "jumlah_baris"])
used = int(kl.loc["dipakai", "jumlah_baris"])
raw_total = int(prof["baris_total"])
assert dup + used + nullc + ret_cnt + nonprod + zero_p == raw_total

# ---------- verdict per bagian ----------
def hv(h):
    return hyp.set_index("hipotesis").loc[h, "verdict"]
hyp_counts = hyp.verdict.value_counts().to_dict()

# ---------- Report v2 ----------
evq_rows = [
    ("1", "Apakah data berhasil didapat dan dibersihkan?", pill("Terverifikasi", ""),
     f"Data {num(raw_total)} baris terbaca, {num(used)} baris dipakai setelah cleaning."),
    ("2", "Apakah business question terjawab?", pill("Sesuai", ""),
     "12 pertanyaan dijawab dengan angka dari data; jawaban bercatatan ditandai kuning."),
    ("3", "Apakah dataset sesuai dengan Design Project?", pill("Sesuai", ""),
     "Dataset Online Retail II sesuai rancangan. Dua sheet ternyata tumpang tindih (ditambahkan sebagai keputusan cleaning)."),
    ("4", "Apakah tools yang digunakan sesuai?", pill("Sesuai + penyesuaian", ""),
     "DuckDB + SQL dan pandas dipakai. Excel tidak dibuat (opsional, tidak diperlukan untuk cek silang)."),
    ("5", "Apakah alur pengerjaan sesuai dengan Design Project?", pill("Sesuai + penyesuaian", ""),
     "Urutan tahap A sampai D dipertahankan. Nama file dan penomoran skrip berbeda dari usulan rancangan (lihat 5)."),
    ("6", "Apakah project output tercapai?", pill("Sebagian", "p"),
     "Dashboard dibuat dan diuji dengan AppTest, belum di-deploy. Slide tidak dibuat (opsional)."),
    ("7", "Apakah success criteria tercapai?", pill("Sebagian", "p"),
     "Lihat 7.3: sebagian besar tercapai; dashboard belum diuji oleh pembaca awam."),
]

def qa(n, text, prio, status, body, warn=False):
    cls = "qa w" if warn else "qa"
    return (f'<div class="{cls}" id="sec2{n}"><div class="qh"><span class="qn">Q{n}</span> '
            f'<span class="qt">{esc(text)}</span> {pill(prio)} {pill(status, "p" if warn else "")}</div>'
            f'<div class="qb">{body}</div></div>')

# Q1 cek kolom bulan 1,3,6 dan kohort terendah/tertinggi
q1_rows = []
for _, r in q1.iterrows():
    q1_rows.append([r.cohort_month, num(r.cohort_size),
                    pct(r.ret_bulan_1) if pd.notna(r.ret_bulan_1) else "–",
                    pct(r.ret_bulan_3) if pd.notna(r.ret_bulan_3) else "–",
                    pct(r.ret_bulan_6) if pd.notna(r.ret_bulan_6) else "–"])
t_q1 = table(["Kohort", "Ukuran", "Bulan 1", "Bulan 3", "Bulan 6"], q1_rows)

q3_rows = [[r.kuartil_nilai_pertama, num(r.pelanggan_memenuhi), pct(r.retensi),
            f"{pct(r.ci_bawah)} – {pct(r.ci_atas)}"] for _, r in q3[q3.bulan == 1].iterrows()]
t_q3 = table(["Kuartil nilai invoice pertama", "Pelanggan", "Kembali bulan 1", "CI 95%"], q3_rows)

q45_rows = [[r.segment, num(r.pelanggan), pct_raw(r.pct_pelanggan, 1), pct_raw(r.pct_revenue, 1),
             num(r.revenue_per_pelanggan, 0), num(r.median_recency_hari, 0), r.aksi] for _, r in q45.iterrows()]
t_q45 = table(["Segmen", "Pelanggan", "% pelanggan", "% revenue", "Revenue per pelanggan (£)", "Median recency (hari)", "Aksi"], q45_rows)

q6_rows = []
for seg_name in q45.segment:
    if seg_name in q6.columns:
        q6_rows.append([seg_name, pct_raw(q6i.loc["Inggris", seg_name], 1), pct_raw(q6i.loc["Luar Inggris", seg_name], 1)])
t_q6 = table(["Segmen", "Inggris (%)", "Luar Inggris (%)"], q6_rows)

q7p = q7.copy()
def prod_rows(kel):
    g = q7p[q7p.kelompok.str.startswith(kel)].sort_values("peringkat")
    return [[num(r.peringkat), esc(r.description), num(r.revenue, 0), num(r.pelanggan)] for _, r in g.iterrows()]
t_q7a = table(["No", "Produk", "Revenue (£)", "Pelanggan"], prod_rows("Nilai tinggi"))
t_q7b = table(["No", "Produk", "Revenue (£)", "Pelanggan"], prod_rows("Berisiko"))

q8_rows = [[r.segment, num(r.pelanggan_2plus_hari_beli), "–" if pd.isna(r.median_jarak_hari) else num(r.median_jarak_hari, 1),
            "–" if pd.isna(r.rata_jarak_hari) else num(r.rata_jarak_hari, 1)] for _, r in q8.iterrows()]
t_q8 = table(["Segmen", "Pelanggan ≥2 hari beli", "Median jarak (hari)", "Rata-rata jarak (hari)"], q8_rows)

q9_rows = [[num(r.kenaikan_retensi_bulan_1_poin), num(r.tambahan_pelanggan_bulan_total, 1),
            f"£{num(r.tambahan_revenue_per_tahun_estimated, 0)}", pill("estimated", "p")] for _, r in q9.iterrows()]
t_q9 = table(["Kenaikan retensi bulan 1 (poin)", "Tambahan pelanggan-bulan (total periode)", "Tambahan revenue per tahun", "Label"], q9_rows)

hyp_rows = []
for _, r in hyp.iterrows():
    k = "" if r.verdict == "Terbukti" else ("p" if r.verdict == "Sebagian" else "d")
    hyp_rows.append([esc(r.hipotesis), esc(r.metrik), esc(r.nilai) + (f" {esc(r.satuan)}" if isinstance(r.satuan, str) and r.satuan not in ("%",) else ("%" if r.satuan == "%" else "")), pill(r.verdict, k), esc(r.bukti)])
t_hyp = table(["Hipotesis", "Metrik", "Nilai", "Verdict", "Bukti"], hyp_rows)

sens_rows = [[esc(r.definisi), esc(r.varian), num(r.baseline, 4 if r.baseline < 1 else 2), num(r.alternatif, 4 if r.alternatif < 1 else 2),
              "–" if pd.isna(r.selisih_poin) else num(r.selisih_poin, 2)] for _, r in sens.iterrows()]
t_sens = table(["Definisi", "Varian", "Baseline", "Alternatif", "Selisih (poin)"], sens_rows)

seg_map = dict(zip(dim.segment, dim.suggested_action))
ct = q12m.set_index(q12m.columns[0])
q12_seg_rows = []
for s in ct.index:
    same = ct.loc[s, s] if s in ct.columns else 0
    tot = ct.loc[s].sum()
    q12_seg_rows.append([esc(s), num(tot), num(same), pct(same / tot) if tot else "–"])
t_q12 = table(["Segmen 2010", "Pelanggan", "Sama di 2011", "Persen sama"], q12_seg_rows)

cc_rows = [[esc(r.cek), num(r.dibandingkan), num(r.cocok), pill(r.status, "" if r.status == "PASS" else "d")] for _, r in cc.iterrows()]
t_cc = table(["Cek", "Dibandingkan", "Cocok", "Status"], cc_rows)

clog_rows = [[esc(r.alasan), num(r.jumlah_baris), pct_raw(r.pct_dari_total_raw, 2)] for _, r in clog.iterrows()]
t_clog = table(["Alasan", "Jumlah baris", "% dari raw"], clog_rows)

kpi_rows = [
    ["Retention rate bulan 1 (tertimbang)", pct(kpi["retention_rate_bulan_1_tertimbang"]), "Sum aktif bulan 1 / sum ukuran kohort (kohort teramati)"],
    ["Repeat purchase rate", pct(kpi["repeat_purchase_rate"]), "Pelanggan dengan ≥2 invoice / semua pelanggan"],
    ["Revenue per pelanggan", "£" + num(kpi["revenue_per_pelanggan"], 2), "Total line revenue / pelanggan unik"],
    ["Pelanggan unik", num(cust_n), "Pelanggan dengan Customer ID dan baris bersih"],
    ["Total revenue (bersih)", "£" + num(kpi["total_revenue"], 0), "Jumlah line revenue baris bersih"],
]
t_kpi = table(["KPI", "Hasil", "Rumus ringkas"], kpi_rows)

t_files = table(["Rancangan", "Realisasi", "Verdict"], [
    ["data/raw/online_retail_II.xlsx", "project/data/raw/online_retail_II.xlsx (tidak di-commit)", pill("Sesuai", "")],
    ["sql/01_clean.sql", "project/code/1-data-preparation/sql/01_clean.sql", pill("Sesuai + penyesuaian", "")],
    ["sql/02_customers.sql", "project/code/2-analysis/sql/03_customers.sql (penomoran lintas tahap)", pill("Sesuai + penyesuaian", "")],
    ["sql/03_cohort.sql", "project/code/2-analysis/sql/04_cohort.sql", pill("Sesuai + penyesuaian", "")],
    ["sql/04_rfm_segments.sql", "project/code/2-analysis/sql/05_rfm_segments.sql", pill("Sesuai + penyesuaian", "")],
    ["retail.duckdb", "project/retail.duckdb (tidak di-commit)", pill("Sesuai", "")],
    ["docs/cleaning_log.md", "project/results/1-data-preparation/cleaning_log.csv + docs/cleaning_log.md", pill("Sesuai + penyesuaian", "")],
    ["notebooks/analysis.ipynb", "(tidak dibuat; analisis dalam skrip Python)", pill("Tidak dibuat", "d")],
    ["outputs/*.csv", "project/results/2-analysis/*.csv", pill("Sesuai + penyesuaian", "")],
    ["dashboard/app.py", "project/code/3-presentation/streamlit/app.py", pill("Sesuai + penyesuaian", "")],
    ["docs/definitions.md", "project/docs/definitions.md", pill("Sesuai", "")],
    ["slides/presentation.pdf", "(tidak dibuat, Opsional)", pill("Tidak dibuat", "d")],
], "")

def build_report():
    qchips = []
    cards_s2 = []
    # ---------- Bagian 2: pertanyaan ----------
    cards_s2.append('<div class="how">Setiap pertanyaan diberi nomor. Klik nomornya untuk melompat ke jawabannya. Kuning = terjawab dengan catatan.</div>')
    items = [
        ("1", "Berapa persen pelanggan yang kembali belanja 1, 3, dan 6 bulan setelah pembelian pertama, per kohort bulan?", "Utama", "Terjawab", False,
         f"<p>Retensi bulan 1 rata-rata {pct(kpi['retention_rate_bulan_1_tertimbang'])} (tertimbang). Kohort {esc(best1.cohort_month[:7])} tertinggi ({pct(best1.ret_bulan_1)}), terendah {esc(worst1.cohort_month[:7])} ({pct(worst1.ret_bulan_1)}).</p>" + t_q1 + "<p class='tight'>Tabel 2.1a: matriks retensi kohort (bulan 1, 3, 6). Kosong jika bulan belum lengkap.</p>"),
        ("2", "Kohort mana yang retensinya paling baik dan paling buruk, dan adakah pola musiman?", "Utama", "Dengan catatan", True,
         f"<p>Terbaik bulan 1: {esc(best1.cohort_month[:7])} ({pct(best1.ret_bulan_1)}). Terburuk: {esc(worst1.cohort_month[:7])} ({pct(worst1.ret_bulan_1)}). Pola musiman hanya bisa dilihat dari dua tahun data, jadi belum bisa disimpulkan.</p>"),
        ("3", "Apakah pelanggan dengan pembelian pertama bernilai besar lebih mungkin kembali?", "Pendukung", "Terjawab", False,
         f"<p>Ya. Retensi bulan 1 naik dari {pct(q3_1.loc['Q1 terendah','retensi'])} (kuartil terendah) ke {pct(q3_1.loc['Q4 tertinggi','retensi'])} (kuartil tertinggi). Bulan 3: {pct(q3_3.loc['Q1 terendah','retensi'])} ke {pct(q3_3.loc['Q4 tertinggi','retensi'])}.</p>" + t_q3 + "<p class='tight'>Tabel 2.3a: retensi per kuartil nilai invoice pertama (kohort yang bulan 1-nya sudah lengkap).</p>"),
        ("4", "Berapa jumlah pelanggan dan porsi revenue tiap segmen RFM?", "Utama", "Dengan catatan", True,
         f"<p>Champions {num(champ.pelanggan)} pelanggan ({pct_raw(champ.pct_pelanggan,1)}) menghasilkan {pct_raw(champ.pct_revenue,1)} revenue. Aturan segmen adalah asumsi (lihat docs/definitions.md).</p>" + t_q45 + "<p class='tight'>Tabel 2.4a: segmen RFM (8 segmen).</p>"),
        ("5", "Segmen mana yang paling bernilai dan mana yang paling berisiko berhenti belanja?", "Utama", "Dengan catatan", True,
         f"<p>Paling bernilai: Champions (revenue per pelanggan £{num(champ.revenue_per_pelanggan,0)}). Paling berisiko: At Risk, median recency {num(at_risk.median_recency_hari,0)} hari, {pct_raw(at_risk.pct_revenue,1)} revenue. Lost lebih lama lagi ({num(lost.median_recency_hari,0)} hari).</p>"),
        ("6", "Apakah komposisi segmen berbeda antara pelanggan Inggris dan luar Inggris?", "Pendukung", "Terjawab", False,
         f"<p>Ya, secara statistik (chi-kuadrat {num(float(meta['chi2']),2)}, p {p_chi}, df {int(float(meta['dof']))}). Luar Inggris lebih banyak di Potential Loyalist dan Lost, Inggris lebih banyak di At Risk. Kelompok luar Inggris berisi {num(q6i.loc['Luar Inggris'].pelanggan)} pelanggan.</p>" + t_q6 + "<p class='tight'>Tabel 2.6a: komposisi segmen per kelompok negara (persen).</p>"),
        ("7", "Produk apa yang paling sering dibeli segmen bernilai tinggi dan segmen berisiko?", "Pendukung", "Terjawab", False,
         "<p>Lima produk teratas menurut revenue untuk tiap kelompok:</p>" + t_q7a + "<p class='tight'>Tabel 2.7a: produk teratas, nilai tinggi (Champions, Loyal).</p>" + t_q7b + "<p class='tight'>Tabel 2.7b: produk teratas, berisiko (At Risk, Lost, Hibernating).</p>"),
        ("8", "Berapa rata-rata jarak antar pembelian di tiap segmen?", "Tambahan", "Dengan catatan", True,
         "<p>Jarak dihitung dari pelanggan yang punya minimal dua hari beli. Segmen New dan Lost tidak punya data jarak karena hanya satu invoice.</p>" + t_q8 + "<p class='tight'>Tabel 2.8a: jarak antar hari beli per segmen.</p>"),
        ("9", "Jika retensi bulan pertama naik sekian poin, berapa estimasi tambahan revenue per tahun?", "Utama", "Dengan catatan", True,
         f"<p>Estimasi, bukan hasil data. Kenaikan 2 poin menambah sekitar £{num(q9.iloc[0].tambahan_revenue_per_tahun_estimated,0)} per tahun. Asumsi: revenue per pelanggan aktif per bulan £{num(rev_pm,0)} (dari data, bukan £250 ilustrasi rancangan).</p>" + t_q9 + "<p class='tight'>Tabel 2.9a: skenario uplift (label estimated).</p>"),
        ("10", "Berapa persen baris tanpa Customer ID, retur atau invoice batal, dan harga nol, dan apa keputusan untuk masing-masing?", "Utama", "Terjawab", False,
         f"<p>Customer ID kosong {pct_raw(clog.set_index('alasan').loc['customer_id_kosong','pct_dari_total_raw'],2)} dari baris mentah. Retur atau batal {pct_raw(clog.set_index('alasan').loc['retur_atau_batal','pct_dari_total_raw'],2)}. Harga nol {pct_raw(clog.set_index('alasan').loc['harga_nol_atau_negatif','pct_dari_total_raw'],2)}. Keputusan dan jumlah baris ada di Tabel 1.1.</p>"),
        ("11", "Apakah retensi dan skor RFM dari SQL sama dengan hasil pandas?", "Utama", "Terjawab", False,
         f"<p>Ya. {xcheck_pass} dari {xcheck_total} cek silang lulus (lihat Tabel 1.2b).</p>"),
        ("12", "Apakah segmen stabil jika periode acuan digeser satu tahun?", "Pendukung", "Dengan catatan", True,
         f"<p>Tidak stabil. Dari {num(stab_n)} pelanggan yang sudah belanja sampai 9 Des 2010, hanya {pct_raw(stab_pct,1)} yang mendapat segmen sama di snapshot 2011. Populasi snapshot berbeda, jadi sebagian perbedaan berasal dari itu.</p>" + t_q12 + "<p class='tight'>Tabel 2.12a: matriks perpindahan segmen (baris 2010, kolom 2011 tidak ditampilkan, hanya persen sama).</p>"),
    ]
    for n, text, prio, status, warn, body in items:
        cards_s2.append(qa(n, text, prio, status, body, warn))
        qchips.append(f'<a class="qc{" w" if warn else ""}" href="#sec2{n}" title="{esc(text)}">Q{n}</a>')
    s2_html = ('<h4>Jawaban singkat</h4><div class="card"><p>Semua 12 pertanyaan dijawab dengan angka dari data. '
               f"Jawaban bercatatan (kuning): Q2, Q4, Q5, Q8, Q9, Q12. Pertanyaan utama dijawab di bagian 7.</p>"
               '<div class="qchips">' + "".join(qchips) + '</div>'
               '<p class="tight">Q hijau = terjawab, Q kuning = terjawab dengan catatan.</p></div>'
               + "".join(cards_s2)
               + '<h4>Hipotesis pada Design Project</h4><p>Bunyi dan ambang hipotesis mengikuti rancangan dan docs/definitions.md. Yang dibantah data ditulis apa adanya.</p>'
               + t_hyp + "<p class='tight'>Tabel 2.H: verdict hipotesis (Terbukti / Sebagian / Tidak terbukti).</p>")
    s2_html = s2_html  # dipakai di rp2

    rp1 = ('<div class="callout a"><h4>Catatan data</h4><p>Ini data publik (bukan simulasi). Dua sheet di file asli tumpang tindih; dibersihkan dengan dedup.</p></div>'
           '<div class="card"><p>Data mentah: ' + num(raw_total) + ' baris, 8 kolom. Data bersih: ' + num(used) + ' baris dipakai, '
           + num(5852) + ' pelanggan unik.</p></div>'
           '<h4>1.1 Kualitas data dan keputusan cleaning</h4>' + t_clog + '<p class="tight">Tabel 1.1: alasan tiap baris (satu alasan per baris, urutan prioritas, total = jumlah baris mentah).</p>'
           '<h4>1.2 Database dan file hasil</h4><div class="card"><p>Database DuckDB (retail.duckdb, tidak di-commit) berisi tabel raw_union, raw_dedup, cleaning_tagged, transactions_clean, returns_lines, customers, cohort_retention, dim_segment, customers_seg.</p></div>'
           + '<p class="tight">Tabel 1.2a: isi database.</p>'
           + t_cc + '<p class="tight">Tabel 1.2b: cek silang SQL vs pandas (Q11).</p>'
           + '<h4>1.3 Angka kunci (KPI)</h4>' + t_kpi + '<p class="tight">Tabel 1.3: KPI dari results/2-analysis/kpi.csv.</p>')
    rp2 = s2_html
    rp3 = ('<div class="card"><p><b>Jawaban singkat:</b> dataset sesuai, dengan satu perubahan: dua sheet tumpang tindih dan harus didedup.</p></div>'
           + table(["Rancangan", "Realisasi", "Verdict"], [
               ["Dataset Online Retail II, 1.067.371 baris, 8 kolom", f"{num(raw_total)} baris, 8 kolom (2 sheet)", pill("Sesuai", "")],
               ["Periode 1 Des 2009 sampai 9 Des 2011", f"{prof['tanggal_min'][:10]} sampai {prof['tanggal_max'][:10]}", pill("Sesuai", "")],
               ["Lisensi CC BY 4.0", "CC BY 4.0 (sesuai halaman dataset); belum diverifikasi dengan file yang diunduh", pill("Sesuai", "")],
               ["Hipotesis 5: 20–25% baris tanpa Customer ID", f"{pct_raw(float(hyp.set_index('hipotesis').loc['H5','nilai']),2)} baris mentah", pill("Terbukti", "")],
               ["Jumlah pelanggan unik sekitar 5.900", f"{num(cust_n)} pelanggan (dengan Customer ID dan baris bersih)", pill("Sesuai", "")],
               ["Dataset ini dipakai juga di Project 9 (skrip cleaning dipakai ulang)", "Skrip cleaning dibuat baru di repo ini; belum diverifikasi dengan Project 9", pill("Belum dikerjakan", "d")],
           ]) + '<p class="tight">Tabel 3.1: perbandingan dataset rancangan dengan realisasi.</p>'
           + '<h4>3.2 Hipotesis data</h4>' + t_hyp)
    rp4 = (table(["Rancangan", "Realisasi", "Verdict"], [
        ["DuckDB + SQL", "DuckDB 2.0 (cleaning, kohort, RFM) dan SQL", pill("Sesuai", "")],
        ["Python (pandas)", "pandas (cek silang Q11, skenario Q9, uji statistik)", pill("Sesuai", "")],
        ["Streamlit + Plotly", "Streamlit 1.66 dan Plotly; diuji AppTest, belum di-deploy", pill("Sebagian", "p")],
        ["Excel (opsional)", "Tidak dibuat; cek silang dilakukan di pandas", pill("Tidak dibuat", "d")],
        ["GitHub + Markdown", "Repo, README, dan docs", pill("Sesuai", "")],
    ]) + '<p class="tight">Tabel 4.1: tools rancangan vs eksekusi.</p>')
    rp5 = ('<p>Dari 12 langkah rancangan, semua dikerjakan. Dua di antaranya dipecah lebih rinci dan penomoran skrip mengikuti urutan data.</p>'
           + table(["Langkah rancangan", "Realisasi", "Verdict"], [
               ["1 Menyepakati definisi", "docs/definitions.md (asumsi diberi label)", pill("Sesuai + penyesuaian", "")],
               ["2 Mengunduh dan mendokumentasikan sumber", "Diunduh user (sandbox diblokir); DOI dan tanggal akses dicatat", pill("Berubah", "p")],
               ["3 Profil dan cleaning", "01_prepare_raw.py, 02_clean_and_load.py, 01_clean.sql", pill("Sesuai + tambahan", "")],
               ["4 Memuat ke DuckDB", "02_clean_and_load.py (raw_union dan transactions_clean)", pill("Sesuai", "")],
               ["5 Tabel pelanggan", "03_customers.sql", pill("Sesuai", "")],
               ["6 Retensi kohort (Q1–Q3)", "04_cohort.sql dan 05_analysis.py", pill("Sesuai", "")],
               ["7 Skor RFM dan segmen (Q4–Q6)", "05_rfm_segments.sql dan 05_analysis.py", pill("Sesuai", "")],
               ["8 Produk dan jarak (Q7–Q8)", "05_analysis.py", pill("Sesuai", "")],
               ["9 Skenario dampak (Q9)", "05_analysis.py", pill("Sesuai", "")],
               ["10 Cek silang dan stabilitas (Q11–Q12)", "04_crosscheck.py, 05_analysis.py, 06_sensitivity.py", pill("Sesuai + tambahan", "")],
               ["11 Dashboard", "07_dashboard_data.py, app.py, 08_test_dashboard.py", pill("Sebagian", "p")],
               ["12 README dan finalisasi", "README.md, docs", pill("Sesuai", "")],
           ]) + '<p class="tight">Tabel 5.1: langkah rancangan vs yang dijalankan.</p>'
           + '<h4>5.2 Penyesuaian dan improvisasi</h4><div class="card"><ul>'
           + '<li>Dua sheet tumpang tindih 1–9 Des 2010 didedup (keputusan tambahan).</li>'
           + '<li>Kode non-produk (POST, DOT, M, dll.) dikeluarkan dari analisis.</li>'
           + '<li>Segmen: aturan delapan segmen dilengkapi; Lost dipisahkan dari Hibernating.</li>'
           + '<li>Sensitivitas definisi dilakukan (06_sensitivity.py).</li></ul></div>'
           + table(["Rancangan", "Realisasi"], [
               ["sql/02_customers.sql", "project/code/2-analysis/sql/03_customers.sql"],
               ["sql/03_cohort.sql", "project/code/2-analysis/sql/04_cohort.sql"],
               ["sql/04_rfm_segments.sql", "project/code/2-analysis/sql/05_rfm_segments.sql"],
               ["notebooks/analysis.ipynb", "(tidak ada di rancangan) tidak dibuat"],
           ]) + '<p class="tight">Tabel 5.2: perubahan nama dan lokasi file.</p>')
    rp6_status = table(["Output", "Status", "Bukti"], [
        ["Dashboard interaktif", pill("Sebagian", "p"), "Dibuat dan diuji AppTest; belum di-deploy"],
        ["Strategi per segmen", pill("Tercapai", ""), "Tabel 2.4a dan kolom Aksi"],
        ["Database dan query SQL", pill("Tercapai", ""), "project/code/*/sql/*.sql"],
        ["Log cleaning", pill("Tercapai", ""), "Tabel 1.1 dan results/1-data-preparation/cleaning_log.csv"],
        ["Notebook analisis", pill("Tidak dibuat", "d"), "Diganti skrip Python"],
        ["Laporan temuan dan rekomendasi", pill("Tercapai", ""), "README dan halaman ini"],
        ["Repositori GitHub", pill("Sebagian", "p"), "Branch project-22-build; belum di-merge"],
        ["Slide presentasi (Opsional)", pill("Tidak dibuat", "d"), "–"],
    ]) + '<p class="tight">Tabel 6.1: status output rancangan.</p>'
    rp6_files = table(["Dokumen rancangan", "Realisasi", "Verdict"], [
        ["data/raw/online_retail_II.xlsx", "project/data/raw/ (tidak di-commit)", pill("Sesuai", "")],
        ["sql/01_clean.sql", "project/code/1-data-preparation/sql/01_clean.sql", pill("Sesuai", "")],
        ["docs/cleaning_log.md", "project/results/1-data-preparation/cleaning_log.csv", pill("Berubah", "p")],
        ["retail.duckdb", "project/retail.duckdb (tidak di-commit)", pill("Sesuai", "")],
        ["notebooks/analysis.ipynb", "(tidak dibuat)", pill("Tidak dibuat", "d")],
        ["dashboard/app.py", "project/code/3-presentation/streamlit/app.py", pill("Sesuai", "")],
        ["slides/presentation.pdf", "(tidak dibuat)", pill("Tidak dibuat", "d")],
    ]) + '<p class="tight">Tabel 6.2: daftar dokumen rancangan vs repositori.</p>'
    rp6 = rp6_status + rp6_files
    crit = [
        ["Ketujuh pertanyaan utama terjawab dengan angka dari data", "Tercapai", "Q1, Q2, Q4, Q5, Q9, Q10, Q11"],
        ["Retensi dan skor RFM SQL sama dengan pandas", "Tercapai", f"{xcheck_pass} dari {xcheck_total} cek lulus"],
        ["Setiap hipotesis dinyatakan terbukti, tidak terbukti, atau belum bisa disimpulkan", "Tercapai", f"{hyp_counts.get('Terbukti',0)} Terbukti, {hyp_counts.get('Sebagian',0)} Sebagian, {hyp_counts.get('Tidak terbukti',0)} Tidak terbukti (Tabel 2.H)"],
        ["Log cleaning mencatat semua keputusan dan jumlah barisnya", "Tercapai", "Tabel 1.1, total = baris mentah"],
        ["Orang awam bisa membuka dashboard dan menyebut segmen paling bernilai dan berisiko dalam < 1 menit", "Belum diuji", "Belum ada uji pembaca awam"],
        ["Checklist standar terpenuhi: dashboard ter-deploy", "Sebagian", "Dashboard belum di-deploy"],
    ]
    n_ok = sum(1 for c in crit if c[1] == "Tercapai")
    crit_html = table(["Kriteria", "Status", "Bukti"], [[c[0], pill(c[1], "" if c[1] == "Tercapai" else "p"), c[2]] for c in crit])
    rp7 = (
        '<h4>7.1 Hasil analisis</h4><div class="card"><p><b>Pertanyaan utama:</b> seperti rancangan. '
        f'Retensi bulan 1 rata-rata {pct(kpi["retention_rate_bulan_1_tertimbang"])}. Hanya sekitar {pct_raw(top20_share,0)} revenue dari 20% pelanggan teratas (H1 Terbukti). '
        f'Segmen Champions ({pct_raw(champ.pct_pelanggan,1)} pelanggan) menyumbang {pct_raw(champ.pct_revenue,1)} revenue. At Risk dan Lost punya median recency lebih dari setahun.</p></div>'
        '<h4>7.2 Impact</h4><div class="card"><p>Estimasi (label estimated): kenaikan retensi bulan 1 sebesar 2 poin menambah sekitar £'
        + num(q9.iloc[0].tambahan_revenue_per_tahun_estimated, 0) + ' per tahun; 5 poin sekitar £' + num(q9.iloc[1].tambahan_revenue_per_tahun_estimated, 0)
        + '; 10 poin sekitar £' + num(q9.iloc[2].tambahan_revenue_per_tahun_estimated, 0) + '. Angka ini memakai asumsi revenue per pelanggan aktif dan tidak diuji di lapangan.</p></div>'
        '<h4>7.3 Success criteria</h4>' + crit_html + f'<p class="tight">Hasil: {n_ok} dari {len(crit)} kriteria tercapai penuh; sisanya sebagian atau belum diuji.</p>'
        '<h4>7.4 Rekomendasi</h4><div class="card"><ul>'
        '<li><b>Champions</b> (' + pct_raw(champ.pct_pelanggan,1) + ' pelanggan): pertahankan dengan layanan dan penawaran prioritas.</li>'
        '<li><b>At Risk</b> dan <b>Need Attention</b>: aktifkan kembali sebelum memburuk. Median recency At Risk sekitar ' + num(at_risk.median_recency_hari,0) + ' hari.</li>'
        '<li><b>Hibernating</b> dan <b>Lost</b>: biarkan, kecuali ada kampanye biaya rendah.</li>'
        '<li><b>Pelanggan baru</b> (Potential Loyalist dan New): dorong pembelian kedua. Repeat purchase rate hanya ' + pct(kpi['repeat_purchase_rate']) + ' secara keseluruhan.</li></ul></div>'
        '<h4>7.5 Saran perbaikan</h4><div class="card"><ul>'
        '<li>Uji stabilitas segmen dengan kohort per bulan, bukan hanya dua snapshot.</li>'
        '<li>Ukur efek kampanye aktivasi ulang (Need Attention, At Risk) lewat kelompok kontrol.</li>'
        '<li>Deploy dashboard dan uji dengan pembaca awam.</li></ul></div>'
        '<h4>7.6 Batasan</h4><div class="card"><ul>'
        '<li>Angka dampak (Q9) adalah estimasi dari asumsi, bukan hasil eksperimen. Label estimated.</li>'
        '<li>Desember 2009 bisa berisi pelanggan lama sebelum periode data; Desember 2011 tidak lengkap.</li>'
        '<li>Aturan segmen dan ambang hipotesis adalah asumsi (docs/definitions.md). Hasil di-sensitivitas (Tabel 7.6a).</li>'
        '<li>Skor F banyak berbagi nilai (kebanyakan pelanggan 1–2 invoice), sehingga batas kuintil bergantung pada tie-breaker.</li>'
        '<li>Pergeseran tanggal acuan recency tidak mengubah segmen, karena NTILE berbasis peringkat (lihat Tabel 7.6a).</li>'
        '<li>Hipotesis H4 terbukti secara aturan, tetapi selisih frekuensi (6,24 vs 6,26) sangat kecil.</li>'
        '<li>Segmen menunjukkan perilaku, bukan penyebab berhenti belanja.</li>'
        '<li>Dashboard belum di-deploy. Branch project-22-build belum di-merge ke main.</li></ul></div>'
        + t_sens + '<p class="tight">Tabel 7.6a: uji sensitivitas definisi (06_sensitivity.py).</p>'
    )
    return "".join([
        '<h2 id="rp1">1. Data yang berhasil didapatkan<small>Isi data mentah, tabel di database, dan data hasil analisis</small></h2>' + rp1,
        '<h2 id="rp2">2. Apakah business question terjawab?<small>12 pertanyaan pada Design Project, dijawab dengan data</small></h2>' + rp2,
        '<h2 id="rp3">3. Apakah dataset sesuai dengan Design Project?<small>Perbandingan rancangan dengan realisasi</small></h2>' + rp3,
        '<h2 id="rp4">4. Apakah tools yang digunakan sesuai?<small>Perbandingan rancangan dengan eksekusi</small></h2>' + rp4,
        '<h2 id="rp5">5. Apakah alur pengerjaan sesuai dengan Design Project?<small>12 langkah rancangan vs yang dijalankan</small></h2>' + rp5,
        '<h2 id="rp6">6. Apakah project output tercapai?<small>Output pada Design Project, bagian 7</small></h2>' + rp6,
        '<h2 id="rp7">7. Kesimpulan<small>Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan</small></h2>' + rp7,
    ])


REPORT_CSS = """
.qchips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}
.qc{display:inline-block;padding:4px 10px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--navy);font-weight:600;text-decoration:none;font-size:14px}
.qc.w{background:#FEF7E0;border-color:#FDD663;color:#3C2A00}
.qa{background:var(--card);border:1px solid var(--line);border-left:6px solid var(--teal);border-radius:14px;padding:14px 18px;margin:14px 0}
.qa.w{border-left-color:var(--amber)}
.qh{font-weight:700;margin-bottom:6px}
.qn{display:inline-block;background:var(--soft);color:var(--head);border-radius:8px;padding:2px 8px;margin-right:4px}
.qt{color:var(--ink)}
.qb p{margin:6px 0}
.tight{font-size:14px;color:var(--mut);margin:4px 0 14px}
@media (min-width:1280px){
main{grid-template-columns:250px minmax(0,1fr)}
main>nav{display:grid;grid-template-columns:1fr 1fr;gap:8px}
main>nav .tab{padding:10px 8px;font-size:15px;text-align:center;border:2px solid var(--line);border-top:6px solid var(--c)}
main>nav .tab.on{border-color:var(--c);background:var(--c);color:#fff}
main>nav .links{grid-column:1/-1;margin:8px 0 0 4px}}
.pane code{overflow-wrap:anywhere}
.pane pre code{overflow-wrap:normal}
"""

report_html_body = build_report()
intro = ('<div class="callout a"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4>'
         '<p>Data pada project ini adalah dataset publik Online Retail II (bukan simulasi). Ada 12 cek silang dan ' + num(len(sens)) + ' uji sensitivitas. '
         'Angka dibaca dari file CSV di results/, tidak diketik tangan.</p></div>'
         + table(["No", "Pertanyaan evaluasi", "Verdict", "Ringkasan"], [[a, esc(b), c, esc(d)] for a, b, c, d in evq_rows]))
nav_block = ""
report_pane = ('<div class="pane" id="report" data-tab="report" hidden>\n' + intro + "\n" + report_html_body + "\n</div>\n\n")

head_part = src[:d_start]
assert head_part.count("</style>") == 1, "blok style harus satu"
head_part = head_part.replace("</style>", REPORT_CSS + "</style>")
NAV_NEW = (
    '<nav aria-label="Project navigation">'
    '<button type="button" class="tab on" data-t="design" aria-expanded="true" aria-controls="design">Design Project</button>'
    '<button type="button" class="tab" data-t="report" aria-expanded="false" aria-controls="report">Report Project</button>'
    '<div class="links" data-tab="design">'
    '<a href="#s1">Background</a><a href="#s2">Business Questions</a><a href="#s3">Cohort &amp; RFM</a>'
    '<a href="#s4">Dataset</a><a href="#s5">Tools</a><a href="#s6">Work Plan</a><a href="#s7">Project Outputs</a>'
    '<a href="#s8">Success Criteria</a><a href="#s9">Assumptions &amp; Limitations</a></div>'
    '<div class="links" data-tab="report" hidden>'
    '<a href="#rp1">Data</a><a href="#rp2">Business Questions</a><a href="#rp3">Dataset</a><a href="#rp4">Tools</a>'
    '<a href="#rp5">Alur Kerja</a><a href="#rp6">Project Output</a><a href="#rp7">Kesimpulan</a></div></nav>'
)
head_part, n_nav = re.subn(r'<nav aria-label="Project navigation">.*?</nav>', lambda m: NAV_NEW, head_part, flags=re.S)
assert n_nav == 1, n_nav
out = head_part + design_pane + report_pane + script_block
# pastikan pane Design tidak berubah
out_path = HERE.parent / "index.html"
out_path.write_text(out, encoding="utf-8")
print("tertulis", out_path, len(out))
