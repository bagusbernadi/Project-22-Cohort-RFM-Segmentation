# Data

## Sumber
- Dataset: Online Retail II, UCI Machine Learning Repository.
- Link: https://archive.ics.uci.edu/dataset/502/online+retail+ii
- Versi: DOI 10.24432/C5CG6D, didonasikan 20 September 2019.
- Tanggal akses: 24 Oktober 2026 (dicatat dari rancangan; file diunduh user dan dilampirkan ke sesi).
- Lisensi: CC BY 4.0.
- Sitasi: Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository.
- File: `online_retail_II.xlsx` (dari `online_retail_II.zip`), 2 sheet: `Year 2009-2010` dan `Year 2010-2011`.

## Cara menjalankan ulang
1. Unduh dataset dari link di atas (atau pakai file yang sudah dilampirkan).
2. Simpan sebagai `project/data/raw/online_retail_II.xlsx`. Folder ini tidak di-commit.
3. Jalankan `code/run_all.sh` dari folder `project/`.

## Isi folder
- `raw/`: file asli (tidak di-commit).
- `clean/`: parquet hasil gabungan dua sheet (tidak di-commit).
- `reference/`, `sample/`: tidak dipakai.
