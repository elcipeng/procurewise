# ProcureWise

Web app decision support untuk procurement UMKM. User memasukkan kebutuhan pengadaan, model machine learning menyusun ranking vendor, lalu Gemini menjelaskan alasan dan trade-off dari ranking tersebut. Keputusan akhir tetap ada di tangan user (owner/admin).

Proyek ini adalah Capstone Project Dicoding Bootcamp Batch 15 (ID grup DB15-I037, learning path Generative AI) untuk use case Firaza UC3: Vendor Recommendation & Procurement Assistant.

> Status: tahap setup awal. Belum ada fitur selain endpoint health check.

## Struktur Repo

```
procurewise/
├── frontend/   React + Vite + TypeScript + Tailwind CSS + shadcn/ui
├── backend/    FastAPI + SQLAlchemy (async) + Alembic + asyncpg
└── ml/         Data sintetis, EDA, training, dan evaluasi model ranking
    └── notebooks/
```

## Prasyarat

- Node.js 20 atau lebih baru (dikembangkan dengan Node 24)
- Python 3.14
- PostgreSQL (lokal, Neon, atau Supabase)

## Menjalankan Secara Lokal

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # lalu isi DATABASE_URL
uvicorn app.main:app --reload
```

- Health check: http://localhost:8000/api/v1/health
- Dokumentasi API (Swagger): http://localhost:8000/docs

Migrasi database memakai Alembic (`alembic upgrade head`). URL database dibaca dari `DATABASE_URL`, bukan dari `alembic.ini`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Buka http://localhost:5173. Halaman awal menampilkan status koneksi ke backend.

### ML

```bash
cd ml
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m generator              # generate data sintetis ke ml/data/raw/ (seed default 15037)
```

Spesifikasi dan cara kerja generator data sintetis ada di [ml/README.md](ml/README.md). Notebook disimpan di `ml/notebooks/`. Kontribusi fitur (SHAP) dihitung langsung dari LightGBM lewat `predict(..., pred_contrib=True)` yang memakai algoritma TreeSHAP bawaan, jadi tidak perlu paket `shap`.

## Environment Variable

| Lokasi | Variabel | Keterangan |
| --- | --- | --- |
| `backend/.env` | `DATABASE_URL` | URL Postgres. Format `postgresql://` dan `sslmode=require` dari Neon/Supabase otomatis diubah ke format asyncpg |
| `backend/.env` | `CORS_ORIGINS` | Origin frontend yang diizinkan, dipisah koma |
| `backend/.env` | `ENVIRONMENT` | `development` atau `production` |
| `backend/.env` | `GEMINI_API_KEY` | Disiapkan untuk fitur penjelasan, belum dipakai |
| `frontend/.env` | `VITE_API_BASE_URL` | Base URL backend termasuk prefix `/api/v1` |

File `.env` tidak boleh di-commit. Yang di-commit hanya `.env.example`.

## SBOM (Software Bill of Materials)

Aturan proyek: dependency hanya boleh berlisensi MIT, BSD, atau Apache 2.0. Lisensi GPL, AGPL, LGPL, MPL, dan EPL tidak dipakai sebagai dependency langsung. Daftar di bawah dicek dari metadata paket yang terpasang pada 12 Oktober 2026.

### Backend (`backend/requirements.txt`)

| Paket | Versi | Lisensi |
| --- | --- | --- |
| fastapi | 0.143.0 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| SQLAlchemy[asyncio] | 2.1.4 | MIT |
| alembic | 1.20.0 | MIT |
| asyncpg | 0.32.0 | Apache-2.0 |
| pydantic | 2.14.1 | MIT |
| pydantic-settings | 2.15.0 | MIT |

Dependency transitif: annotated-doc (MIT), annotated-types (MIT), anyio (MIT), click (BSD-3-Clause), greenlet (MIT AND PSF-2.0), h11 (MIT), idna (BSD-3-Clause), Mako (MIT), MarkupSafe (BSD-3-Clause), opentelemetry-api (Apache-2.0), pydantic_core (MIT), python-dotenv (BSD-3-Clause), starlette (BSD-3-Clause), typing-inspection (MIT), typing_extensions (PSF-2.0).

Driver PostgreSQL yang dipakai adalah asyncpg (Apache-2.0). psycopg dan psycopg2 sengaja tidak dipakai karena berlisensi LGPL.

### Frontend (`frontend/package.json`)

Dependency runtime (ikut ke bundle aplikasi):

| Paket | Versi | Lisensi |
| --- | --- | --- |
| react | 19.3.0 | MIT |
| react-dom | 19.3.0 | MIT |
| @tanstack/react-query | 5.104.2 | MIT |
| axios | 1.20.0 | MIT |
| recharts | 3.10.1 | MIT |
| radix-ui | 1.8.0 | MIT |
| class-variance-authority | 0.7.1 | Apache-2.0 |
| cn | 0.4.0 | MIT |
| lucide-react | 1.55.0 | ISC |
| tw-animate-css | 1.4.0 | MIT |

Dependency development (hanya dipakai saat build dan pengembangan):

| Paket | Versi | Lisensi |
| --- | --- | --- |
| vite | 8.3.4 | MIT |
| @vitejs/plugin-react | 6.1.2 | MIT |
| tailwindcss | 4.3.3 | MIT |
| @tailwindcss/vite | 4.3.3 | MIT |
| shadcn | 4.21.4 | MIT |
| typescript | 6.0.3 | Apache-2.0 |
| oxlint | 1.87.0 | MIT |
| @types/node | 24.19.2 | MIT |
| @types/react | 19.3.0 | MIT |
| @types/react-dom | 19.3.0 | MIT |

Ringkasan dependency transitif runtime: 136 MIT, 13 ISC (paket d3 dari recharts dan lucide-react), 1 Apache-2.0, 1 BSD-3-Clause, 1 0BSD.

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
| ipykernel | 7.4.0 | BSD-3-Clause |

Dependency transitif ML seluruhnya MIT, BSD, atau Apache-2.0, kecuali typing_extensions (PSF-2.0).

### Catatan Lisensi

- **ISC** (lucide-react dan paket d3 dari recharts) adalah lisensi permisif yang secara isi setara dengan MIT dan disetujui OSI.
- **PSF-2.0** (typing_extensions, sebagian greenlet) adalah lisensi permisif non-copyleft. Paket ini wajib untuk pydantic dan SQLAlchemy sehingga tidak bisa dihindari.
- **lightningcss (MPL-2.0)** adalah dependency transitif dari vite 8 dan Tailwind CSS v4. Paket ini hanya berjalan saat build, tidak ikut ke bundle aplikasi, dan tidak dimodifikasi.
- Paket lain yang muncul hanya di tool build: caniuse-lite (CC-BY-4.0), isexe dan minimatch (BlueOak-1.0.0), type-fest (MIT OR CC0-1.0). Semuanya tidak ikut ke bundle.
- Beberapa paket sengaja tidak dipakai karena lisensinya: `shap` (menarik tqdm yang MPL-2.0, diganti TreeSHAP bawaan LightGBM), `matplotlib` (lisensi berbasis PSF, diganti plotly), font Geist bawaan preset shadcn (SIL OFL 1.1, diganti font sistem), dan `httpx` untuk testing (menarik certifi yang MPL-2.0).

## Sumber Data dan Referensi

Belum ada. Dataset sintetis dan referensi harga marketplace akan dicatat di bagian ini.

## Lisensi

[MIT](LICENSE)
