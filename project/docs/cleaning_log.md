# Log cleaning

Angka dari `results/1-data-preparation/cleaning_log.csv`. Satu alasan per baris, urutan prioritas dari atas. Total = jumlah baris mentah (1.067.371).

| Alasan | Jumlah baris | % dari raw |
|---|---:|---:|
| Duplikat persis dihapus (8 kolom) | 34.335 | 3,22 |
| Customer ID kosong | 234.437 | 21,96 |
| Retur atau batal (invoice `C…`) | 19.104 | 1,79 |
| Kode non-produk | 2.852 | 0,27 |
| Harga nol atau negatif | 60 | 0,01 |
| **Dipakai** | **776.583** | **72,76** |

Catatan:
- Kedua sheet tumpang tindih 1–9 Des 2010 (22.523 baris per sheet di periode itu). Duplikat dihapus lewat `DISTINCT` pada 8 kolom.
- Retur tidak dihapus dari database; disimpan di `returns_lines`.
- Quantity ≤ 0 pada invoice bukan retur tidak ditemukan setelah langkah sebelumnya (0 baris).
