# ProcureWise

Web app decision support untuk procurement UMKM. User memasukkan kebutuhan pengadaan, model LightGBM LambdaRank menyusun peringkat vendor, lalu Gemini menjelaskan alasan dan trade-off dari peringkat tersebut. Keputusan akhir tetap ada di tangan user (owner atau admin).

Proyek ini adalah Capstone Project Dicoding Bootcamp Batch 15 (ID grup DB15-I037, learning path Generative AI) untuk use case Firaza UC3: Vendor Recommendation & Procurement Assistant. Firaza adalah UMKM retail hampers dan personalized gifts (handuk, sajadah) yang hampir seluruh penjualannya online.

- **Live URL:** https://procurewise-rouge.vercel.app
- **Dokumentasi API interaktif:** https://procurewise-rouge.vercel.app/docs

## Fitur

- **Kelola vendor, material, dan penawaran.** CRUD lewat web dengan pencarian, sort, paginasi, form dalam modal, dan pesan validasi per field. Vendor dinonaktifkan (soft delete) supaya histori transaksi tetap utuh.
- **Input kebutuhan procurement.** Material, jumlah, tanggal dibutuhkan, prioritas, budget, dan catatan.
- **Peringkat vendor dengan model AI.** Kandidat dicek dulu dengan filter keras (ketersediaan, MOQ, kapasitas, budget). Kandidat yang lolos diberi skor oleh LightGBM LambdaRank dari 16 fitur penawaran, histori, dan konteks.
- **Perbandingan vendor.** Tiga vendor teratas dibandingkan berdampingan dengan nilai terbaik ditandai, ada tabel peringkat lengkap, dan vendor yang gugur tampil beserta alasannya.
- **Faktor model per vendor.** Tiga kontribusi fitur terbesar dari TreeSHAP bawaan LightGBM (`pred_contrib`) ditampilkan dengan arah menaikkan atau menurunkan peringkat.
- **Penjelasan Generative AI.** Gemini menerima JSON terstruktur (request, 3 vendor teratas, metrik, kontribusi fitur, vendor gugur) dan mengembalikan ringkasan, kelebihan dan kekurangan per vendor, trade-off, dan catatan risiko dalam bahasa Indonesia. Setiap angka di output dicek terhadap input.
- **Tahan gagal.** Kalau Gemini gagal, kena limit, atau angkanya tidak cocok setelah satu kali generate ulang, penjelasan memakai template berbasis aturan. Kalau model LightGBM gagal dimuat, peringkat memakai baseline weighted sum dan UI menampilkan label metode cadangan.
- **Responsif** untuk mobile, tablet, dan desktop.

## Arsitektur

```
Browser (React SPA)
   │  Axios + TanStack Query, path relatif /api/v1
   ▼
FastAPI (/api/v1)
   ├── api/        router tipis, validasi Pydantic, envelope response standar
   ├── services/   aturan bisnis dan batas transaksi
   │     ├── ranking_engine       ──► procurewise_ml (filter keras, 16 fitur, LightGBM, fallback weighted sum)
   │     └── explanation_service  ──► Gemini (google-genai), validasi angka, retry, fallback template
   ├── models/     SQLAlchemy async (7 tabel), migrasi Alembic
   └── db/         asyncpg ──► Neon PostgreSQL
```

- **Frontend**: React, Vite, TypeScript, IBM Carbon Design System (`@carbon/react`, `@carbon/styles`, `@carbon/icons-react`), font IBM Plex, Axios, TanStack Query.
- **Backend**: FastAPI, SQLAlchemy async, Alembic, asyncpg, Pydantic.
- **ML**: paket `procurewise_ml` di `ml/` dipakai bersama oleh notebook training dan backend, jadi logika filter dan fitur saat inference sama persis dengan saat training. Model disimpan bersama metadata (versi, urutan fitur, parameter, metrik), dan backend menolak model yang urutan fiturnya berbeda.
- **Generative AI**: Gemini dipanggil hanya dari backend dengan temperature 0,2 dan schema output JSON. API key hanya ada di environment variable. Hasil penjelasan Gemini di-cache di kolom `recommendations.explanation`.
- **Deploy**: satu project Vercel (Services) untuk backend dan frontend di satu domain, database Neon PostgreSQL.

