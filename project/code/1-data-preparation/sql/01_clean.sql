-- 01_clean.sql: penyaringan baris transaksi (urutan prioritas alasan, satu alasan per baris).
-- Input: tabel raw_union (hasil 01_prepare_raw.py). Output: raw_dedup, transactions_clean, returns_lines, cleaning_reason.

-- Langkah 1: hapus duplikat persis di seluruh 8 kolom (overlap sheet 1-9 Des 2010 dan duplikat lain).
CREATE OR REPLACE TABLE raw_dedup AS
SELECT DISTINCT
    Invoice                    AS invoice,
    StockCode                  AS stock_code,
    Description                AS description,
    CAST(Quantity AS INTEGER)  AS quantity,
    InvoiceDate                AS invoice_ts,
    CAST(Price AS DOUBLE)      AS price,
    CAST("Customer ID" AS BIGINT) AS customer_id,
    Country                    AS country
FROM raw_union;

-- Langkah 2: beri satu alasan per baris (urutan: retur, tanpa ID, kode non-produk, harga nol, qty nol).
CREATE OR REPLACE TABLE cleaning_tagged AS
SELECT *,
    CASE
        WHEN invoice LIKE 'C%'                       THEN 'retur_atau_batal'
        WHEN customer_id IS NULL                     THEN 'customer_id_kosong'
        WHEN stock_code IN (SELECT unnest(['POST','DOT','M','D','S','B','m','C2','BANK CHARGES','ADJUST','AMAZONFEE','PADS','CRUK','TEST001']))
                                                     THEN 'kode_bukan_produk'
        WHEN price <= 0                              THEN 'harga_nol_atau_negatif'
        WHEN quantity <= 0                           THEN 'qty_nol_atau_negatif'
        ELSE 'dipakai'
    END AS alasan
FROM raw_dedup;

-- Tabel log: jumlah baris per alasan (total = jumlah baris setelah dedup).
CREATE OR REPLACE TABLE cleaning_reason AS
SELECT alasan, COUNT(*) AS jumlah_baris
FROM cleaning_tagged
GROUP BY alasan;

-- Langkah 3: transaksi bersih = baris 'dipakai'. line_revenue = quantity * price.
CREATE OR REPLACE TABLE transactions_clean AS
SELECT invoice, stock_code, description, quantity, invoice_ts,
       CAST(invoice_ts AS DATE) AS invoice_date,
       price, customer_id, country,
       quantity * price AS line_revenue
FROM cleaning_tagged
WHERE alasan = 'dipakai';

-- Retur dan batal dicatat terpisah (tidak dipakai di kohort atau RFM).
CREATE OR REPLACE TABLE returns_lines AS
SELECT invoice, stock_code, quantity, invoice_ts, price, customer_id, country,
       quantity * price AS line_revenue
FROM cleaning_tagged
WHERE alasan = 'retur_atau_batal';
