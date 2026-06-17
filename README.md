# IPAL Public API

Public read-only REST API untuk data jaringan IPAL (Instalasi Pengolahan Air Limbah) — manhole dan jaringan pipa. Data dibaca langsung dari file GeoJSON saat startup tanpa database.

## Base URL

```
https://psait-x-pad.onrender.com
```

## Endpoints

### Statistik

#### `GET /api/ipal/statistics`

Ringkasan statistik jumlah manhole dan pipa.

**Query params (opsional):**
| Param | Deskripsi |
|---|---|
| `wilayah` | Filter berdasarkan wilayah |
| `kecamatan` | Filter berdasarkan kecamatan (manholes only) |

**Response:**
```json
{
  "success": true,
  "data": {
    "manhole": {
      "total": 5286,
      "by_status": { "baik": 5286, "perbaikan": 0, "rusak": 0 },
      "by_kondisi": { "Lancar": 4654, "Kurang Lancar": 185 }
    },
    "pipa": {
      "total": 458,
      "total_panjang_km": 187.61,
      "by_status": { "baik": 458, "perbaikan": 0, "rusak": 0 },
      "by_fungsi": { "Lateral": 385, "Induk": 51, "Glontor": 22 }
    }
  },
  "filters_applied": { "wilayah": null, "kecamatan": null }
}
```

---

### Manhole

#### `GET /api/ipal/manholes`

Daftar manhole dengan pagination dan filter.

**Query params:**
| Param | Deskripsi |
|---|---|
| `page` | Nomor halaman (default: 1) |
| `per_page` | Item per halaman (default: 15, max: 500) |
| `kecamatan` | Filter kecamatan |
| `desa` | Filter desa |
| `kondisi_mh` | Filter kondisi (`Lancar`, `Kurang Lancar`, `Tidak Lancar`, `Tidak Diketahui`) |
| `risiko` | Filter risiko |
| `klasifikasi` | Filter klasifikasi (`Risiko Rendah`, `Risiko Sedang`, `Risiko Tinggi`, `Risiko Sangat Tinggi`) |
| `status` | Filter status (`baik`, `perbaikan`, `rusak`) |
| `bentuk` | Filter bentuk (`Kotak/Persegi`, `Tabung`) |
| `material_mh` | Filter material |
| `sektor` | Filter sektor (integer) |
| `wilayah` | Filter wilayah |
| `search` | Cari berdasarkan kode manhole, desa, atau kecamatan |

#### `GET /api/ipal/manholes/{id}`

Detail satu manhole berdasarkan ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "kode_manhole": "ABBAH_3_J.15-10",
    "bentuk": "Kotak/Persegi",
    "kondisi_mh": "Lancar",
    "risiko": "Kondisi Baik",
    "klasifikasi": "Risiko Rendah",
    "status": "baik",
    "kecamatan": "Wirobrajan",
    "desa": "Pakuncen",
    "longitude": 110.353312678,
    "latitude": -7.79914364729,
    "geometry": { "type": "Point", "coordinates": [110.353312678, -7.79914364729] },
    "sektor": 1,
    "wilayah": "Wirobrajan",
    "aduan_count": 0
  }
}
```

#### `GET /api/ipal/manholes/filters`

Daftar nilai unik untuk setiap field filter manhole.

#### `GET /api/ipal/manholes/geojson`

GeoJSON FeatureCollection semua manhole (untuk peta).

**Query params:** `kecamatan`, `kondisi_mh`, `risiko`, `status`, `sektor`, `wilayah`

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [110.353, -7.799] },
      "properties": {
        "id": 1,
        "kode_manhole": "ABBAH_3_J.15-10",
        "kondisi_mh": "Lancar",
        "status": "baik",
        "aduan_count": 0
      }
    }
  ]
}
```

---

### Jaringan Pipa

#### `GET /api/ipal/pipes`

Daftar pipa dengan pagination dan filter.

**Query params:**
| Param | Deskripsi |
|---|---|
| `page` | Nomor halaman (default: 1) |
| `per_page` | Item per halaman (default: 15, max: 500) |
| `fungsi` | Filter fungsi (`Lateral`, `Induk`, `Glontor`) |
| `pipe_dia` | Filter diameter pipa (mm) |
| `tahun` | Filter tahun pemasangan |
| `status` | Filter status |
| `material` | Filter material |
| `wilayah` | Filter wilayah |
| `search` | Cari berdasarkan kode pipa atau ID jalur |

#### `GET /api/ipal/pipes/{id}`

Detail satu pipa berdasarkan ID.

#### `GET /api/ipal/pipes/filters`

Daftar nilai unik untuk setiap field filter pipa.

#### `GET /api/ipal/pipes/geojson`

GeoJSON FeatureCollection semua pipa (untuk peta).

**Query params:** `fungsi`, `tahun`, `status`, `wilayah`

---

## Data

| Aset | Jumlah |
|---|---|
| Manhole | 5.286 titik |
| Jaringan pipa | 458 segmen |
| Total panjang pipa | ±187 km |

Data bersumber dari survei lapangan 2024 area Kota Yogyakarta.

Koordinat manhole dalam format WGS84 (EPSG:4326). Koordinat pipa dikonversi otomatis dari UTM Zone 49S (EPSG:32749) ke WGS84 saat service startup.

---

## Menjalankan Lokal

**Dengan Docker:**
```bash
docker compose up
# API tersedia di http://localhost:8000
```

**Tanpa Docker:**
```bash
pip install -r requirements.txt
uvicorn main:app --reload
# API tersedia di http://localhost:8000
```

---

## Stack

- **Runtime**: Python 3.12
- **Framework**: FastAPI
- **Koordinat**: pyproj (UTM → WGS84)
- **Deploy**: Docker → Render.com
