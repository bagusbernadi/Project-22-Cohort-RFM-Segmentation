# Definisi dan asumsi

Label: **[rancangan]** = tertulis di rancangan (index.html). **[asumsi]** = ditetapkan di sini karena rancangan belum mendefinisikannya; diuji sensitivitasnya di `code/2-analysis/python/06_sensitivity.py`.

## Data dan periode
- **[rancangan]** Dataset: Online Retail II (UCI), 2 sheet, 1 Des 2009 sampai 9 Des 2011.
- **[asumsi]** Kedua sheet tumpang tindih 1–9 Des 2010 (22.523 baris di tiap sheet). Semua baris digabung, lalu duplikat persis di 8 kolom dihapus (`DISTINCT`). Konsekuensi: pasangan baris identik yang sah dalam satu invoice juga ikut terhapus.
- **[asumsi]** Desember 2011 tidak dipakai sebagai bulan penuh (data berhenti 9 Des 2011). Retensi hanya dihitung untuk bulan kohort + k yang berakhir sebelum 1 Des 2011 (bulan terakhir penuh = November 2011).
- **[asumsi]** Kohort Desember 2009 dipakai, tetapi diberi catatan: pelanggan lama sebelum periode data ikut terhitung sebagai "pembelian pertama".

## Penyaringan baris (urutan prioritas, satu alasan per baris)
Lihat `code/1-data-preparation/sql/01_clean.sql` dan `results/1-data-preparation/cleaning_log.csv`.
1. **[asumsi]** Duplikat persis di 8 kolom: dihapus.
2. **[asumsi]** Invoice berawalan `C` (retur atau batal): dipisah ke `returns_lines`, tidak masuk kohort atau RFM.
3. **[asumsi]** Customer ID kosong: tidak dipakai (dari rancangan: "Baris tanpa Customer ID tidak dipakai").
4. **[asumsi]** Kode non-produk (`POST`, `DOT`, `M`, `D`, `S`, `B`, `m`, `C2`, `BANK CHARGES`, `ADJUST`, `AMAZONFEE`, `PADS`, `CRUK`, `TEST001`): ongkos kirim, biaya bank, penyesuaian, atau uji. Bukan pembelian produk.
5. **[asumsi]** Harga ≤ 0: dibuang.
6. **[asumsi]** Quantity ≤ 0 pada invoice bukan retur: dibuang (tidak ditemukan setelah langkah sebelumnya).

## Pelanggan aktif dan kohort
- **[rancangan]** Kohort = bulan pembelian pertama pelanggan.
- **[asumsi]** Pelanggan **aktif** di bulan m jika punya minimal 1 invoice dengan baris bersih di bulan m (`date_trunc('month')`).
- Retensi bulan ke-k (k = 0, 1, 2, …) = jumlah pelanggan aktif di bulan kohort + k dibagi ukuran kohort. Bulan ke-0 selalu 100%.
- Retensi "1, 3, dan 6 bulan" (Q1) = k = 1, 3, 6.
- **Uji sensitivitas:** aktif = minimal 2 invoice di bulan itu (lihat `06_sensitivity.py`).

## Skor RFM
- **[rancangan]** Recency, Frequency, Monetary; skor kuintil 1–5 (NTILE).
- **[asumsi]** Tanggal acuan recency = 10 Des 2011 (satu hari setelah transaksi terakhir, 9 Des 2011). `recency_days` = tanggal acuan − tanggal invoice terakhir.
- **[asumsi]** Frequency = jumlah invoice berbeda. Monetary = jumlah `line_revenue` (quantity × price) dari baris bersih, seluruh periode.
- **[asumsi]** R = 6 − NTILE(5) dari recency (recency kecil = skor 5). F dan M = NTILE(5) ascending. Pengurutan memakai `customer_id` sebagai tie-breaker.
- **Batasan:** Frequency sangat banyak bernilai sama (kebanyakan pelanggan hanya 1–2 invoice), sehingga batas kuintil F bergantung pada urutan tie-breaker. Dicatat di Batasan.

