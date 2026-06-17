# IPAL Public API

Public read-only REST API untuk data jaringan IPAL (Instalasi Pengolahan Air Limbah) Kota Yogyakarta — mencakup **5.286 titik manhole** dan **458 segmen jaringan pipa** hasil survei lapangan 2024.

**Base URL:** `https://psait-x-pad.onrender.com`  
**Dokumentasi Interaktif (Swagger):** `https://psait-x-pad.onrender.com/docs`  
**Dokumentasi Alternatif (ReDoc):** `https://psait-x-pad.onrender.com/redoc`

---

## Interoperabilitas

### Arsitektur: Pemisahan Frontend dan Backend

Sistem ini dibangun dengan arsitektur **decoupled** — backend API dan frontend berjalan sebagai layanan yang sepenuhnya terpisah, berkomunikasi melalui **HTTP REST API**.

```
┌─────────────────────────────┐        HTTPS / REST API       ┌──────────────────────────────┐
│        FRONTEND             │ ─────────────────────────────▶│        BACKEND (repo ini)    │
│  (repo terpisah)            │                               │                              │
│                             │  GET /api/ipal/statistics     │  FastAPI (Python)            │
│  - Leaflet.js (peta)        │  GET /api/ipal/manholes/...   │  Data: GeoJSON file          │
│  - MapTiler SDK             │  GET /api/ipal/pipes/...      │  Koordinat: WGS84            │
│  - Alpine.js / Blade        │◀─────────────────────────────│  CORS: terbuka (*)           │
│                             │  JSON Response                │                              │
└─────────────────────────────┘                               └──────────────────────────────┘
```

### Cara Kerja Integrasi

**1. Konfigurasi API Base URL di Frontend**

Frontend mendefinisikan satu titik konfigurasi `API_BASE` yang mengarah ke URL API ini:

```javascript
const API_BASE          = 'https://psait-x-pad.onrender.com/api/ipal';
const API_PIPES_GEOJSON = API_BASE + '/pipes/geojson';
const API_MHOLE_GEOJSON = API_BASE + '/manholes/geojson';
const API_PIPES_FILTERS = API_BASE + '/pipes/filters';
const API_STATISTICS    = API_BASE + '/statistics';
```

**2. Pengambilan Data GeoJSON untuk Peta**

Saat halaman peta dibuka, frontend melakukan `fetch()` ke endpoint `/geojson` dan hasilnya langsung dirender sebagai layer Leaflet.js:

```javascript
// Contoh pengambilan data manhole untuk peta
const resp = await fetch(API_MHOLE_GEOJSON + '?kecamatan=Wirobrajan');
const geojson = await resp.json();

L.geoJSON(geojson, {
    pointToLayer: (feature, latlng) => L.circleMarker(latlng, { ... })
}).addTo(map);
```

**3. CORS (Cross-Origin Resource Sharing)**

Backend dikonfigurasi dengan CORS terbuka (`allow_origins: ["*"]`) sehingga frontend yang di-host di domain mana pun dapat mengonsumsi API ini tanpa hambatan browser policy. Hanya method `GET` yang diizinkan sesuai sifat API yang read-only.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

**4. Format Data**

Semua endpoint mengembalikan **JSON**. Endpoint `/geojson` mengembalikan format standar **GeoJSON RFC 7946** (FeatureCollection) yang kompatibel langsung dengan Leaflet.js, MapLibre GL, dan library peta modern lainnya. Endpoint lain menggunakan format:

```json
{ "success": true, "data": { ... } }
```

---

## Deployment

### Platform: Render.com (Cloud Hosting)

API ini di-deploy pada **Render.com** menggunakan layanan **Web Service** dengan plan **Free Tier**. Render.com adalah platform cloud hosting yang mendukung deployment langsung dari Docker image via GitHub repository.

**Spesifikasi Free Tier Render.com:**
| Resource | Kapasitas |
|---|---|
| CPU | 0.1 shared vCPU |
| RAM | 512 MB |
| Storage | Ephemeral (bawaan image) |
| Bandwidth | 100 GB/bulan |
| Sleep | Setelah 15 menit tidak ada request |

> **Catatan Cold Start:** Karena free tier mematikan service saat idle, request pertama setelah periode diam membutuhkan waktu ±30 detik untuk "bangun" kembali. Setelah aktif, response time normal.

### Alur Deployment

Deployment dilakukan secara **otomatis (CI/CD)** setiap kali ada push ke branch `master` di GitHub:

