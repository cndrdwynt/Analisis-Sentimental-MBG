# 🍽️ Analisis Aspirasi Publik: Program Makan Bergizi Gratis (MBG)

Sistem pemantauan sentimen dan aspirasi masyarakat secara **real-time** terhadap kebijakan program nasional **Makan Bergizi Gratis (MBG)** menggunakan data komentar dari platform YouTube. Dibangun dengan arsitektur otomatisasi ujung-ke-ujung (*end-to-end*) yang mengintegrasikan data crawling, pipeline AI, penyimpanan database, hingga visualisasi interaktif pada dashboard analitik.

---

## 📊 Arsitektur & Alur Sistem

Sistem bekerja secara otomatis dalam lingkaran berkala (*scheduled loop*) dengan pembagian tugas sebagai berikut:

1. **Data Crawling (Python & Service Schedule):** Skrip Python mengidentifikasi video YouTube topikal via `yt-dlp` dan menarik komentar menggunakan `YoutubeCommentDownloader`. Data mentah langsung disimpan ke koleksi MongoDB lokal.
2. **AI-Driven Orchestration (n8n & Groq LLM):** n8n membaca data berstatus `belum` dianalisis, lalu mengirimkannya ke LLM Agent (`llama-3.1-8b-instant` via Groq) untuk mengekstrak label sentimen (*Positif/Negatif/Netral*), alasan singkat, dan kategorisasi isu kebijakan.
3. **Database Sinkronisasi (MongoDB):** Dokumen yang telah diproses AI di-update ke koleksi `processed_mbg`, dan status analisis di koleksi utama diubah menjadi `sudah`.
4. **Data Visualization (Metabase Dashboard):** Metabase membaca MongoDB untuk menyajikan grafik peta sentimen makro, tren topik, dan pemetaan keresahan kolektif masyarakat secara interaktif.

---

## 🛠️ Spesifikasi Teknologi

Seluruh infrastruktur penunjang dikontainerisasi menggunakan **Docker**.

### Docker Services

| Komponen | Image | Fungsi |
|---|---|---|
| **Database** | `mongo:latest` | Storage utama data kualitatif bervolume besar |
| **Database GUI** | `mongo-express` | Manajemen visual dokumen MongoDB |
| **Automation Engine** | `docker.n8n.io/n8nio/n8n` | Node-workflow untuk integrasi pipeline ke AI |
| **AI Engine** | Groq Cloud API | LangChain Agent + model `llama-3.1-8b-instant` |
| **BI & Dashboard** | `metabase/metabase:latest` | Visualisasi data analitik berbasis web UI |

### Python Crawler

- Menggunakan pustaka `schedule` untuk penarikan data otomatis setiap **6 jam**
- Dilengkapi fungsi pembersihan teks dan filter minimal **15 karakter** untuk membuang *noise data*
- Menerapkan sistem **Upsert** berbasis `username` + `full_text` untuk mencegah duplikasi data

---

## 📂 Struktur Direktori

```text
analisis-mbg/
│
├── data_metabase/             # Diabaikan .gitignore (H2 Database Metabase)
├── data_n8n/                  # Diabaikan .gitignore (Konfigurasi Lokal n8n)
├── db_mongo/                  # Diabaikan .gitignore (Penyimpanan Fisik MongoDB)
├── env/                       # Diabaikan .gitignore (Python Virtual Environment)
│
├── crawler_mbg.py             # Skrip utama Python YouTube Crawler & Scheduler
├── docker-compose.yml         # Konfigurasi orkestrasi seluruh Docker services
├── .env                       # Diabaikan .gitignore (Kredensial & API Key)
├── .gitignore                 # Aturan pengabaian pelacakan Git
├── workflow mbg.json       # Export workflow n8n pipeline
├── requirements.txt           # Daftar dependensi library Python
└── README.md                  # Dokumentasi utama proyek
```

---

## 🚀 Panduan Setup & Deployment

### 1. Prasyarat Sistem

Pastikan perangkat sudah terinstal:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.10+
- Git CLI

### 2. Clone Project & Konfigurasi Environment

```bash
git clone <url-repository-kamu>
cd analisis-mbg
```

Buat file `.env` di root direktori (jangan di-push ke publik):

```env
MONGO_INITDB_ROOT_USERNAME=your_mongo_username
MONGO_INITDB_ROOT_PASSWORD=your_strong_password
GROQ_API_KEY=your_groq_api_key
```

### 3. Jalankan Infrastruktur Docker

```bash
docker compose up -d
```

Verifikasi seluruh kontainer berjalan normal via `docker ps` atau Docker Desktop GUI.

### 4. Setup Python & Crawler

```bash
# Buat virtual environment
python -m venv env

# Aktivasi (Windows PowerShell)
.\env\Scripts\Activate.ps1

# Instalasi dependensi
pip install -r requirements.txt

# Jalankan crawler
python crawler_mbg.py
```

Skrip akan mengunduh komentar dari **15 video teratas** dengan keyword *"Makan Bergizi Gratis"* dan berjalan di latar belakang setiap 6 jam secara otomatis.

### 5. Import Workflow ke n8n

1. Buka browser, akses `http://localhost:5678`
2. Buat workflow baru → klik menu pojok kanan atas → **Import from File**
3. Pilih file `workflow mbg.json` dari folder proyek
4. Sesuaikan konfigurasi kredensial:
   - Node MongoDB account → masukkan kredensial MongoDB sesuai file .env kamu
   - Node **Groq Chat Model** → masukkan API Key Groq kamu
5. Klik **Save** → aktifkan trigger (**Set Active**)

Pipeline AI kini siap mengolah data setiap **12 jam** secara berkala, atau bisa dijalankan manual via *Execute Workflow*.

### 6. Akses Dashboard Metabase

1. Buka browser, akses `http://localhost:3000`
2. Ikuti setup awal, pilih koneksi database ke **MongoDB**
3. Masukkan detail kredensial MongoDB sesuai konfigurasi Docker

Kamu kini dapat menyusun:
- 🥧 Grafik lingkaran **Peta Sentimen**
- 📊 Grafik batang **Topik Utama**
- 📋 Tabel **Aspirasi Masyarakat** berdasarkan jumlah likes tertinggi

---

## 📈 Contoh Output Analisis

Berdasarkan pengujian agregat data riil dari platform YouTube:

**Peta Sentimen Umum:**
- Mayoritas percakapan publik didominasi sentimen **Negatif/Kritis** terkait efisiensi alokasi dana
- Diikuti sentimen **Positif** yang mendukung peningkatan gizi anak sekolah
- Serta respons **Netral** yang bersifat observatif lapangan

**Kategori Isu Terpanas:**
- 🔴 **Kritik Anggaran** — potensi kebocoran anggaran & korupsi lokal
- 🟠 **Keluhan Teknis** — kesiapan infrastruktur dapur umum
- 🟡 **Dampak Ekonomi** — dampak terhadap ekosistem PKL & warung sekitar sekolah

---

## 📄 Lisensi

Proyek ini dikembangkan untuk mendukung metodologi evaluasi kebijakan publik berbasis analisis **Big Data** yang akurat dan transparan.