## Segmen (8 segmen)
- **[rancangan]** Champions (R 4–5, F 4–5); At Risk (R 1–2, F 3–5); Hibernating (R 1–2, F 1–2).
- **[asumsi]** Aturan dievaluasi berurutan (baris pertama yang cocok):
  1. Champions: R ≥ 4 dan F ≥ 4
  2. Loyal: R ≥ 3 dan F ≥ 3
  3. New: R = 5 dan F = 1
  4. Potential Loyalist: R ≥ 4 (sisanya dengan F ≤ 2)
  5. Need Attention: R = 3 dan F ≤ 2
  6. At Risk: R ≤ 2 dan F ≥ 3 **[rancangan]**
  7. Lost: R = 1 dan F = 1
  8. Hibernating: R ≤ 2 dan F ≤ 2 (sisa dari R 1–2, F 1–2 **[rancangan]**, setelah Lost dipisah)
- Aksi: Champions, Loyal, Potential Loyalist, New → **pertahankan**; Need Attention, At Risk → **aktifkan kembali**; Hibernating, Lost → **biarkan**.

## Uplift retensi (Q9)
- **[rancangan]** Kenaikan retensi bulan ke-1 sebesar 2, 5, dan 10 poin; kenaikan diasumsikan ikut ke bulan berikutnya secara proporsional; revenue contoh £250 per pelanggan aktif per bulan (hanya ilustrasi di dashboard).
- **[asumsi]** Revenue per pelanggan aktif per bulan = total `line_revenue` dibagi total pelanggan-bulan aktif di data (bukan £250).
- **[asumsi]** Retensi baru k = retensi lama k × (retensi lama 1 + kenaikan) / retensi lama 1. Tambahan pelanggan-bulan = ukuran kohort × selisih retensi, dijumlahkan untuk bulan yang teramati.
- **[asumsi]** Estimasi tahunan = tambahan revenue total dibagi lama periode data (tahun, dari 1 Des 2009 sampai 30 Nov 2011). Semua angka berlabel **estimated**.

## Hipotesis (ambang keputusan)
- H1 "sebagian kecil (sekitar 20%) menyumbang sebagian besar revenue": **[asumsi]** Terbukti jika 20% pelanggan teratas (menurut monetary) ≥ 50% revenue. Di 20–50% = Sebagian.
- H2 "retensi turun paling tajam dari bulan 0 ke 1, lalu mendatar": **[asumsi]** Dihitung per kohort lalu dirata-rata antar kohort: penurunan 0→1 = r0 − r1; penurunan lanjutan = rata-rata (r_{k−1} − r_k) untuk k = 2..6. Terbukti jika penurunan 0→1 lebih besar dari penurunan lanjutan; Sebagian jika lebih besar tetapi selisihnya kurang dari 2×; Tidak terbukti jika tidak.
- H3 "Desember 2009 paling loyal": **[asumsi]** Terbukti jika retensi bulan 1, 3, dan 6 Des 2009 lebih tinggi dari rata-rata (tanpa bobot) kohort lain yang teramati pada k yang sama; Sebagian jika hanya sebagian k.
- H4 "luar Inggris lebih jarang belanja, nilai per invoice lebih besar": **[asumsi]** Terbukti jika invoice per pelanggan lebih kecil DAN rata-rata nilai per invoice lebih besar untuk luar Inggris.
- H5 "20–25% baris tanpa Customer ID": **[rancangan]** Dicek terhadap persentase baris raw (22,77%).

## Q3 dan Q12
- Q3 (**[asumsi]**): nilai pembelian pertama = total `line_revenue` pada invoice pertama pelanggan, dibagi kuartil seluruh pelanggan. Retensi bulan 1 hanya untuk kohort ≤ Oct 2011 dan bulan 3 hanya untuk kohort ≤ Aug 2011 (bulan kohort + k harus sudah lengkap).
- Q12 (**[asumsi]**): snapshot 2010 = data sampai 9 Des 2010 dengan tanggal acuan 10 Des 2010; snapshot 2011 = data penuh dengan tanggal acuan 10 Des 2011. Skor RFM dihitung ulang di tiap snapshot dengan populasi snapshot itu. Stabilitas = persen pelanggan yang punya pembelian sampai 9 Des 2010 dan mendapat segmen sama di kedua snapshot.

## Uji dan interval
- Interval kepercayaan 95% untuk proporsi: Wilson. Jumlah pelanggan per kohort ditulis di tabel.
- Perbandingan dua kelompok: Mann-Whitney U (distribusi miring). Kelompok kecil (< 30 pelanggan) ditandai.
