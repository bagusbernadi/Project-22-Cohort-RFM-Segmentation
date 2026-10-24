[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 22: Cohort & RFM Segmentation

**Status: Design (rancangan).**

**Tujuan:** Mengukur berapa banyak pelanggan yang kembali belanja dari bulan ke bulan dan mengelompokkan pelanggan berdasarkan kapan terakhir belanja, seberapa sering, dan berapa besar belanjanya, sehingga toko bisa memilih segmen yang perlu dipertahankan, diaktifkan kembali, atau dibiarkan, beserta estimasi dampaknya.


| | |
|---|---|
| Kategori | Retail online |
| Tingkat | Menengah |
| Data | Dataset publik: Online Retail II (UCI Machine Learning Repository) |
| Tools | DuckDB + SQL, Python (pandas), Streamlit + Plotly, Excel (opsional) |

## 1. Problem
Bagaimana pola retensi pelanggan per kohort, segmen RFM mana yang paling bernilai atau paling berisiko berhenti belanja, dan strategi apa yang paling layak untuk tiap segmen?

## 2. Data
Online Retail II, UCI Machine Learning Repository. Sumber data: [here](https://archive.ics.uci.edu/dataset/502/online+retail+ii) (Versi: DOI 10.24432/C5CG6D, didonasikan 20 September 2019, Tanggal akses: 24 Oktober 2026). Lisensi CC BY 4.0. Sitasi: Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. Ukuran menurut halaman dataset: 1.067.371 baris, 8 kolom, 1 Desember 2009 sampai 9 Desember 2011 (perkiraan, belum diverifikasi dengan file yang diunduh). File data tidak disimpan di repo.

## 3. Analysis
Rencana: matriks retensi kohort bulanan, skor RFM kuintil dan 8 segmen, produk per segmen, skenario uplift retensi, cek silang SQL vs pandas. Belum dikerjakan.

## 4. Recommendation
Belum dikerjakan.

## 5. Impact
Belum dikerjakan. Angka dampak akan diberi label `estimated` / `simulated`.

## Batasan yang sudah diketahui
- Kohort Desember 2009 bisa berisi pelanggan lama sebelum periode data.
- Desember 2011 tidak lengkap.
- Baris tanpa Customer ID tidak dipakai untuk kohort dan RFM.
- Segmen menunjukkan perilaku, bukan penyebab.

## Struktur repository (rencana)
```
docs/            # definisi dan log cleaning
data/README.md   # sumber, versi, cara mengunduh
sql/             # cleaning, pelanggan, kohort, RFM
notebooks/       # analisis dan cek silang
dashboard/       # aplikasi Streamlit
index.html       # halaman rancangan (GitHub Pages)
README.md
```
