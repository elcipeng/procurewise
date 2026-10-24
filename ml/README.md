# ML ProcureWise

Folder ini berisi generator data sintetis, EDA, preprocessing, training, dan evaluasi model ranking vendor.

Dokumen ini adalah **spesifikasi generator data sintetis**. Spesifikasi ditulis sebelum implementasi supaya asumsi, parameter, dan cara pembuatan label bisa direview dulu. Nilai parameter di dokumen ini sudah disamakan dengan hasil kalibrasi di `generator/config.py`.

## Menjalankan Generator

Dari folder `ml/` dengan virtualenv aktif:

```bash
python -m generator                         # seed default 15037, output ke ml/data/raw/
python -m generator --seed 42 --out data/raw
```

Generator menulis CSV, lalu langsung menjalankan validasi dan mencetak ringkasan (jumlah baris, on-time rate per vendor, sebaran harga, distribusi grade, dan pengecekan kewajaran). Exit code 1 kalau ada constraint DB yang dilanggar. Data belum di-seed ke database.

| Modul | Isi |
| --- | --- |
| `generator/config.py` | Semua parameter, nomor bagian di komentar mengacu ke dokumen ini |
| `generator/price_reference.yaml` | Harga, sebaran harga, MOQ, dan lead time per material (bertanda `# TODO: kalibrasi`) |
| `generator/seasons.py` | Kalender musim ramai dan libur Lebaran |
| `generator/vendors.py` | Vendor, karakter tersembunyi, arketipe, cold start, penawaran |
| `generator/requests.py` | Procurement request dan filter keras |
| `generator/simulation.py` | Simulasi hasil pesanan, dipakai bersama oleh transaksi dan label |
| `generator/transactions.py` | Pemilihan vendor historis dan transaksi |
| `generator/labels.py` | Label relevansi dari simulasi kontrafaktual |
| `generator/schema.py` | Cerminan kolom, enum, dan constraint 7 tabel DB |
| `generator/validate.py` | Validasi constraint DB, konsistensi file, pengecekan kewajaran, ringkasan |

## Daftar Isi

