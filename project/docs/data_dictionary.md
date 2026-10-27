# Kamus data

## Sumber (raw, Online Retail II)
| Kolom | Arti |
|---|---|
| Invoice | Nomor invoice. Berawalan `C` = retur atau batal |
| StockCode | Kode produk (atau kode non-produk) |
| Description | Nama produk |
| Quantity | Jumlah barang per baris |
| InvoiceDate | Tanggal dan jam invoice |
| Price | Harga satuan (GBP) |
| Customer ID | ID pelanggan (kosong pada ±23% baris) |
| Country | Negara pelanggan |

## Tabel di DuckDB (retail.duckdb, tidak di-commit)
| Tabel | Isi (1 baris = …) | Kolom utama |
|---|---|---|
| raw_union | Satu baris mentah dari dua sheet | 8 kolom asli + source_sheet |
| raw_dedup | Satu baris setelah dedup 8 kolom | invoice, stock_code, quantity, invoice_ts, price, customer_id, country |
| cleaning_tagged | Satu baris dengan alasan cleaning | + alasan |
| transactions_clean | Satu baris barang bersih | + line_revenue, invoice_date |
| returns_lines | Satu baris retur atau batal | line_revenue |
| customers | Satu pelanggan | first_purchase, cohort_month, recency_days, frequency, monetary, r/f/m_score, first_invoice_value |
| cohort_retention | Satu kohort pada satu bulan sesudah pembelian pertama | cohort_month, month_index, cohort_size, active_customers, retention_rate |
| dim_segment | Aturan segmen | segment, rule_ringkas, suggested_action |

## CSV hasil (results/)
Lihat `results/2-analysis/` dan `results/3-presentation/`. Setiap file dihasilkan oleh satu skrip (lihat README bagian Struktur repository).
