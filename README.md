# Milestone P1M1 — Omnichannel Retail NL-to-SQL Analytics

## 1. Skenario

Anda bekerja sebagai Data Engineer di perusahaan retail omnichannel. Perusahaan
menjual produk melalui beberapa channel, memiliki toko fisik dan channel
digital, menjalankan campaign marketing, serta menerima pembayaran, refund,
return, dan permintaan bantuan pelanggan.

Data perusahaan tidak berasal dari satu sistem yang rapi. Anda akan menerima
data dari beberapa sumber berikut:

- Data operasional customer, order, product, store, promotion, dan channel.
- Event payment, refund, return, customer support, serta aktivitas web/mobile.
- Snapshot inventory harian.
- Data pengeluaran dan atribusi campaign.

Data mentah tersedia melalui Google Drive yang berperan sebagai data lake.
Gunakan link berikut saat dataset dibagikan:

```text
https://drive.google.com/drive/folders/1pJrx8eUprI1Z_CJeQDNbRbelrFzlIshy?usp=sharing
```

Dataset sengaja memiliki masalah yang umum dijumpai dalam sistem produksi:

- Duplicate order dan duplicate event.
- Split payment dan partial refund.
- Event terlambat dan timestamp yang tidak berurutan.
- Timestamp dengan timezone berbeda.
- Missing reference ke customer, product, atau order.
- Negative quantity.
- Perubahan profil customer dan kategori product.
- Order yang dibatalkan tetapi payment-nya sudah captured.
- Inventory snapshot yang hilang.
- Banyak promotion dan campaign yang berpotensi menggandakan fact.

Di sisi lain, perusahaan sudah memiliki NL-to-SQL engine dan UI. Engine hanya
dapat membaca tabel `gold.*`. Jika Bronze, Silver, dan Gold dibangun dengan
tidak tepat, engine dapat menghasilkan analisis yang tampak benar tetapi
sebenarnya salah.

## 2. Tujuan Milestone

Tujuan Anda adalah membangun pipeline data lokal dari data lake sampai ke
analytical Gold layer PostgreSQL:

```text
Google Drive data lake
        ↓
Raw files lokal
        ↓
Bronze PostgreSQL
        ↓
Silver PostgreSQL
        ↓
Gold PostgreSQL
        ↓
NL-to-SQL engine
        ↓
Analisis dan visualisasi melalui UI
```

Anda harus:

1. Mengunduh dan memvalidasi raw data dari Google Drive.
2. Mempertahankan source evidence ke Bronze tanpa mengubah payload asli.
3. Mendesain Silver sebagai tabel typed, normalized, tervalidasi, dan memiliki
   lineage.
4. Membangun Gold dengan schema, grain, dan definisi metric yang sudah tetap.
5. Menambahkan quality checks dan reconciliation yang membuktikan hasil
   pipeline dapat dipercaya.
6. Menjalankan pertanyaan analitik menggunakan engine yang telah disediakan.

Anda tidak perlu membangun ulang LLM, NL-to-SQL engine, UI, Neon database,
atau generator data. Komponen tersebut disediakan sebagai consumer dan alat
verifikasi untuk pipeline Anda.

## 3. Sasaran Pembelajaran

Setelah menyelesaikan milestone ini, Anda diharapkan dapat:

- Mendesain pipeline multi-source dari data lake ke PostgreSQL.
- Memisahkan source preservation, normalization, dan analytical modeling.
- Menangani deduplication secara deterministik.
- Merekonstruksi state dari event payment, refund, return, dan support.
- Memilih versi customer atau product berdasarkan waktu transaksi.
- Menggabungkan inventory dan campaign tanpa menggandakan fakta.
- Menangani record invalid dan missing reference secara eksplisit.
- Menjaga grain Gold table tetap konsisten.
- Membuat quality checks untuk uniqueness, reconciliation, dan business rules.
- Menjelaskan trade-off dan keputusan desain pipeline.

## 4. Kontrak Gold Layer

Gold schema tersedia di `database/schemas/gold.sql`. Jangan mengganti nama
tabel, nama kolom, grain, tipe data, atau arti metric karena schema ini juga
digunakan oleh Neon demo, NL-to-SQL engine, dan benchmark.