Alur utama: user membuat kebutuhan, lalu `POST /api/v1/recommendations` menjalankan filter keras, fitur, dan model, kemudian menyimpan semua kandidat ke tabel `recommendations`. Halaman detail menampilkan peringkat dan memanggil `POST /api/v1/recommendations/{request_id}/explanation` untuk penjelasan.

## Struktur Repo

```
procurewise/
├── frontend/   React SPA (pages, components, api, hooks, types)
├── backend/    FastAPI (api, schemas, services, models, db), migrasi Alembic, script seed
└── ml/
    ├── generator/        generator data sintetis + validasi constraint
    ├── procurewise_ml/   fitur, filter keras, baseline, evaluasi, ranker
    ├── models/           lgbm_v1.txt dan metadata lgbm_v1.json
    └── notebooks/        01 EDA, 02 baseline, 03 LightGBM
```

## Prasyarat

- Node.js 20 atau lebih baru (dikembangkan dengan Node 24)
- Python 3.14 (3.13 juga didukung)
- PostgreSQL (lokal atau Neon)

## Menjalankan Secara Lokal

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # lalu isi DATABASE_URL dan GEMINI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload
```

Alternatif dengan uv: jalankan `uv sync` dari folder `backend/`. Perintah ini memakai `pyproject.toml` dan `uv.lock`, sekaligus memasang `ml/` sebagai paket `procurewise-ml`. Saat development backend membaca modul `procurewise_ml` dan model langsung dari folder `ml/` di repo.

- Health check: http://localhost:8000/api/v1/health (field `model` menunjukkan model ranking yang aktif)
- Dokumentasi API (Swagger): http://localhost:8000/docs

Untuk mengisi database dengan data sintetis, generate data dulu di `ml/` (lihat bagian ML), lalu dari folder `backend/` jalankan `python scripts/seed.py`. Script ini mengosongkan semua tabel (termasuk `recommendations`) lalu mengisi ulang 6 tabel dalam satu transaksi.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env            # VITE_API_BASE_URL=http://localhost:8000/api/v1
npm run dev
```

Buka http://localhost:5173. Halaman awal adalah daftar kebutuhan procurement.

### ML

```bash
cd ml
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m generator              # generate data sintetis ke ml/data/raw/ (seed default 15037)
```

Notebook dijalankan berurutan: `01_eda.ipynb`, `02_baseline.ipynb`, `03_lightgbm.ipynb`. Spesifikasi generator ada di [ml/README.md](ml/README.md). Kontribusi fitur dihitung langsung dari LightGBM lewat `predict(..., pred_contrib=True)` yang memakai algoritma TreeSHAP bawaan, jadi tidak perlu paket `shap`.

## Dokumentasi API

Semua endpoint ada di bawah prefix `/api/v1` dan terdokumentasi interaktif di `/docs` (Swagger bawaan FastAPI).

| Method | Path | Keterangan |
| --- | --- | --- |
| GET | `/health` | Status aplikasi, database, dan versi model ranking aktif |
| GET | `/vendors` | Daftar vendor, filter pencarian, kategori, dan status aktif |
| POST | `/vendors` | Tambah vendor |
| GET | `/vendors/{id}` | Detail vendor |
| PATCH | `/vendors/{id}` | Ubah sebagian data vendor |
| DELETE | `/vendors/{id}` | Nonaktifkan vendor (soft delete lewat `is_active`) |
| GET | `/materials` | Daftar material |
| POST | `/materials` | Tambah material (kode unik) |
| GET | `/materials/{id}` | Detail material |
| PATCH | `/materials/{id}` | Ubah material |
| DELETE | `/materials/{id}` | Hapus material (409 kalau masih dipakai) |
| GET | `/vendor-offers` | Daftar penawaran vendor (harga, MOQ, lead time, kapasitas) |
| POST | `/vendor-offers` | Tambah penawaran (satu per pasangan vendor dan material) |
| GET | `/vendor-offers/{id}` | Detail penawaran |
| PATCH | `/vendor-offers/{id}` | Ubah penawaran |
| DELETE | `/vendor-offers/{id}` | Hapus penawaran |
| GET | `/procurement-requests` | Daftar kebutuhan, paginasi server (`page`, `page_size`) dan filter status |
| POST | `/procurement-requests` | Buat kebutuhan procurement |
| GET | `/procurement-requests/{id}` | Detail kebutuhan |
| POST | `/recommendations` | Inference API: filter keras dan model ranking untuk `request_id`, hasil disimpan ke database |
| GET | `/recommendations/{request_id}` | Hasil peringkat tersimpan, termasuk vendor gugur dan alasannya |
| POST | `/recommendations/{request_id}/explanation` | Penjelasan Gemini (atau template kalau Gemini gagal) |