```
Developer (lokal)
      │
      │  git push origin master
      ▼
GitHub Repository
(AzrilFahmiardi/psait_x_pad)
      │
      │  Webhook trigger
      ▼
Render.com Build Pipeline
      │
      ├── 1. Pull source code dari GitHub
      ├── 2. Build Docker image (docker build)
      ├── 3. Push image ke Render internal registry
      ├── 4. Deploy container baru
      └── 5. Health check → traffic dialihkan ke container baru
      │
      ▼
https://psait-x-pad.onrender.com  ✅
```

### Konfigurasi Render (`render.yaml`)

```yaml
services:
  - type: web
    name: ipal-public-api
    runtime: docker
    plan: free
    healthCheckPath: /
```

File `render.yaml` di root repository memberitahu Render bahwa service ini menggunakan Docker runtime dan endpoint `/` digunakan sebagai health check.

---

## Penggunaan Docker

### Implementasi Docker

Seluruh proses packaging dan deployment memanfaatkan **Docker** untuk memastikan konsistensi environment antara development lokal dan production.

### Dockerfile

```dockerfile
FROM python:3.12-slim        # Base image ringan (~50MB compressed)

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt   # Install dependencies

COPY . .                     # Copy source code + data GeoJSON

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Strategi yang digunakan:**
- **`python:3.12-slim`** — image ringan tanpa tools yang tidak diperlukan, mempercepat build dan mengurangi ukuran image
- **Copy `requirements.txt` lebih dulu** — memanfaatkan Docker layer caching; layer dependencies tidak di-rebuild selama requirements tidak berubah
- **Data GeoJSON di-bundle ke dalam image** — file `data/manhole.geojson` dan `data/pipes.geojson` ikut masuk ke image sehingga container bersifat self-contained tanpa perlu external storage

### docker-compose.yml (Development Lokal)

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data:ro    # Mount data sebagai read-only
    restart: unless-stopped
```

### Menjalankan Lokal dengan Docker

```bash
# Build dan jalankan
docker compose up

# Atau tanpa compose
docker build -t ipal-public-api .
docker run -p 8000:8000 ipal-public-api
```

API tersedia di `http://localhost:8000` setelah container aktif.

### Alur Data Saat Container Startup

```
Container start
      │
      ▼
uvicorn main:app
      │
      ▼
FastAPI lifespan event: load_all()
      │
      ├── Baca data/manhole.geojson  → parse 5.286 features → simpan di memory
      └── Baca data/pipes.geojson   → parse 458 features
                                      → konversi koordinat UTM Zone 49S → WGS84
                                      → simpan di memory
      │
      ▼
API siap melayani request (tanpa query ke database)
```

Pendekatan **in-memory** dipilih karena data bersifat statis (tidak berubah saat runtime), sehingga setiap request langsung dilayani dari RAM tanpa I/O disk atau query database.

---

## Endpoints

| Method | Endpoint | Deskripsi |
|---|---|---|
| GET | `/api/ipal/statistics` | Statistik ringkasan jaringan IPAL |
| GET | `/api/ipal/manholes` | Daftar manhole (pagination + filter) |
| GET | `/api/ipal/manholes/{id}` | Detail satu manhole |
| GET | `/api/ipal/manholes/filters` | Nilai unik untuk filter manhole |
| GET | `/api/ipal/manholes/geojson` | GeoJSON manhole untuk peta |
| GET | `/api/ipal/pipes` | Daftar pipa (pagination + filter) |
| GET | `/api/ipal/pipes/{id}` | Detail satu pipa |
| GET | `/api/ipal/pipes/filters` | Nilai unik untuk filter pipa |
| GET | `/api/ipal/pipes/geojson` | GeoJSON pipa untuk peta |

Dokumentasi lengkap tiap endpoint (parameter, contoh request/response) tersedia di **Swagger UI**: `https://psait-x-pad.onrender.com/docs`

---

## Stack Teknologi

| Komponen | Teknologi |
|---|---|
| Framework API | FastAPI (Python 3.12) |
| Web Server | Uvicorn (ASGI) |
| Transformasi Koordinat | pyproj (UTM → WGS84) |
| Containerisasi | Docker |
| Cloud Hosting | Render.com |
| CI/CD | GitHub → Render auto-deploy |
| Format Data | GeoJSON (RFC 7946) |

---

## Data

| Aset | Jumlah | Sumber Koordinat |
|---|---|---|
| Manhole | 5.286 titik | WGS84 (EPSG:4326) — langsung dari GeoJSON |
| Jaringan pipa | 458 segmen | UTM Zone 49S (EPSG:32749) → dikonversi ke WGS84 |
| Total panjang pipa | ±187 km | — |

Data bersumber dari survei lapangan jaringan IPAL Kota Yogyakarta tahun 2024.