| Tabel | Grain | Isi utama |
|---|---|---|
| `gold.order_360` | Satu baris per order | Nilai order, discount, payment, refund, return, promotion, dan status order |
| `gold.customer_daily` | Satu customer per tanggal | Order, unit, revenue, refund, return, support, dan status customer |
| `gold.product_daily` | Satu product per tanggal | Penjualan, revenue, refund unit, inventory, category, dan stockout |
| `gold.channel_campaign_daily` | Satu tanggal, channel, dan campaign | Spend, attributed order/customer, revenue, refund, ROAS, dan conversion |
| `gold.executive_kpis_daily` | Satu tanggal bisnis | Total order, revenue, AOV, refund rate, return rate, repeat rate, stockout rate, dan active customer |

Contoh aturan yang harus konsisten:

- `net_revenue = gross_merchandise_value - discount_amount + shipping_revenue - refunded_amount`.
- `refund_rate` membandingkan order yang memiliki refund selesai dengan order
  yang payment-nya captured.
- `return_rate` menghitung order yang memiliki return event dibandingkan
  dengan resolved order.
- `roas` menghitung attributed net revenue dibagi campaign spend.
- Setiap Gold table harus memiliki grain sesuai kontrak dan tidak boleh
  mengalami fact multiplication.

## 5. Pembagian Tanggung Jawab

### Yang harus Anda bangun

- `database/schemas/bronze.sql`
- `database/schemas/silver.sql`
- `database/schemas/ops.sql`
- `pipelines/bronze/build_bronze.py`
- `pipelines/silver/build_silver.py`
- `pipelines/gold/build_gold.py`
- Quality checks dan reconciliation queries.
- Dokumentasi keputusan transformasi.

### Yang sudah disediakan

- Gold contract di `database/schemas/gold.sql`.
- NL-to-SQL engine dan schema catalog.
- ChatGPT-style UI.
- Test harness dan benchmark.
- Data generator untuk kebutuhan instructor.
- Neon demo Gold-only dengan sample data.

## 6. Data Lake Google Drive

Download seluruh isi folder Google Drive ke `data/raw/`. Struktur lokal harus
menjadi:

```text
data/raw/
├── manifest.json
├── operational/
│   ├── customers.json
│   ├── customer_profiles.json
│   ├── customer_addresses.json
│   ├── products.json
│   ├── product_categories.json
│   ├── stores.json
│   ├── sales_channels.json
│   ├── promotions.json
│   ├── orders.json
│   ├── order_items.json
│   └── order_promotions.json
├── events/
│   ├── payment_events.json
│   ├── refund_events.json
│   ├── return_events.json
│   ├── support_events.json
│   └── web_events.json
├── inventory/
│   └── inventory_snapshots.csv
└── reference/
    ├── campaign_spend.csv
    └── city_reference.json
```

## 7. Arsitektur Pipeline

### Bronze

Bronze menyimpan source evidence yang immutable. Payload asli disimpan dalam
bentuk `JSONB` atau representasi setara, bersama nama file, nomor baris, source
record identifier, checksum, dan ingestion run.

Bronze tidak boleh melakukan business join, deduplication, atau kalkulasi
metric. Record invalid dan duplicate tetap dipertahankan di layer ini.

### Silver

Silver mengubah payload menjadi tabel bertipe dan ter-normalisasi. Terapkan:

- Timestamp normalization ke UTC.
- Deduplication dengan deterministic key.
- Validasi foreign reference.
- Status normalization.
- Rejection untuk quantity negatif atau record invalid.
- Event identity resolution.
- Temporal version selection.
- Lineage ke Bronze.
- Penanganan late-arriving records.

Record yang ditolak harus memiliki alasan di `silver.rejected_records` atau
mekanisme setara yang terdokumentasi.

### Gold

Gold membaca Silver, bukan file mentah secara langsung. Bangun fact dan
aggregate secara terpisah sebelum melakukan join ke promotion, campaign,
inventory, atau event agar tidak terjadi penggandaan nilai.

## 8. Orkestrasi dengan Airflow

Pipeline wajib diorkestrasi menggunakan Airflow. Buat DAG pada file
`dags/dag.py`; file ini menjadi entrypoint utama untuk menjalankan pipeline
Anda. Jangan menjadikan perintah CLI manual sebagai pengganti DAG.