Format response sama untuk semua endpoint, termasuk error:

```json
{ "status": 200, "message": "Success", "timestamp": "2026-11-21T15:20:53+07:00", "data": {} }
```

- 422: `message` berbunyi "Data <entitas> tidak valid" dan `data` berisi daftar `{ "field", "error" }` untuk semua field yang gagal
- 404 dan 409: `data` bernilai `null`, pesan 409 menyebut aturan bisnis yang dilanggar
- 503: database atau modul ranking tidak tersedia
- endpoint list yang dipaginasi menambah `meta: { "page", "page_size", "total" }`

## Data dan Model

### Data sintetis

Data Firaza asli tidak tersedia, jadi data dibuat oleh generator sendiri di `ml/generator` (seed utama 15037). Generator meniru perilaku vendor, musim ramai (Ramadan, Syawal, Dzulhijjah), dan hasil pesanan. Spesifikasi lengkap ada di [ml/README.md](ml/README.md).

| Item | Jumlah |
| --- | --- |
| Periode | 1 April 2025 s.d. 30 September 2026 (18 bulan) |
| Material | 15 (5 bahan produk, 5 jasa bordir dan printing, 5 packaging) |
| Vendor | 28 (10 bahan, 9 jasa, 9 packaging) |
| Penawaran vendor | 77 |
| Procurement request | 2.102 (train 1.475, val 397, test 230) |
| Transaksi | 2.050 |
| Kandidat (pasangan request dan vendor) | 9.754, dengan 7.191 kandidat lolos filter keras yang diberi label grade 0 sampai 3 |

Label relevansi dihitung dari simulasi kontrafaktual hasil pesanan tiap kandidat (peluang tepat waktu, perkiraan cacat, biaya efektif) dengan bobot menurut prioritas. Karakter vendor yang dipakai simulasi disimpan terpisah di `_hidden_vendor_traits.csv` dan tidak pernah dipakai sebagai fitur. Split dilakukan berdasarkan waktu (`request_date`): train April 2025 s.d. Maret 2026, val April s.d. Juni 2026, test Juli s.d. September 2026.

### Fitur

| Kelompok | Fitur |
| --- | --- |
| Penawaran | `unit_price`, `price_rel_median`, `total_cost`, `quoted_lead_time_days`, `moq_ratio` |
| Histori vendor | `on_time_rate`, `avg_delay_days`, `defect_rate`, `avg_rating`, `n_transactions`, `days_since_last_order`, `has_history` |
| Konteks request | `slack_days`, `qty_capacity_ratio`, `priority_code`, `is_peak_season` |

Anti leakage: metrik histori hanya dihitung dari transaksi yang hasilnya sudah diketahui sebelum `request_date`. Hal ini dibuktikan lewat uji perturbasi data masa depan di `ml/procurewise_ml/leakage_check.py`.

### Model dan evaluasi

LightGBM LambdaRank (`lgbm-v1`) dilatih di split train. Early stopping dan tuning kecil (12 kombinasi) hanya memakai split val, dan split test hanya dipakai sekali di akhir. Pembanding: weighted sum, TOPSIS, TOPSIS berbobot prioritas, urutan acak, dan pilihan historis. Bobot baseline ditetapkan sebelum evaluasi pertama dan tidak diubah. Detail ada di `ml/notebooks/03_lightgbm.ipynb`.

Hasil di split test, grup informatif (194 grup):