1. [Tujuan dan Prinsip](#1-tujuan-dan-prinsip)
2. [Penanda Parameter](#2-penanda-parameter)
3. [Periode Data dan Split](#3-periode-data-dan-split)
4. [Material](#4-material)
5. [Vendor dan Karakter Tersembunyi](#5-vendor-dan-karakter-tersembunyi)
6. [Penawaran Vendor](#6-penawaran-vendor)
7. [Musim Ramai dan Libur](#7-musim-ramai-dan-libur)
8. [Procurement Request Historis](#8-procurement-request-historis)
9. [Filter Keras](#9-filter-keras)
10. [Pemilihan Vendor Historis](#10-pemilihan-vendor-historis)
11. [Simulasi Hasil Pesanan](#11-simulasi-hasil-pesanan)
12. [Transaksi](#12-transaksi)
13. [Label Relevansi](#13-label-relevansi)
14. [Seed dan Reproducibility](#14-seed-dan-reproducibility)
15. [Output Generator](#15-output-generator)
16. [Pengecekan Kewajaran](#16-pengecekan-kewajaran)
17. [Kalibrasi dari Marketplace](#17-kalibrasi-dari-marketplace)
18. [Batasan](#18-batasan)

## 1. Tujuan dan Prinsip

Generator menghasilkan data yang cukup realistis untuk melatih dan menguji model learning-to-rank, tanpa memakai data asli Firaza.

Prinsip utama:

- **Ada "kebenaran" tersembunyi.** Tiap vendor punya karakter asli (harga, kualitas, keandalan, lead time, kapasitas). Karakter ini menentukan hasil pesanan tapi tidak pernah menjadi fitur model. Model hanya melihat apa yang bisa dilihat Firaza di dunia nyata, yaitu penawaran vendor dan histori transaksi.
- **Penawaran tidak selalu jujur.** Vendor yang kurang andal cenderung menjanjikan lead time lebih pendek dari kemampuan aslinya. Karena itu model perlu belajar dari histori, tidak cukup dari penawaran.
- **Korelasi realistis tapi tidak sempurna.** Harga mahal cenderung berkualitas lebih baik, tapi ada vendor murah-tapi-bagus dan mahal-tapi-sering-telat.
- **Label berasal dari hasil simulasi**, bukan dari rumus skor atas fitur. Label dihitung dari hasil pesanan (tepat waktu atau tidak, biaya, cacat) yang disimulasikan memakai karakter tersembunyi.
- **Reproducible.** Seed tetap, parameter terdokumentasi di satu file konfigurasi, versi library di-pin.

## 2. Penanda Parameter

| Penanda | Arti |
| --- | --- |
| **[MP]** | Wajib diisi dari data harga atau listing marketplace (Tokopedia, Shopee, dll.). Sumbernya dicatat di [bagian 17](#17-kalibrasi-dari-marketplace). |
| **[ASUMSI]** | Nilai awal dari asumsi penulis. Boleh direvisi setelah EDA atau diskusi dengan advisor. |
| **[VERIFIKASI]** | Tanggal atau fakta eksternal yang perlu dicek ulang ke sumber resmi. |
| **[KALIBRASI]** | Disetel setelah generator jalan supaya hasil pengecekan di [bagian 16](#16-pengecekan-kewajaran) masuk target. |

## 3. Periode Data dan Split

| Item | Nilai |
| --- | --- |
| Periode data | 1 April 2025 s.d. 30 September 2026 (18 bulan) |
| Train | 1 April 2025 s.d. 31 Maret 2026 (12 bulan) |
| Validasi | 1 April 2026 s.d. 30 Juni 2026 (3 bulan) |
| Test | 1 Juli 2026 s.d. 30 September 2026 (3 bulan) |
| Target jumlah transaksi | sekitar 2.000 |

Split dilakukan berdasarkan `request_date`. Satu procurement request (satu grup ranking) selalu berada utuh di satu split.

## 4. Material

Ada 15 material, 5 per kategori. Kolom `category` di tabel `materials` memakai nilai `bahan`, `jasa`, dan `packaging`.

### 4.1 Daftar Material

| Kode | Nama | Kategori | Satuan |
| --- | --- | --- | --- |
| B01 | Handuk mandi katun 70x140 cm | bahan | pcs |
| B02 | Handuk muka katun 30x30 cm | bahan | pcs |
| B03 | Sajadah tebal polos | bahan | pcs |
| B04 | Sajadah travel lipat | bahan | pcs |
| B05 | Tasbih kayu 33 butir | bahan | pcs |
| J01 | Jasa bordir nama (maks. 12 karakter) | jasa | pcs |
| J02 | Jasa bordir logo atau motif | jasa | pcs |
| J03 | Jasa sablon DTF | jasa | pcs |
| J04 | Cetak kartu ucapan | jasa | lembar |
| J05 | Cetak stiker label custom | jasa | lembar |
| P01 | Rigid box hampers | packaging | pcs |
| P02 | Kotak duplex lipat | packaging | pcs |
| P03 | Paper bag | packaging | pcs |
| P04 | Tas spunbond (goodie bag) | packaging | pcs |
| P05 | Kertas serut (filler) | packaging | kg |

### 4.2 Parameter per Material

| Kode | Harga referensi (Rp/satuan) | Sebaran harga p25 s.d. p75 | MOQ dasar | Lead time dasar (hari) | Kapasitas mingguan dasar | Qty median per order | Laju order dasar per bulan | Tingkat cacat dasar |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01 | **[MP]** | **[MP]** | 24 **[MP]** | 7 **[MP]** | 300 | 100 | 9 | 2,0% |
| B02 | **[MP]** | **[MP]** | 50 **[MP]** | 7 **[MP]** | 500 | 200 | 7 | 2,0% |
| B03 | **[MP]** | **[MP]** | 20 **[MP]** | 7 **[MP]** | 250 | 80 | 8 | 2,0% |
| B04 | **[MP]** | **[MP]** | 24 **[MP]** | 8 **[MP]** | 200 | 60 | 5 | 2,0% |
| B05 | **[MP]** | **[MP]** | 100 **[MP]** | 5 **[MP]** | 800 | 200 | 4 | 2,0% |
| J01 | **[MP]** | **[MP]** | 12 **[MP]** | 5 **[MP]** | 250 | 100 | 8 | 3,0% |
| J02 | **[MP]** | **[MP]** | 24 **[MP]** | 7 **[MP]** | 200 | 80 | 4 | 3,0% |
| J03 | **[MP]** | **[MP]** | 12 **[MP]** | 4 **[MP]** | 400 | 100 | 4 | 3,0% |
| J04 | **[MP]** | **[MP]** | 100 **[MP]** | 3 **[MP]** | 2.000 | 300 | 5 | 1,5% |
| J05 | **[MP]** | **[MP]** | 100 **[MP]** | 3 **[MP]** | 3.000 | 500 | 3 | 1,5% |
| P01 | **[MP]** | **[MP]** | 50 **[MP]** | 10 **[MP]** | 250 | 100 | 6 | 1,5% |
| P02 | **[MP]** | **[MP]** | 100 **[MP]** | 7 **[MP]** | 800 | 200 | 5 | 1,5% |
| P03 | **[MP]** | **[MP]** | 100 **[MP]** | 7 **[MP]** | 800 | 200 | 4 | 1,5% |
| P04 | **[MP]** | **[MP]** | 50 **[MP]** | 6 **[MP]** | 500 | 150 | 4 | 1,5% |
| P05 | **[MP]** | **[MP]** | 1 **[MP]** | 3 **[MP]** | 60 | 10 | 4 | 1,0% |

Keterangan kolom:

- **Harga referensi** adalah median harga grosir untuk pembelian sekitar qty median. Dipakai sebagai harga dasar semua vendor.
- **Sebaran harga** dipakai untuk mengkalibrasi variasi `price_level` antar vendor (lihat [bagian 5.2](#52-distribusi-karakter-tersembunyi)).
- **MOQ dasar** dan **lead time dasar** sudah diberi nilai awal **[ASUMSI]** supaya spesifikasi bisa dibaca utuh, tapi tetap harus dicocokkan dengan listing marketplace (MOQ grosir dan masa pre-order). Lead time dasar sudah termasuk pengiriman.
- **Kapasitas mingguan dasar**, **qty median**, **laju order dasar**, dan **tingkat cacat dasar** adalah **[ASUMSI]**.
- Total laju order dasar adalah 80 order per bulan. Setelah dikali efek musim ramai (rata-rata sekitar 1,4x), totalnya sekitar 2.000 order dalam 18 bulan. Laju dasar disetel ulang **[KALIBRASI]** kalau total meleset.

## 5. Vendor dan Karakter Tersembunyi

### 5.1 Jumlah dan Jenis Vendor

Total 28 vendor.

| Kategori | Jenis vendor | Jumlah | Material yang ditawarkan |
| --- | --- | --- | --- |
| bahan | Pabrik/grosir handuk | 4 | B01, B02 |
| bahan | Grosir sajadah | 2 | B03, B04 |
| bahan | Grosir perlengkapan muslim | 4 | B03, B04, B05, kadang B02 |
| jasa | Konveksi bordir | 4 | J01, J02, kadang J03 |
| jasa | Percetakan | 5 | J04, J05, kadang J03 |
| packaging | Produsen box | 4 | P01, P02 |
| packaging | Grosir packaging | 5 | P02, P03, P04, P05 |

Material bertanda "kadang" ditawarkan dengan peluang 50% **[ASUMSI]**. Setelah penawaran dibuat, generator mengecek bahwa **setiap material punya minimal 4 vendor penawar**. Kalau kurang, ditambahkan penawaran dari vendor sekategori yang dipilih acak sampai jumlahnya cukup. Tujuannya supaya setiap grup ranking punya kandidat yang cukup.

Atribut publik vendor (masuk tabel `vendors`):

- `name`: nama fiktif, dibuat dari kombinasi kata umum (contoh pola: "CV Sinar Tekstil", "Percetakan Mitra Jaya"). Tidak boleh memakai nama usaha asli.
- `city` **[ASUMSI]**: diambil acak berbobot dari kota sentra industri yang sesuai jenisnya. Handuk dan tekstil dari Bandung, Majalaya, Pekalongan, Solo. Bordir dari Tasikmalaya dan Bandung. Percetakan dan packaging dari Jakarta, Tangerang, Bekasi, Surabaya, Yogyakarta.
- `contact`: nomor dan email fiktif dengan domain `example.com`.
- `payment_terms`: `cash` 40%, `dp_50` 40%, `tempo_14` 15%, `tempo_30` 5% **[ASUMSI]**. Hanya informasi, tidak memengaruhi simulasi.
- `is_active`: `true` untuk semua vendor di akhir periode.
- `onboard_date` (hanya di data generator, tidak masuk tabel): 25 vendor aktif sejak 1 April 2025. 3 vendor (1 per kategori) baru bergabung pada tanggal acak antara 1 April 2026 dan 31 Agustus 2026. Ketiganya menjadi kasus **cold start** di periode validasi dan test.

### 5.2 Distribusi Karakter Tersembunyi

Lima karakter dibangkitkan bersama memakai Gaussian copula. Pertama dibangkitkan vektor `z = (z_p, z_q, z_r, z_l, z_c)` dari distribusi normal multivariat dengan mean 0, varians 1, dan matriks korelasi `R`. Setelah itu tiap komponen diubah ke skala aslinya.

Matriks korelasi `R` **[ASUMSI]** (urutan: harga, kualitas, keandalan, lead time, kapasitas):

|  | z_p | z_q | z_r | z_l | z_c |
| --- | --- | --- | --- | --- | --- |
| z_p (harga) | 1,00 | 0,45 | 0,15 | 0,10 | -0,30 |
| z_q (kualitas) | 0,45 | 1,00 | 0,30 | 0,15 | 0,00 |
| z_r (keandalan) | 0,15 | 0,30 | 1,00 | -0,30 | 0,15 |
| z_l (lead time) | 0,10 | 0,15 | -0,30 | 1,00 | -0,35 |
| z_c (kapasitas) | -0,30 | 0,00 | 0,15 | -0,35 | 1,00 |

Matriks ini sudah dicek positive definite (eigenvalue terkecil 0,378). Logikanya: barang mahal cenderung lebih bagus, vendor andal cenderung lebih cepat, vendor besar cenderung lebih murah dan lebih cepat, dan kualitas tinggi butuh pengerjaan sedikit lebih lama.

Transformasi ke skala asli (`Phi` adalah CDF normal standar):

| Karakter | Rumus | Rentang | Arti |
| --- | --- | --- | --- |
| `price_level` | `clip(exp(sigma_p * z_p), 0.70, 1.40)` | 0,70 s.d. 1,40 | Pengali harga terhadap harga referensi material |
| `true_quality` | `0.35 + 0.60 * Phi(z_q)` | 0,35 s.d. 0,95 | Memengaruhi tingkat cacat dan rating |
| `true_reliability` | `0.30 + 0.65 * Phi(z_r)` | 0,30 s.d. 0,95 | Memengaruhi variasi lead time, peluang gangguan, kejujuran janji lead time, dan pembatalan |
| `lead_time_factor` | `exp(0.25 * z_l)` | sekitar 0,6 s.d. 1,6 | Pengali lead time dasar material |
| `capacity_factor` | `exp(0.50 * z_c)` | sekitar 0,37 s.d. 2,7 | Pengali kapasitas mingguan dasar material |

`sigma_p` default 0,15 **[ASUMSI]**. Setelah data marketplace terkumpul, nilainya diganti dengan median dari `ln(p75 / p25) / 1,349` semua material **[MP]**. Rumus ini mengubah rentang antar-kuartil harga marketplace menjadi simpangan baku log-harga.

Karakter dibangkitkan **per vendor**, berlaku sama untuk semua material yang ditawarkan vendor tersebut.

### 5.3 Arketipe Wajib

Supaya korelasi tidak sempurna dan ada kasus yang menarik untuk dievaluasi, setelah sampling beberapa vendor dipaksa masuk arketipe tertentu dengan mengganti nilai z-nya. Vendor dipilih acak dari kategori yang berbeda-beda.

| Arketipe | Jumlah | Override |
| --- | --- | --- |
| Murah tapi bagus | 2 | `z_p = -1,2`, `z_q = +1,2`, `z_r = +0,8` |
| Mahal tapi sering telat | 2 | `z_p = +1,3`, `z_q = +0,5`, `z_r = -1,3` |
| Murah dan buruk | 1 | `z_p = -1,3`, `z_q = -1,3` |
| Kecil tapi andal | 1 | `z_c = -1,2`, `z_r = +1,2` |

Daftar vendor beserta arketipenya disimpan di file karakter tersembunyi supaya bisa dicek saat evaluasi.

## 6. Penawaran Vendor

Untuk setiap pasangan vendor dan material yang ditawarkan:

```
unit_price_dasar   = harga_referensi[m] * price_level[v] * LogNormal(0, 0.05)
moq                = MOQ_dasar[m] * pilih({0.5, 1, 2}, peluang {0.3, 0.5, 0.2})
lead_time_asli     = lead_time_dasar[m] * lead_time_factor[v]
quoted_lead_time   = round(lead_time_asli * (0.95 + 0.65 * true_reliability[v]))
weekly_capacity    = round(kapasitas_dasar[m] * capacity_factor[v])
```

Poin penting ada di `quoted_lead_time`. `lead_time_asli` adalah lead time median, padahal pengiriman aktual masih ditambah noise dan gangguan (bagian 11). Vendor dengan keandalan 0,95 memberi buffer besar (janji sekitar 1,57 kali median), sedangkan vendor dengan keandalan 0,30 hanya sekitar 1,15 kali median walaupun variasinya paling besar. Jadi vendor yang kurang andal terlihat lebih cepat di penawaran dan lebih sering telat. Konstanta 0,95 dan 0,65 adalah hasil **[KALIBRASI]** supaya tingkat tepat waktu keseluruhan masuk target bagian 16. Nilai awal 0,70 dan 0,35 menghasilkan tepat waktu hanya 24%.

Harga dan lead time berubah sedikit mengikuti waktu. Snapshot penawaran pada tanggal `t` dihitung dari nilai dasar di atas:

```
unit_price(t)        = unit_price_dasar * (1 + 0.003)^(bulan sejak awal) * (1 + 0.05 * s(t))
quoted_lead_time(t)  = round(quoted_lead_time * (1 + 0.15 * s(t)))
is_available(t)      ~ Bernoulli(0.95 - 0.10 * s(t))
```

- Inflasi 0,3% per bulan **[ASUMSI]**.
- `s(t)` adalah intensitas musim ramai (lihat [bagian 7](#7-musim-ramai-dan-libur)). Saat musim ramai, vendor menaikkan harga sekitar 5% dan menambah janji lead time 15%. Kenaikan janji ini lebih kecil dari efek musim ramai yang sebenarnya, jadi keterlambatan tetap meningkat.
- Harga dibulatkan ke Rp100 untuk harga di atas Rp5.000 dan ke Rp50 untuk sisanya.

Tabel `vendor_offers` di database diisi dengan snapshot per 30 September 2026. `updated_at` diambil acak dalam 60 hari terakhir. Vendor cold start hanya punya penawaran sejak `onboard_date`.

## 7. Musim Ramai dan Libur

Intensitas musim ramai `s(t)` bernilai 0 sampai 1 per tanggal. Semua tanggal Hijriah bersifat **[VERIFIKASI]** dan perlu dicocokkan dengan kalender resmi Kemenag. Intensitas tiap periode adalah **[ASUMSI]**.

| Periode | Rentang tanggal | s(t) | Alasan |
| --- | --- | --- | --- |
| Libur Lebaran 2025 | 1 s.d. 6 April 2025 | libur | Idul Fitri 1446 H sekitar 31 Maret 2025 |
| Musim nikah Syawal | 7 April s.d. 27 Mei 2025 | 0,5 | Banyak pernikahan setelah Lebaran |
| Musim nikah Dzulhijjah | 28 Mei s.d. 25 Juni 2025 | 0,4 | Sekitar Idul Adha 1446 H (6 Juni 2025) |
| Akhir tahun | 1 November s.d. 20 Desember 2025 | 0,6 | Hampers Natal dan tahun baru, musim nikah akhir tahun |
| Menjelang Ramadan | 5 Januari s.d. 17 Februari 2026 | naik linear 0,3 ke 1,0 | Persiapan hampers Ramadan |
| Ramadan | 18 Februari s.d. 15 Maret 2026 | 1,0 | Puncak permintaan hampers Lebaran |
| Libur Lebaran 2026 | 16 s.d. 27 Maret 2026 | libur | Idul Fitri 1447 H sekitar 20 Maret 2026 |
| Musim nikah Syawal | 28 Maret s.d. 15 Mei 2026 | 0,5 | Banyak pernikahan setelah Lebaran |
| Musim nikah Dzulhijjah | 18 Mei s.d. 15 Juni 2026 | 0,4 | Sekitar Idul Adha 1447 H (27 Mei 2026) |
| Di luar periode di atas | | 0 | Normal |

Efek musim ramai:

| Efek | Rumus |
| --- | --- |
| Permintaan | laju order dikali `1 + 1,5 * s(t)` |
| Qty per order | median qty dikali `1 + 0,5 * s(t)` |
| Lead time asli | dikali `1 + 0,35 * s(t)` |
| Kapasitas efektif | dibagi `1 + 0,4 * s(t)` (vendor juga melayani pelanggan lain) |
| Peluang gangguan | ditambah `0,08 * s(t)` |
| Tingkat cacat | dikali `1 + 0,4 * s(t)` (pengerjaan terburu-buru) |

Efek libur Lebaran:

- Tidak ada request baru selama periode libur (Firaza juga libur).
- Vendor berhenti produksi. Kalau rentang produksi sebuah pesanan beririsan dengan periode libur, jumlah hari yang beririsan ditambahkan ke lead time.
- `s(t)` selama libur dianggap 0 untuk efek lain.

## 8. Procurement Request Historis

Setiap order historis Firaza diawali satu procurement request. Request ini menjadi satu grup ranking.

### 8.1 Waktu Request

Untuk tiap material `m`, request dibangkitkan dengan proses Poisson harian dengan laju `laju_dasar[m] / 26 * (1 + 1,5 * s(t))`. Hari Minggu dan periode libur Lebaran tidak menghasilkan request **[ASUMSI]**. Pembagi 26 (jumlah hari kerja per bulan) dipakai supaya hari Minggu yang dilewati tidak mengurangi volume bulanan.

### 8.2 Atribut Request

| Atribut | Cara membangkitkan |
| --- | --- |
| `request_date` | Tanggal hasil proses Poisson di bagian 8.1. Disimpan di kolom `procurement_requests.request_date` dan menjadi acuan `slack_days` serta cutoff anti leakage. `created_at` hanya untuk audit |
| `qty` | `LogNormal(ln(qty_median[m] * (1 + 0,5 * s(t))), 0,6)`, dibulatkan ke kelipatan 10 (kelipatan 1 untuk satuan kg), minimal 10 (minimal 1 untuk kg) |
| Tingkat urgensi | 25% ketat, 50% normal, 25% santai **[ASUMSI]** |
| `needed_by` | `request_date + round(lead_time_dasar[m] * u + 7 * max(0, qty / kapasitas_dasar[m] - 1))`. Nilai `u` diambil dari Uniform(1,1, 1,5) untuk ketat, Uniform(1,5, 2,2) untuk normal, dan Uniform(2,2, 3,5) untuk santai **[KALIBRASI]**. Rentang awal 0,6 s.d. 1,0 untuk ketat membuat hampir semua kandidat telat sehingga grup tidak memberi sinyal ranking |
| `priority` | Bergantung urgensi (tabel di bawah) |
| `max_budget` | Dengan peluang 70%: `qty * harga_pasar[m](t) * Uniform(1,05, 1,45)`, dibulatkan ke Rp1.000. `harga_pasar` adalah harga referensi setelah inflasi dan kenaikan musim ramai (rumus `unit_price(t)` di bagian 6 tanpa `price_level`). Sisanya kosong (tanpa batas) **[KALIBRASI]** |
| `notes` | Kosong atau kalimat template pendek, misalnya "untuk pesanan hampers corporate" |
| `created_by` | Acak dari user seed (1 owner, 1 admin) |
| `status` | `completed` untuk semua request historis |

Peluang `priority` (nilai: `high`, `normal`, `low`) **[ASUMSI]**:

| Urgensi | high | normal | low |
| --- | --- | --- | --- |
| Ketat | 70% | 25% | 5% |
| Normal | 20% | 60% | 20% |
| Santai | 5% | 35% | 60% |

`priority` menyatakan seberapa penting ketepatan waktu dibanding biaya. Nilai ini dipakai sebagai fitur dan juga untuk menentukan bobot label ([bagian 13](#13-label-relevansi)).

### 8.3 Kandidat

Kandidat sebuah request adalah semua vendor yang menawarkan material tersebut dan sudah aktif pada `request_date`. Untuk setiap kandidat disimpan snapshot penawaran pada tanggal request (harga, MOQ, janji lead time, kapasitas, ketersediaan).

## 9. Filter Keras

Sebelum ranking, kandidat disaring dengan aturan berikut. Kandidat yang gugur tetap disimpan beserta alasannya supaya bisa ditampilkan di aplikasi sebagai "tidak memenuhi".

| Kode alasan | Kondisi gugur |
| --- | --- |
| `tidak_tersedia` | `is_available = false` |
| `moq_lebih_besar` | `moq > qty` |
| `kapasitas_kurang` | `qty > weekly_capacity * max(1, (needed_by - request_date) / 7)` |
| `melebihi_budget` | `max_budget` terisi dan `unit_price * qty > max_budget` |

Satu kandidat bisa punya lebih dari satu alasan. Request dengan kurang dari 2 kandidat lolos tetap menghasilkan transaksi (kalau ada 1 kandidat), tapi tidak dipakai sebagai grup training ranking.

Filter ini sama persis dengan filter yang nanti dipakai di backend.

## 10. Pemilihan Vendor Historis

Transaksi historis mencerminkan pilihan Firaza di masa lalu, yang tidak selalu optimal. Kebijakan pemilihan ini sengaja dibuat sederhana dan bias ke harga murah dan vendor langganan.

Di antara kandidat yang lolos filter:

```
skor_pilih[v] = -1.5 * z_harga[v] + 0.4 * ln(1 + jumlah_order_sebelumnya[v]) + Gumbel(0, 1)
```

- `z_harga` adalah z-score harga penawaran di dalam grup.
- Dengan peluang 15% vendor dipilih acak seragam (eksplorasi) **[ASUMSI]**.
- Bobot vendor langganan 0,4 adalah hasil **[KALIBRASI]**. Dengan bobot awal 0,8, Firaza terkunci di beberapa vendor murah sampai satu vendor mendapat sekitar 19% dari semua order.
- Vendor dengan skor tertinggi dipilih.

Dampaknya:

- Vendor murah yang kurang andal tetap sering dipilih, jadi kelemahannya terlihat di histori.
- Vendor bagus yang jarang dipilih punya histori sedikit. Ini realistis dan menjadi tantangan untuk model.
- Pilihan historis **tidak** dipakai sebagai label.

## 11. Simulasi Hasil Pesanan

Fungsi simulasi menerima `(vendor, material, qty, order_date, snapshot penawaran, s(t))` dan menghasilkan satu kemungkinan hasil pesanan. Fungsi yang sama dipakai untuk membuat transaksi historis ([bagian 12](#12-transaksi)) dan label ([bagian 13](#13-label-relevansi)).

### 11.1 Tanggal Dijanjikan

Vendor menjanjikan tanggal berdasarkan janji lead time dan kapasitas nominal (bukan kapasitas efektif saat musim ramai):

```
promised_date = order_date + quoted_lead_time(t) + 7 * max(0, ceil(qty / weekly_capacity) - 1)
```

### 11.2 Lead Time Aktual

```
kapasitas_efektif = weekly_capacity / (1 + 0.4 * s(t))
beban             = qty / kapasitas_efektif
hari_produksi     = lead_time_asli * (1 + 0.35 * s(t)) + 7 * max(0, beban - 1)
noise             = LogNormal(0, 0.08 + 0.25 * (1 - true_reliability))
gangguan          = Bernoulli(0.02 + 0.20 * (1 - true_reliability) + 0.08 * s(t)) * Gamma(shape 2, scale 3)
hari_total        = hari_produksi * noise + gangguan + hari_libur_beririsan
delivered_date    = order_date + ceil(hari_total)
```

- **Efek kapasitas.** Setiap kelebihan satu minggu kapasitas efektif menambah sekitar 7 hari. Vendor kecil yang menerima order besar di musim ramai akan terlambat.
- **Gangguan** (bahan baku telat, mesin rusak, kurir bermasalah) menambah rata-rata 6 hari. Peluangnya sekitar 3% untuk vendor sangat andal dan sekitar 16% untuk vendor paling tidak andal, ditambah efek musim.
- **Keterlambatan** dihitung sebagai `delay_days = delivered_date - promised_date`. Pesanan tepat waktu kalau `delay_days <= 0`.

### 11.3 Cacat

```
p_cacat = cacat_dasar[m] * exp(3.5 * (0.60 - true_quality)) * (1 + 0.4 * s(t)) * (1 + 0.5 * [beban > 1])
p_cacat = min(p_cacat, 0.30)
p_draw  ~ Beta(60 * p_cacat, 60 * (1 - p_cacat))
qty_defect ~ Binomial(qty, p_draw)
```

Untuk bahan dengan cacat dasar 2%, vendor berkualitas 0,95 menghasilkan sekitar 0,6% cacat dan vendor berkualitas 0,35 sekitar 4,8%. Pivot 0,60 adalah hasil **[KALIBRASI]** (awalnya 0,65, rata-rata cacat 4,3%). Distribusi Beta menambah variasi antar pesanan supaya tidak terlalu mulus. Faktor `beban > 1` mewakili pesanan yang dikerjakan terburu-buru karena melebihi kapasitas.

### 11.4 Rating Kualitas

Rating 1 sampai 5 diberikan admin Firaza setelah barang diterima:

```
rating_latent  = 1.8 + 3.0 * true_quality - 10 * (qty_defect / qty) - 0.12 * max(0, delay_days) + Normal(0, 0.45)
quality_rating = clip(round(rating_latent), 1, 5)
```

Kualitas 0,35 s.d. 0,95 menghasilkan rating dasar sekitar 2,9 s.d. 4,7. Koefisien awal (1,2, 3,6, dan 25) membuat rata-rata rating banyak vendor di bawah 2 sehingga diubah **[ASUMSI]**. Rating bergantung pada kualitas asli dan juga pada pengalaman (cacat dan telat). Jadi rating adalah sinyal yang berisik, bukan salinan `true_quality`.

### 11.5 Pembatalan

Dengan peluang `0.01 + 0.04 * (1 - true_reliability)` pesanan dibatalkan vendor. Pesanan batal tidak punya `delivered_date`, `qty_defect`, dan `quality_rating`.

## 12. Transaksi

Untuk setiap request historis yang punya minimal 1 kandidat lolos:

1. Vendor dipilih dengan kebijakan di [bagian 10](#10-pemilihan-vendor-historis).
2. `order_date = request_date`.
3. `unit_price = unit_price(t) * LogNormal(0, 0.03)` (sedikit negosiasi), dibulatkan seperti di bagian 6.
4. Hasil pesanan disimulasikan **satu kali** dengan fungsi di [bagian 11](#11-simulasi-hasil-pesanan).
5. `status`:
   - `cancelled` kalau batal,
   - `in_progress` kalau `delivered_date` jatuh setelah 30 September 2026 (dalam hal ini `delivered_date`, `qty_defect`, dan `quality_rating` dikosongkan),
   - `completed` untuk sisanya.

Jumlah order sebelumnya per vendor (untuk kebijakan pemilihan) diperbarui setiap kali transaksi dibuat, sehingga request diproses berurutan menurut tanggal.

**Aturan anti leakage untuk fitur histori** (dipakai di tahap preprocessing, ditulis di sini supaya generator menyimpan kolom yang dibutuhkan):

- Metrik yang butuh hasil (`on_time_rate`, `avg_delay_days`, `defect_rate`, `avg_rating`) hanya dihitung dari transaksi `completed` dengan `delivered_date < request_date`.
- `n_transactions` dan `days_since_last_order` dihitung dari transaksi dengan `order_date < request_date`.
- Vendor tanpa histori selesai memakai nilai rata-rata kategori dari periode sebelum `request_date` dan diberi flag `data_terbatas = true`.

## 13. Label Relevansi

Label adalah grade 0 sampai 3 untuk setiap kandidat yang lolos filter di setiap grup. Label dihitung dari **hasil pesanan yang disimulasikan** memakai karakter tersembunyi vendor, bukan dari fitur yang dilihat model.

### 13.1 Simulasi Kontrafaktual

Untuk setiap kandidat lolos, hasil pesanan disimulasikan **K = 30 kali** dengan fungsi di bagian 11 dan aliran random terpisah dari transaksi. Simulasi berulang dipakai karena satu kali simulasi terlalu berisik untuk dijadikan label. Dari 30 hasil dihitung:

| Ukuran | Definisi |
| --- | --- |
| `p_tepat` | Proporsi simulasi dengan `delivered_date <= needed_by`. Simulasi yang batal dihitung tidak tepat |
| `e_cacat` | Rata-rata `qty_defect / qty` dari simulasi yang tidak batal |
| `e_biaya` | `unit_price * qty + rata-rata(qty_defect) * unit_price`. Barang cacat dianggap harus dibeli ulang |

Perhatikan bahwa ketepatan diukur terhadap `needed_by` (kebutuhan Firaza), bukan terhadap `promised_date` (janji vendor).

### 13.2 Aturan Grade

**Langkah 1, gugur hasil.** Grade 0 kalau `p_tepat < 0,5` atau `e_cacat > 0,08`.

**Langkah 2, skor hasil.** Untuk kandidat lainnya:

```
skor_waktu   = p_tepat
skor_cacat   = 1 - min(1, e_cacat / 0.08)
skor_biaya   = min(e_biaya di grup) / e_biaya
skor_hasil   = w_waktu * skor_waktu + w_cacat * skor_cacat + w_biaya * skor_biaya
```

`min(e_biaya di grup)` diambil dari kandidat lolos di grup yang sama.

Bobot menurut `priority` **[ASUMSI]**:

| priority | w_waktu | w_cacat | w_biaya |
| --- | --- | --- | --- |
| high | 0,60 | 0,25 | 0,15 |
| normal | 0,40 | 0,30 | 0,30 |
| low | 0,25 | 0,30 | 0,45 |

**Langkah 3, grade.**

| Grade | Kondisi |
| --- | --- |
| 3 | `skor_hasil >= 0,90` |
| 2 | `0,76 <= skor_hasil < 0,90` |
| 1 | `skor_hasil < 0,76` |

Ambang 0,90 dan 0,76 adalah hasil **[KALIBRASI]** (nilai awal 0,85 dan 0,70). Ambang disetel sekali sampai distribusi grade mendekati target di [bagian 16](#16-pengecekan-kewajaran), lalu dibekukan sebelum training dimulai.

### 13.3 Kenapa Ini Bukan "Rumus Skor"

Rumus di langkah 2 bekerja di atas **hasil sebenarnya** (peluang tepat waktu, cacat aktual, biaya aktual) yang tidak bisa dilihat saat keputusan dibuat. Baseline weighted sum dan TOPSIS, sebaliknya, bekerja di atas **fitur yang terlihat** (harga penawaran, janji lead time, metrik histori). Model dinilai dari seberapa baik ia menebak hasil sebenarnya dari informasi yang terlihat. Model tidak meniru rumus label karena input rumus label tidak tersedia baginya.

### 13.4 Hasil untuk Evaluasi Bisnis

`p_tepat`, `e_cacat`, dan `e_biaya` per kandidat ikut disimpan di file kandidat. Dengan begitu metrik bisnis vendor peringkat 1 (tingkat tepat waktu, tingkat cacat, biaya) bisa dihitung untuk model maupun baseline, walaupun vendor tersebut tidak dipilih di histori.

### 13.5 Set Skenario Urgent vs Santai

Generator juga bisa membuat set skenario tambahan di periode test. Untuk beberapa kombinasi material dan qty, dibuat dua versi request yang identik kecuali `needed_by` dan `priority`:

- versi urgent: `u = 0,7`, `priority = high`
- versi santai: `u = 3,0`, `priority = low`

Set ini tidak masuk transaksi. Gunanya hanya untuk menguji apakah ranking berubah sesuai konteks.

## 14. Seed dan Reproducibility

- Seed utama: `DEFAULT_SEED = 15037` (Batch 15, grup I037). Bisa diganti lewat `--seed`.
- Generator memakai `numpy.random.SeedSequence(seed).spawn(7)` lalu memberi satu `Generator` (PCG64) untuk setiap komponen, dengan urutan tetap:

| Urutan | Komponen |
| --- | --- |
| 0 | Vendor dan karakter tersembunyi |
| 1 | Penawaran |
| 2 | Waktu dan atribut request |
| 3 | Ketersediaan snapshot penawaran |
| 4 | Pemilihan vendor historis |
| 5 | Simulasi transaksi |
| 6 | Simulasi label dan set skenario |

Dengan aliran terpisah, mengubah satu komponen (misalnya K pada label) tidak menggeser angka acak komponen lain.

- Parameter disimpan di `generator/config.py`, sedangkan harga, MOQ, dan lead time di `generator/price_reference.yaml`. Hash kedua file dicetak dan disimpan di `_manifest.json` setiap kali generator dijalankan.
- Seed yang sama menghasilkan file yang identik byte per byte. `_manifest.json` mencatat SHA-256 tiap file untuk membuktikannya.
- Versi numpy dan pandas di-pin di `requirements.txt`, karena algoritma sampling bisa berubah antar versi mayor.

## 15. Output Generator

Semua file ditulis ke `ml/data/raw/` (folder `ml/data/` di-gitignore karena bisa dibuat ulang).

**Tabel DB.** Kolom, urutan kolom, dan nilai enum sama persis dengan 7 tabel di database. Siap di-seed apa adanya.

| File | Isi |
| --- | --- |
| `users.csv` | 1 owner dan 1 admin fiktif |
| `materials.csv` | 15 material |
| `vendors.csv` | 28 vendor, tanpa karakter tersembunyi |
| `vendor_offers.csv` | Snapshot penawaran per 30 September 2026 |
| `procurement_requests.csv` | Request historis, termasuk `request_date`. Status `completed` kalau ada transaksi, `cancelled` kalau tidak ada kandidat yang lolos filter |
| `transactions.csv` | Transaksi historis dengan `request_id` |
| `recommendations.csv` | Header saja. Tabel ini diisi oleh model, bukan generator |

**File tambahan.** Berawalan `_`, tidak di-seed ke database.

| File | Isi | Boleh jadi fitur? |
| --- | --- | --- |
| `_candidates.csv` | Satu baris per (request, vendor): snapshot penawaran saat request (harga, MOQ, janji lead time, kapasitas, ketersediaan), `is_eligible`, `filter_reasons` (format JSON seperti kolom DB), `chosen` | Ya, kecuali `chosen` |
| `_labels.csv` | Satu baris per (request, vendor) yang lolos filter: `p_tepat`, `e_cacat`, `e_biaya`, `skor_hasil`, `grade` | Tidak, hanya label dan evaluasi |
| `_request_meta.csv` | `split`, `urgency`, `season_intensity`, jumlah kandidat, `is_training_group` | `season_intensity` boleh, sisanya untuk split dan analisis |
| `_hidden_vendor_traits.csv` | Karakter tersembunyi, nilai z, jenis vendor, arketipe, `onboard_date` | Tidak |
| `_manifest.json` | Seed, hash konfigurasi, jumlah baris, SHA-256 tiap file | |

Aturan untuk `_hidden_vendor_traits.csv` dan `_labels.csv`:

- Tidak boleh di-join ke tabel fitur. Pipeline preprocessing akan punya pengecekan otomatis bahwa tidak ada kolom karakter tersembunyi (`price_level`, `true_quality`, `true_reliability`, `lead_time_factor`, `capacity_factor`, `archetype`) atau kolom label di matriks fitur.
- Tidak di-seed ke database.

Set skenario urgent vs santai (bagian 13.5) belum diimplementasikan. Set ini akan ditambahkan saat tahap evaluasi.

## 16. Pengecekan Kewajaran

Setelah generate, script mengecek angka-angka berikut. Kalau ada yang di luar target, parameter bertanda **[KALIBRASI]** disetel ulang lalu generator dijalankan lagi.

| Pengecekan | Target |
| --- | --- |
| Jumlah transaksi | 1.800 s.d. 2.200 |
| Vendor penawar per material | minimal 4 |
| Korelasi `price_level` dan `true_quality` antar vendor | 0,2 s.d. 0,6 |
| Jumlah vendor per arketipe | sesuai tabel bagian 5.3 |
| Tingkat tepat waktu transaksi (terhadap `promised_date`) | 70% s.d. 85% secara keseluruhan |
| Tingkat tepat waktu saat `s(t) >= 0,5` dibanding `s(t) = 0` | lebih rendah minimal 10 poin persen |
| Tingkat cacat rata-rata | 1% s.d. 4% |
| Proporsi pesanan batal | di bawah 5% |
| Kandidat gugur filter keras | 10% s.d. 30% dari semua kandidat |
| Grup layak training (minimal 2 kandidat lolos) | minimal 85% dari request |
| Distribusi grade | grade 0 sekitar 15% s.d. 25%, grade 3 sekitar 10% s.d. 20% |
| Grup dengan semua kandidat ber-grade sama | di bawah 15% (grup seperti ini tidak memberi sinyal ranking) |
| Kolom tersembunyi di file publik | tidak ada |

Selain pengecekan di atas, validasi otomatis mengecek semua constraint DB (kolom, NOT NULL, PK, FK, unique, enum, CHECK, panjang VARCHAR) dan konsistensi antar file (label sama dengan kandidat lolos, vendor terpilih termasuk kandidat lolos, status request sesuai transaksi). Pelanggaran constraint DB membuat generator keluar dengan exit code 1. Pengecekan kewajaran hanya berupa peringatan.

Hasil dengan seed default 15037:

| Pengecekan | Hasil |
| --- | --- |
| Jumlah transaksi | 2.050 |
| Korelasi `price_level` dan `true_quality` | 0,44 |
| Tepat waktu terhadap `promised_date` | 75,0% |
| Selisih tepat waktu normal vs musim ramai | 14,4 poin persen |
| Tingkat cacat rata-rata | 3,6% |
| Pesanan batal | 2,8% |
| Kandidat gugur filter keras | 26,3% |
| Request layak jadi grup training | 92,4% |
| Grade 0 / 1 / 2 / 3 | 19,0% / 26,2% / 38,0% / 16,8% |
| Grup training dengan semua grade sama | 14,1% |

Kalibrasi dilakukan dengan seed default. Karena vendornya hanya 28, seed lain bisa menghasilkan dunia yang cukup berbeda. Dari seed 1, 2, 3, 42, 43, dan 15037, tiga seed lolos semua pengecekan dan sisanya meleset satu sampai dua pengecekan (paling jauh grup dengan grade sama 26,9% pada seed 43). Untuk training dan laporan dipakai seed default.

Statistik lengkap akan dibahas di notebook EDA.

## 17. Kalibrasi dari Marketplace

Parameter bertanda **[MP]** diisi dari listing marketplace dengan cara berikut:

1. Cari tiap material di Tokopedia dan Shopee dengan kata kunci yang dicatat (contoh: "handuk mandi katun 70x140 grosir").
2. Ambil 15 s.d. 20 listing dari penjual dengan jumlah terjual yang wajar. Abaikan listing yang jelas berbeda spesifikasi atau harganya ekstrem.
3. Pakai harga tier grosir yang paling dekat dengan qty median di bagian 4.2.
4. Catat harga, MOQ, dan masa pre-order atau estimasi pengerjaan per listing.
5. Hitung median, p25, dan p75 harga, median MOQ, dan median masa pre-order.

Hasilnya diisi ke `generator/price_reference.yaml` (ganti nilai bertanda `# TODO: kalibrasi`). Kalau `price_p25` dan `price_p75` semua material sudah terisi, generator otomatis memakai sigma harga dari data marketplace. Setelah itu generator dijalankan ulang dan pengecekan kewajaran dicek lagi.

Tabel yang perlu diisi (akan dipindah ke bagian sitasi README utama):

| Kode | Kata kunci | Platform | Jumlah listing | Median harga | p25 | p75 | Median MOQ | Median pre-order (hari) | Tanggal akses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01 | | | | | | | | | |
| B02 | | | | | | | | | |
| B03 | | | | | | | | | |
| B04 | | | | | | | | | |
| B05 | | | | | | | | | |
| J01 | | | | | | | | | |
| J02 | | | | | | | | | |
| J03 | | | | | | | | | |
| J04 | | | | | | | | | |
| J05 | | | | | | | | | |
| P01 | | | | | | | | | |
| P02 | | | | | | | | | |
| P03 | | | | | | | | | |
| P04 | | | | | | | | | |
| P05 | | | | | | | | | |

Daftar URL listing yang dipakai disimpan sebagai lampiran sitasi. Data mentah hasil pencatatan tidak perlu berisi nama penjual.

## 18. Batasan

- Data sepenuhnya sintetis. Hasil model hanya menunjukkan bahwa pendekatan bekerja di dunia yang diasumsikan generator, belum membuktikan performa di data asli Firaza.
- Antrian antar order Firaza sendiri di vendor yang sama tidak dimodelkan. Efek kesibukan vendor hanya diwakili musim ramai.
- Karakter vendor tidak berubah sepanjang 18 bulan. Opsional setelah MVP: drift kecil pada `true_reliability` beberapa vendor supaya metrik histori terbaru lebih berarti.
- Periode test (Juli s.d. September 2026) hampir seluruhnya musim normal. Perilaku saat musim ramai lebih banyak teruji di periode validasi (Syawal dan Dzulhijjah) dan di set skenario.
- Biaya ongkos kirim dan diskon pembayaran tidak dimodelkan.
- Order material diasumsikan saling independen. Pada kenyataannya order bordir biasanya mengikuti order handuk atau sajadah.
