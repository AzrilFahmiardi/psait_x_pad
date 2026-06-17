import json
import os
from typing import Optional
from pyproj import Transformer

_transformer = Transformer.from_crs("EPSG:32749", "EPSG:4326", always_xy=True)

manholes: list[dict] = []
pipes: list[dict] = []

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _normalize_status(raw: Optional[str]) -> str:
    if not raw:
        return "baik"
    val = raw.strip().lower()
    if val in ("perbaikan", "rusak"):
        return val
    return "baik"


def _convert_utm_coords(coords: list) -> list:
    """Recursively convert UTM Zone 49S coordinate arrays to WGS84 [lon, lat]."""
    if not coords:
        return coords
    if isinstance(coords[0], (int, float)):
        lon, lat = _transformer.transform(coords[0], coords[1])
        return [round(lon, 8), round(lat, 8)]
    return [_convert_utm_coords(c) for c in coords]


def _load_manholes():
    path = os.path.join(DATA_DIR, "manhole.geojson")
    with open(path, encoding="utf-8") as f:
        fc = json.load(f)

    result = []
    for idx, feature in enumerate(fc.get("features", []), start=1):
        props = feature.get("properties", {})
        # Geometry: use X/Y properties (already WGS84) for the point
        lon = props.get("X")
        lat = props.get("Y")
        geometry = {"type": "Point", "coordinates": [lon, lat]} if lon and lat else None

        sektor_raw = props.get("Sektor")
        sektor = int(sektor_raw) if sektor_raw is not None else None

        result.append({
            "id": idx,
            "kode_manhole": props.get("NOMOR_MH"),
            "bentuk": props.get("BENTUK"),
            "dim_mh": props.get("DIM_MH"),
            "panjang": props.get("PANJANG"),
            "lebar": props.get("LEBAR"),
            "kedalaman": props.get("KEDALAMAN"),
            "material_mh": props.get("MATERIALMH"),
            "struktur_mh": props.get("STR_MH"),
            "kondisi_mh": props.get("KONDISI_MH"),
            "sedimen": props.get("SEDIMEN"),
            "jarak_pipa": props.get("JARAKPIPA"),
            "ukuran_pipa": props.get("UKURANPIPA"),
            "material_pipa": props.get("MATERIAL_P"),
            "sekitar": props.get("SEKITAR"),
            "surveyor": props.get("SURVEYOR"),
            "desa": props.get("DESA"),
            "kecamatan": props.get("KECAMATAN"),
            "ketinggian": props.get("KETINGGIAN"),
            "topografi": props.get("TOPOGRAFI"),
            "jenis_tanah": props.get("JENISTANAH"),
            "longitude": lon,
            "latitude": lat,
            "geometry": geometry,
            "foto_1": props.get("FOTO_1"),
            "foto_2": props.get("FOTO_2"),
            "foto_3": props.get("FOTO_3"),
            "foto_4": props.get("FOTO_4"),
            "probabilitas": props.get("Probabilit"),
            "dampak": props.get("Dampak"),
            "tingkat_risiko": props.get("Tingkat_Ri"),
            "risiko": props.get("Risiko"),
            "klasifikasi": props.get("Klasifikas"),
            "pengendali": props.get("Pengendali"),
            "sektor": sektor,
            "status": _normalize_status(props.get("STATUS")),
            "wilayah": props.get("WILAYAH"),
            "aduan_count": 0,
        })
    return result


def _load_pipes():
    path = os.path.join(DATA_DIR, "pipes.geojson")
    with open(path, encoding="utf-8") as f:
        fc = json.load(f)

    result = []
    for idx, feature in enumerate(fc.get("features", []), start=1):
        props = feature.get("properties", {})
        raw_geom = feature.get("geometry")

        # Convert UTM 49S → WGS84
        geometry = None
        if raw_geom:
            converted_coords = _convert_utm_coords(raw_geom["coordinates"])
            geometry = {"type": raw_geom["type"], "coordinates": converted_coords}

        id_jalur = props.get("ID_JALUR")
        kode_pipa = f"PIPA-{idx:04d}" if not id_jalur else f"{id_jalur}-{idx}"

        tahun_raw = props.get("YEAR")
        tahun = int(tahun_raw) if tahun_raw and tahun_raw != 0.0 else None

        fungsi_raw = props.get("FUNGSI")
        fungsi = fungsi_raw.capitalize() if fungsi_raw else None

        result.append({
            "id": idx,
            "id_jalur": id_jalur,
            "kode_pipa": kode_pipa,
            "pipe_dia": props.get("PIPE_DIA"),
            "fungsi": fungsi,
            "length_km": props.get("LENGTH_KM"),
            "tahun": tahun,
            "source": props.get("SOURCE"),
            "material": None,
            "geometry": geometry,
            "status": "baik",
            "wilayah": None,
            "aduan_count": 0,
        })
    return result


def load_all():
    global manholes, pipes
    manholes = _load_manholes()
    pipes = _load_pipes()
    print(f"Loaded {len(manholes)} manholes, {len(pipes)} pipes")