| Metode | NDCG@3 | Hit@1 | MRR | Peringkat 1 tepat waktu |
| --- | --- | --- | --- | --- |
| **LightGBM (lgbm-v1)** | **0,961** | **0,881** | **0,934** | **91,7%** |
| Weighted sum | 0,930 | 0,835 | 0,908 | 90,9% |
| TOPSIS prioritas | 0,925 | 0,804 | 0,897 | 90,7% |
| TOPSIS | 0,901 | 0,773 | 0,871 | 89,8% |
| Acak | 0,750 | 0,392 | 0,634 | 85,2% |
| Pilihan historis | 0,736 | 0,433 | 0,619 | 87,3% |

- Selisih NDCG@3 terhadap weighted sum +0,031 dengan bootstrap CI 95% +0,014 sampai +0,047 (signifikan). Selisih Hit@1 +0,046 dengan CI 0 sampai +0,098, belum signifikan.
- Vendor peringkat 1 LightGBM lebih jarang bergrade 0 (1,4% berbanding 2,8%), tapi biayanya sedikit lebih tinggi (biaya relatif 1,064 berbanding 1,042).
- Per segmen: keunggulan terbesar ada di request dengan sisa waktu ketat (Hit@1 0,788 berbanding 0,673) dan kategori jasa (NDCG@3 0,969 berbanding 0,908). Model kalah di packaging (NDCG@3 0,918 berbanding 0,942, 34 grup).
- Kestabilan: dengan hyperparameter yang sama di 5 seed data lain, LightGBM unggul NDCG@3 di 5 dari 5 seed (rata-rata +0,043) dan Hit@1 di 4 dari 5 seed.
- Fitur paling berpengaruh: `avg_rating`, `slack_days`, dan `price_rel_median`.

## Environment Variable

| Lokasi | Variabel | Keterangan |
| --- | --- | --- |
| `backend/.env` | `DATABASE_URL` | URL Postgres. Format `postgresql://` dan `sslmode=require` dari Neon/Supabase otomatis diubah ke format asyncpg |
| `backend/.env` | `CORS_ORIGINS` | Origin frontend yang diizinkan, dipisah koma |
| `backend/.env` | `ENVIRONMENT` | `development` atau `production` |
| `backend/.env` | `GEMINI_API_KEY` | API key Gemini untuk penjelasan rekomendasi. Kosong berarti penjelasan memakai template |
| `backend/.env` | `GEMINI_MODEL` | Model Gemini, default `gemini-3.5-flash-lite` |
| `backend/.env` | `GEMINI_TIMEOUT_SECONDS` | Batas waktu per percobaan ke Gemini, default 20 detik |
| `frontend/.env` | `VITE_API_BASE_URL` | Base URL backend termasuk prefix `/api/v1` |

File `.env` tidak boleh di-commit. Yang di-commit hanya `.env.example`.

## Deploy

Live URL: https://procurewise-rouge.vercel.app

Frontend dan backend dideploy sebagai satu project Vercel dengan fitur Services (satu domain), diatur oleh `vercel.json` di root repo. Database memakai Neon PostgreSQL.

| Service | Root | Keterangan |
| --- | --- | --- |
| `backend` | `backend/` | FastAPI (`app.main:app`) sebagai fungsi Python. Fungsi hanya berisi folder `backend/`, jadi `ml/` dipasang sebagai paket `procurewise-ml` lewat `[tool.uv.sources]` di `backend/pyproject.toml` (Vercel memasang dependency dengan uv dari file ini dan `uv.lock`). Modul `procurewise_ml` dan file model `lgbm_v1` ikut masuk site-packages |
| `frontend` | `frontend/` | Vite, output `dist`, semua rute diarahkan ke `index.html` supaya rute seperti `/kebutuhan/2103` bisa dibuka langsung |

Rewrite di `vercel.json` mengirim `/api/(.*)` ke service `backend` dan sisanya ke `frontend`. Backend menerima path lengkap, jadi route tetap `/api/v1/...`. Karena satu domain, frontend memanggil API lewat path relatif `/api/v1`.

