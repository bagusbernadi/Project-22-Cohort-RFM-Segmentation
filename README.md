[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 22: Cohort & RFM Segmentation

| | |
|---|---|
| Kategori | Retail online |
| Tingkat | Menengah |
| Data | Dataset publik: Online Retail II (UCI Machine Learning Repository), data nyata, bukan simulasi |
| Tools | DuckDB + SQL, Python (pandas, SciPy), Streamlit + Plotly |

Status: **Selesai di branch `project-22-build`** (belum di-merge ke `main`). Dashboard belum di-deploy.

Pertanyaan utama: pola retensi pelanggan per kohort, segmen RFM mana yang paling bernilai atau paling berisiko, dan strategi apa untuk tiap segmen.

## 1. Problem
Bagaimana pola retensi pelanggan per kohort, segmen RFM mana yang paling bernilai atau paling berisiko berhenti belanja, dan strategi apa yang paling layak untuk tiap segmen?

## 2. Data
Online Retail II, UCI Machine Learning Repository. Sumber data: [here](https://archive.ics.uci.edu/dataset/502/online+retail+ii) (Versi: DOI 10.24432/C5CG6D, didonasikan 20 September 2019, Tanggal akses: 24 Oktober 2026). Lisensi CC BY 4.0. Sitasi: Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository.

- Data mentah: 1.067.371 baris, 2 sheet yang tumpang tindih 1–9 Desember 2010. Setelah dedup dan cleaning, 776.583 baris dipakai dari 5.852 pelanggan.
- Customer ID kosong 21,96% baris (rancangan memperkirakan 20–25%).
- Keputusan cleaning: detail di `project/docs/cleaning_log.md` dan `project/results/1-data-preparation/cleaning_log.csv`.
- File data tidak disimpan di repo; unduh dari sumber di atas (lihat `project/data/README.md`).

## 3. Analysis
- Retensi kohort bulanan (bulan 0 sampai 23). Retensi bulan 1 tertimbang: 23,3%.
- Repeat purchase rate: 72,4% pelanggan punya ≥2 invoice.
- Skor RFM kuintil dan 8 segmen. Champions (25% pelanggan) menyumbang 68,9% revenue.
- Retensi per kuartil nilai invoice pertama: bulan 1 naik dari 16,4% (kuartil terendah) ke 30,1% (kuartil tertinggi).
- Perbandingan Inggris vs luar Inggris: komposisi segmen berbeda (chi-kuadrat, p < 0,000001).
- Cek silang SQL vs pandas: 13 dari 13 cek lulus.
- Hipotesis: H1–H5 semuanya Terbukti menurut ambang di `project/docs/definitions.md`. H4 terbukti secara aturan, tetapi selisih frekuensi sangat kecil (6,24 vs 6,26 invoice per pelanggan).

## 4. Recommendation
- **Champions**: pertahankan dengan layanan dan penawaran prioritas.
- **At Risk** dan **Need Attention**: aktifkan kembali. Median recency At Risk 374 hari.
- **Hibernating** dan **Lost**: biarkan, kecuali ada kampanye biaya rendah.
- **Potential Loyalist** dan **New**: dorong pembelian kedua.

## 5. Impact
Estimasi (label estimated, bukan hasil eksperimen): kenaikan retensi bulan 1 sebesar 2 poin menambah sekitar £535.770 revenue per tahun, 5 poin sekitar £1,34 juta, dan 10 poin sekitar £2,68 juta. Asumsi revenue per pelanggan aktif per bulan: £669 (dari data).

## Batasan
- Dampak (bagian 5) adalah estimasi dari asumsi, belum diuji di lapangan.
- Desember 2009 bisa berisi pelanggan lama sebelum periode data. Desember 2011 tidak lengkap dan tidak dipakai sebagai bulan penuh.
- Aturan segmen dan ambang hipotesis adalah asumsi (`project/docs/definitions.md`). Uji sensitivitas di `project/results/2-analysis/sensitivity.csv`.
- Skor F banyak bernilai sama (kebanyakan pelanggan 1–2 invoice). Batas kuintil F bergantung pada tie-breaker `customer_id`.
- Menggeser tanggal acuan recency tidak mengubah segmen, karena `NTILE` berbasis peringkat.
- Stabilitas segmen rendah: hanya 41,3% pelanggan yang sama segmennya antara snapshot 2010 dan 2011.
- Segmen menunjukkan perilaku, bukan penyebab berhenti belanja.
- Dashboard belum di-deploy; belum diuji oleh pembaca awam.
- Branch `project-22-build` belum di-merge ke `main`.

## Menjalankan
Dari folder `project/`:
```
pip install -r requirements.txt
# letakkan online_retail_II.xlsx di data/raw/
code/run_all.sh
streamlit run code/3-presentation/streamlit/app.py
```
Laporan dibangun dengan `python design-and-report/src/build_report.py` dari root repo.

## Struktur repository
```
README.md
index.html                       pengalihan ke design-and-report/
design-and-report/
  index.html                     halaman Design + Report (GitHub Pages)
  src/page_v1.html               salinan rancangan (sumber pane Design)
  src/report_lib.py, build_report.py
project/
  code/
    common.py                    path dan konstanta
    run_all.sh                   jalankan pipeline dari nol
    1-data-preparation/python/   01_prepare_raw.py, 02_clean_and_load.py
    1-data-preparation/sql/      01_clean.sql
    2-analysis/python/           03_run_analysis_sql.py, 04_crosscheck.py, 05_analysis.py, 06_sensitivity.py, rfm_lib.py
    2-analysis/sql/              03_customers.sql, 04_cohort.sql, 05_rfm_segments.sql
    3-presentation/python/       07_dashboard_data.py, 08_test_dashboard.py
    3-presentation/streamlit/    app.py
  results/                       hasil CSV per tahap
  data/                          raw/ dan clean/ tidak di-commit; README.md (sumber)
  docs/                          definitions.md, cleaning_log.md, data_dictionary.md
  requirements.txt
  retail.duckdb                  dibuat ulang (tidak di-commit)
```