DAG minimal harus memiliki tahapan berikut dengan dependency yang jelas:

```text
validate manifest dan raw files
            ↓
initialize PostgreSQL schemas
            ↓
load Bronze
            ↓
build Silver
            ↓
quality gate
            ↓
build Gold
            ↓
validate Gold dan record pipeline metadata
```

DAG harus:

- Dapat dijalankan ulang tanpa menggandakan data.
- Mengirim `pipeline_run_id` ke setiap layer.
- Menghentikan tahap berikutnya jika quality gate gagal.
- Menyimpan status dan error pipeline pada schema `ops`.
- Menggunakan PostgreSQL lokal sebagai target pipeline.
- Tidak mengunggah Bronze atau Silver ke Neon.

Anda tetap boleh membuat modul Python atau SQL tambahan, tetapi seluruh
pipeline harus dapat ditelusuri dari `dags/dag.py`.

## 9. Menjalankan Agent dengan UV

Untuk menjalankan NL-to-SQL agent dan ChatGPT-style UI, UV sudah cukup.
Docker Compose tidak diperlukan jika agent menggunakan Gold sample di Neon.

### Mode Neon demo

Pastikan `.env` lokal berisi koneksi Neon dan OpenAI API key. File ini hanya
untuk komputer Anda dan tidak boleh di-upload ke GitHub. Jalankan konfigurasi
berikut di terminal PowerShell pertama:

```powershell
uv sync
$env:ANALYTICS_DB_TARGET = "neon"
$env:NL2SQL_PROVIDER = "openai"
$env:OPENAI_API_KEY = "isi_api_key_di_environment_lokal"
uv run uvicorn engine.api.main:app --reload --port 8000
```

Pada terminal kedua, jalankan UI:

```powershell
$env:ENGINE_URL = "http://localhost:8000"
uv run python -m streamlit run ui/app.py --server.port 8501
```

Buka `http://localhost:8501`. UI berkomunikasi dengan agent melalui API dan
tidak mengakses database atau OpenAI secara langsung.

## 10. File yang Wajib Diunggah ke GitHub

Submission hanya perlu berisi artefak implementasi berikut:

```text
submission/
├── dags/
│   └── dag.py
├── database/schemas/
│   ├── bronze.sql
│   ├── silver.sql
│   └── ops.sql
├── pipelines/
│   ├── bronze/build_bronze.py
│   ├── silver/build_silver.py
│   └── gold/build_gold.py
└── evidence/
    ├── airflow_run.png
    └── sample_engine_queries.md
```

`database/schemas/gold.sql` tidak perlu dikumpulkan ulang karena merupakan
schema contract yang sudah diberikan. File berikut juga tidak perlu dikirim:

- `.env` atau `.env.example`.
- `pyproject.toml` atau `requirements.txt`.
- Folder `tests/`.
- `data_contract_notes.md`.
- `architecture.md`.
- `README.md` atau README tambahan.
- Dataset penuh, `.venv`, cache, dan folder `solution/`.

Jangan upload API key atau password database dalam bentuk apa pun.

## 10. Rubrik Penilaian

| Komponen | Bobot | Indikator |
|---|---:|---|
| Bronze ingestion dan source preservation | 15% | Semua input dipertahankan, lineage jelas, append-only/idempotent, manifest tervalidasi |
| Silver normalization dan quality handling | 25% | Tipe data, UTC, deduplication, referential checks, rejection, dan temporal logic benar |
| Gold transformation dan grain | 30% | Lima tabel terisi, grain benar, metric benar, tidak ada fact multiplication |
| Reconciliation dan quality gate | 15% | Pipeline mendeteksi duplikasi, revenue mismatch, refund mismatch, dan broken transformation |
| Airflow orchestration dan reproducibility | 15% | DAG memiliki dependency yang benar, rerunnable, memiliki failure handling, dan mencatat metadata |
| **Total** | **100%** | |


> **Catatan:** Neon hanya berisi sample Gold untuk demo instructor. Pipeline
> peserta harus berjalan di PostgreSQL lokal dan tidak meng-upload Bronze atau
> Silver ke Neon.