Di fungsi serverless (env `VERCEL=1` dari Vercel), koneksi database memakai NullPool: koneksi dibuka per request dan ditutup setelahnya. Migrasi dijalankan dari lokal dengan `alembic upgrade head`.

| Environment variable (Vercel, Settings, Environment Variables) | Nilai |
| --- | --- |
| `DATABASE_URL` | URL koneksi Neon |
| `GEMINI_API_KEY` | API key Gemini |
| `GEMINI_MODEL` | model Gemini yang dipakai, contoh `gemini-3.5-flash-lite` |
| `ENVIRONMENT` | `production` |
| `CORS_ORIGINS` | domain project Vercel, contoh `https://procurewise.vercel.app` (tidak wajib karena satu domain) |
| `VITE_API_BASE_URL` | `/api/v1` |

## SBOM (Software Bill of Materials)

Aturan proyek: dependency hanya boleh berlisensi MIT, BSD, atau Apache 2.0. Lisensi GPL, AGPL, LGPL, MPL, dan EPL tidak dipakai sebagai dependency langsung. Daftar di bawah dicek dari metadata paket yang terpasang pada 12 Oktober 2026.

### Backend (`backend/pyproject.toml` dan `backend/requirements.txt`)

Kedua file berisi versi yang sama. `pyproject.toml` beserta `uv.lock` dipakai build Vercel, `requirements.txt` untuk instalasi pip lokal. Paket lokal `procurewise-ml` (folder `ml/`, lisensi MIT sama dengan repo) ikut dipasang lewat `[tool.uv.sources]`.

| Paket | Versi | Lisensi |
| --- | --- | --- |
| fastapi | 0.143.0 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| SQLAlchemy[asyncio] | 2.1.4 | MIT |
| alembic | 1.20.0 | MIT |
| asyncpg | 0.32.0 | Apache-2.0 |
| pydantic | 2.14.1 | MIT |
| pydantic-settings | 2.15.0 | MIT |
| numpy | 2.5.4 | BSD-3-Clause (beberapa komponen 0BSD, MIT, Zlib, CC0) |
| pandas | 3.0.6 | BSD-3-Clause |
| lightgbm | 4.7.0 | MIT |
| google-genai | 3.6.1 | Apache-2.0 |

numpy, pandas, dan lightgbm dipakai untuk inference ranking lewat modul `ml/procurewise_ml`, dengan versi yang sama seperti `ml/requirements.txt`. google-genai adalah SDK resmi Gemini untuk penjelasan rekomendasi dan hanya dipanggil dari backend.

Dependency transitif: annotated-doc (MIT), annotated-types (MIT), anyio (MIT), click (BSD-3-Clause), greenlet (MIT AND PSF-2.0), h11 (MIT), idna (BSD-3-Clause), Mako (MIT), MarkupSafe (BSD-3-Clause), opentelemetry-api (Apache-2.0), pydantic_core (MIT), python-dateutil (BSD-3-Clause), python-dotenv (BSD-3-Clause), scipy (BSD-3-Clause), starlette (BSD-3-Clause), typing-inspection (MIT), typing_extensions (PSF-2.0), tzdata (Apache-2.0).

Dependency transitif dari google-genai: certifi (MPL-2.0), cffi (MIT-0), charset-normalizer (MIT), cryptography (Apache-2.0 OR BSD-3-Clause), distro (Apache-2.0), google-auth (Apache-2.0), httpcore2 (BSD-3-Clause), httpx2 (BSD-3-Clause), pyasn1 (BSD-2-Clause), pyasn1_modules (BSD-2-Clause), pycparser (BSD-3-Clause), requests (Apache-2.0), sniffio (MIT OR Apache-2.0), tenacity (Apache-2.0), truststore (MIT), urllib3 (MIT), websockets (BSD-3-Clause).

Driver PostgreSQL yang dipakai adalah asyncpg (Apache-2.0). psycopg dan psycopg2 sengaja tidak dipakai karena berlisensi LGPL.

### Frontend (`frontend/package.json`)

Dependency runtime (ikut ke bundle aplikasi):

| Paket | Versi | Lisensi |
| --- | --- | --- |
| react | 19.3.0 | MIT |
| react-dom | 19.3.0 | MIT |
| react-is | 19.3.1 | MIT |
| @carbon/react | 1.121.0 | Apache-2.0 |
| @carbon/styles | 1.120.0 | Apache-2.0 |
| @carbon/icons-react | 11.92.0 | Apache-2.0 |
| @tanstack/react-query | 5.104.2 | MIT |
| axios | 1.20.0 | MIT |
| react-router | 7.18.4 | MIT |
| recharts | 3.10.1 | MIT |

Dependency development (hanya dipakai saat build dan pengembangan):

| Paket | Versi | Lisensi |
| --- | --- | --- |
| vite | 8.3.4 | MIT |
| @vitejs/plugin-react | 6.1.2 | MIT |
| sass | 1.108.2 | MIT |
| typescript | 6.0.3 | Apache-2.0 |
| oxlint | 1.87.0 | MIT |
| prettier | 3.9.10 | MIT |
| @types/node | 24.19.2 | MIT |
| @types/react | 19.3.0 | MIT |
| @types/react-dom | 19.3.0 | MIT |

Ringkasan dependency transitif runtime (121 paket): 84 MIT, 11 ISC (paket d3 dari recharts), 10 Apache-2.0 (paket `@carbon/*` dan `@ibm/telemetry-js`), 2 BSD-3-Clause, 1 0BSD, 1 MIT AND ISC, serta paket font IBM Plex (OFL-1.1). Dependency penting dari Carbon: flatpickr (MIT) untuk date picker, downshift (MIT), motion (MIT), dan @floating-ui/react (MIT).

Font (aset tampilan, bukan kode program):

| Paket | Versi | Lisensi |
| --- | --- | --- |
| @ibm/plex-sans | 2.0.0 | OFL-1.1 (font IBM Plex Sans) |
| @ibm/plex-mono | 2.5.0 | OFL-1.1 (font IBM Plex Mono) |

### ML (`ml/requirements.txt`)

| Paket | Versi | Lisensi |
| --- | --- | --- |
| numpy | 2.5.4 | BSD-3-Clause (beberapa komponen 0BSD, MIT, Zlib, CC0) |
| pandas | 3.0.6 | BSD-3-Clause |
| scikit-learn | 1.9.1 | BSD-3-Clause |
| lightgbm | 4.7.0 | MIT |
| plotly | 7.1.0 | MIT |
| nbformat | 5.11.1 | BSD-3-Clause |
| PyYAML | 6.0.3 | MIT |
| nbclient | 0.11.0 | BSD-3-Clause |
| ipykernel | 7.4.0 | BSD-3-Clause |

Dependency transitif ML seluruhnya MIT, BSD, atau Apache-2.0, kecuali typing_extensions (PSF-2.0).

### Catatan Lisensi

- **ISC** (paket d3 dari recharts) adalah lisensi permisif yang secara isi setara dengan MIT dan disetujui OSI.
- **PSF-2.0** (typing_extensions, sebagian greenlet) adalah lisensi permisif non-copyleft. Paket ini wajib untuk pydantic dan SQLAlchemy sehingga tidak bisa dihindari.
- **lightningcss (MPL-2.0)** adalah dependency transitif dari vite 8. Paket ini hanya berjalan saat build, tidak ikut ke bundle aplikasi, dan tidak dimodifikasi.
- Paket lain yang muncul hanya di tool build: caniuse-lite (CC-BY-4.0), isexe dan minimatch (BlueOak-1.0.0), type-fest (MIT OR CC0-1.0). Semuanya tidak ikut ke bundle.
- **Font IBM Plex (OFL-1.1)** dipakai sebagai font antarmuka sesuai Carbon Design System. Lisensi OFL berlaku untuk file font, bukan kode program, dan font dibundel tanpa modifikasi. @carbon/styles juga menarik paket Plex lain (`@ibm/plex`, `@ibm/plex-serif`, varian Arab, Ibrani, Devanagari, Thai) dengan lisensi yang sama.
- **@ibm/telemetry-js (Apache-2.0)** ikut terpasang bersama paket Carbon dan Plex. Skrip postinstall-nya mengirim data pemakaian paket ke IBM. Saat instalasi skrip ini bisa dimatikan dengan environment variable `IBM_TELEMETRY_DISABLED=true`, dan npm versi terbaru tidak menjalankan skrip install tanpa persetujuan.
- Beberapa paket sengaja tidak dipakai karena lisensinya: `shap` (menarik tqdm yang MPL-2.0, diganti TreeSHAP bawaan LightGBM), `matplotlib` (lisensi berbasis PSF, diganti plotly), dan `httpx` untuk testing (menarik certifi yang MPL-2.0).
- **certifi (MPL-2.0)** ikut terpasang sebagai dependency transitif google-genai (lewat requests dan httpx2) untuk daftar sertifikat TLS. Paket ini tidak dimodifikasi dan statusnya masih menunggu konfirmasi Dicoding bersama MPL-2.0 transitif lainnya.
- **cffi (MIT-0)** adalah varian MIT tanpa kewajiban mencantumkan atribusi, jadi lebih longgar dari MIT.

## Keterbatasan

- **LightGBM di runtime serverless Vercel.** Di runtime serverless Vercel LightGBM tidak dapat dimuat (kemungkinan karena library sistem OpenMP `libgomp.so.1` tidak tersedia), sehingga ranking baru di live URL memakai fallback weighted sum. Aplikasi tidak crash: `/api/v1/health` menunjukkan `weighted-sum-fallback` dan UI menampilkan label metode cadangan. Model `lgbm-v1` berjalan normal di lingkungan lokal atau server biasa. Rekomendasi demo #2103 dan #2104 disusun dengan `lgbm-v1`.
- **Pilihan model Gemini.** Model Gemini yang lebih besar butuh waktu lebih dari batas 20 detik untuk prompt berstruktur (output JSON dengan schema), jadi dipilih varian `gemini-3.5-flash-lite`. Kalau Gemini tetap gagal, penjelasan memakai template berbasis aturan dan sumbernya ditandai di panel.
- **Data sepenuhnya sintetis.** Hasil model menunjukkan pendekatan ini bekerja di dunia yang diasumsikan generator, belum membuktikan performa di data asli Firaza.
- **Referensi harga belum dikalibrasi.** Harga, MOQ, dan lead time acuan di `ml/generator/price_reference.yaml` masih perkiraan awal, belum diisi dari listing marketplace (prosedur kalibrasi ada di ml/README.md bagian 17).
- **Musim ramai belum teruji bersih.** Split test (Juli s.d. September 2026) tidak berisi request musim ramai. Model unggul di musim ramai pada split val, tapi val dipakai untuk tuning.
- **Model kalah di kategori packaging** dibanding weighted sum di split test.
- Belum ada autentikasi user. Aplikasi ditujukan untuk owner atau admin Firaza.

## Sumber Data dan Referensi

- **Dataset**: seluruh data adalah data sintetis buatan sendiri dari generator di `ml/generator` (seed 15037), bukan dataset publik. Spesifikasi, asumsi, dan penanda parameter ([ASUMSI], [KALIBRASI], [MP]) dicatat di [ml/README.md](ml/README.md).
- **Referensi harga**: nilai harga, MOQ, dan lead time acuan per material di `ml/generator/price_reference.yaml` masih perkiraan awal dan belum dikalibrasi dari marketplace (lihat bagian Keterbatasan).
- **Library**: semua library beserta versi dan lisensinya dicatat di bagian SBOM.
- **Model AI**: LightGBM LambdaRank (Ke dkk., "LightGBM: A Highly Efficient Gradient Boosting Decision Tree", NeurIPS 2017), dokumentasi https://lightgbm.readthedocs.io. Kontribusi fitur memakai TreeSHAP (Lundberg dkk., 2020) yang sudah ada di LightGBM.
- **Generative AI**: Google Gemini API lewat SDK `google-genai`, dokumentasi https://ai.google.dev/gemini-api/docs.
- **Baseline**: TOPSIS (Hwang dan Yoon, 1981) dan weighted sum sebagai pembanding multi-kriteria.

## Lisensi

[MIT](LICENSE)
