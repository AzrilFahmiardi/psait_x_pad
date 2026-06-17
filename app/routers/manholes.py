from fastapi import APIRouter, Query, Request, HTTPException
from typing import Optional
from app import data_loader

router = APIRouter(prefix="/api/ipal/manholes", tags=["manholes"])

_MH_ITEM_EXAMPLE = {
    "id": 1,
    "kode_manhole": "ABBAH_3_J.15-10",
    "bentuk": "Kotak/Persegi",
    "dim_mh": 0.0,
    "panjang": 70.0,
    "lebar": 70.0,
    "kedalaman": 0.0,
    "material_mh": "Cor/Beton",
    "struktur_mh": "Baik",
    "kondisi_mh": "Lancar",
    "sedimen": 0.0,
    "risiko": "Kondisi Baik",
    "klasifikasi": "Risiko Rendah",
    "status": "baik",
    "desa": "Pakuncen",
    "kecamatan": "Wirobrajan",
    "wilayah": "Wirobrajan",
    "longitude": 110.353312678,
    "latitude": -7.79914364729,
    "geometry": {"type": "Point", "coordinates": [110.353312678, -7.79914364729]},
    "sektor": 1,
    "aduan_count": 0,
}

_GEOJSON_EXAMPLE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [110.353312678, -7.79914364729]},
            "properties": {
                "id": 1,
                "kode_manhole": "ABBAH_3_J.15-10",
                "kondisi_mh": "Lancar",
                "klasifikasi": "Risiko Rendah",
                "status": "baik",
                "kecamatan": "Wirobrajan",
                "sektor": 1,
                "aduan_count": 0,
            },
        }
    ],
}

_FILTERS_EXAMPLE = {
    "success": True,
    "data": {
        "kondisi_mh": ["Kurang Lancar", "Lancar", "Tidak Diketahui", "Tidak Lancar"],
        "risiko": ["Kondisi Baik", "Bisa menyebabkan aliran tersumbat"],
        "klasifikasi": ["Risiko Rendah", "Risiko Sedang", "Risiko Tinggi", "Risiko Sangat Tinggi"],
        "kecamatan": ["Danurejan", "Gondomanan", "Wirobrajan"],
        "bentuk": ["Kotak/Persegi", "Tabung"],
        "material_mh": ["Bata", "Cor/Beton", "Pracetak"],
        "status": ["baik"],
        "sektor": [1, 2, 3],
        "wilayah": ["Danurejan", "Gondomanan", "Wirobrajan"],
    },
}


def _filter_manholes(
    desa=None, kecamatan=None, kondisi_mh=None, risiko=None,
    klasifikasi=None, status=None, bentuk=None, material_mh=None,
    sektor=None, wilayah=None, search=None,
):
    items = data_loader.manholes
    if desa:
        items = [m for m in items if m["desa"] and desa.lower() in m["desa"].lower()]
    if kecamatan:
        items = [m for m in items if m["kecamatan"] and kecamatan.lower() in m["kecamatan"].lower()]
    if kondisi_mh:
        items = [m for m in items if m["kondisi_mh"] == kondisi_mh]
    if risiko:
        items = [m for m in items if m["risiko"] == risiko]
    if klasifikasi:
        items = [m for m in items if m["klasifikasi"] == klasifikasi]
    if status:
        items = [m for m in items if m["status"] == status]
    if bentuk:
        items = [m for m in items if m["bentuk"] == bentuk]
    if material_mh:
        items = [m for m in items if m["material_mh"] == material_mh]
    if sektor is not None:
        items = [m for m in items if m["sektor"] == sektor]
    if wilayah:
        items = [m for m in items if m["wilayah"] and wilayah.lower() in m["wilayah"].lower()]
    if search:
        s = search.lower()
        items = [
            m for m in items
            if (m["kode_manhole"] and s in m["kode_manhole"].lower())
            or (m["desa"] and s in m["desa"].lower())
            or (m["kecamatan"] and s in m["kecamatan"].lower())
        ]
    return items


def _build_pagination(request: Request, page: int, per_page: int, total: int):
    last_page = max(1, (total + per_page - 1) // per_page)
    base = str(request.base_url).rstrip("/") + str(request.url.path)

    def page_url(p):
        params = dict(request.query_params)
        params["page"] = str(p)
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base}?{qs}"

    links = [{"url": None, "label": "&laquo; Previous", "active": False}]
    for i in range(1, last_page + 1):
        links.append({"url": page_url(i), "label": str(i), "active": i == page})
    links.append({"url": page_url(page + 1) if page < last_page else None, "label": "Next &raquo;", "active": False})

    return {
        "first_page_url": page_url(1),
        "last_page_url": page_url(last_page),
        "next_page_url": page_url(page + 1) if page < last_page else None,
        "prev_page_url": page_url(page - 1) if page > 1 else None,
        "path": base,
        "from": (page - 1) * per_page + 1 if total > 0 else None,
        "to": min(page * per_page, total) if total > 0 else None,
        "last_page": last_page,
        "links": links,
    }


@router.get(
    "",
    summary="Daftar manhole",
    responses={
        200: {
            "description": "Daftar manhole dengan pagination",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "current_page": 1,
                            "data": [_MH_ITEM_EXAMPLE],
                            "per_page": 15,
                            "total": 5286,
                            "last_page": 353,
                            "from": 1,
                            "to": 15,
                            "next_page_url": "https://psait-x-pad.onrender.com/api/ipal/manholes?page=2",
                        },
                    }
                }
            },
        }
    },
)
def list_manholes(
    request: Request,
    page: int = Query(1, ge=1, description="Nomor halaman"),
    per_page: int = Query(15, ge=1, le=500, description="Jumlah item per halaman (max 500)"),
    kecamatan: Optional[str] = Query(None, description="Filter kecamatan"),
    desa: Optional[str] = Query(None, description="Filter desa/kelurahan"),
    kondisi_mh: Optional[str] = Query(None, description="Filter kondisi manhole"),
    risiko: Optional[str] = Query(None, description="Filter tingkat risiko"),
    klasifikasi: Optional[str] = Query(None, description="Filter klasifikasi risiko"),
    status: Optional[str] = Query(None, description="Filter status aset: `baik`, `perbaikan`, `rusak`"),
    bentuk: Optional[str] = Query(None, description="Filter bentuk manhole"),
    material_mh: Optional[str] = Query(None, description="Filter material manhole"),
    sektor: Optional[int] = Query(None, description="Filter sektor (1, 2, atau 3)"),
    wilayah: Optional[str] = Query(None, description="Filter wilayah"),
    search: Optional[str] = Query(None, description="Cari berdasarkan kode manhole, desa, atau kecamatan"),
):
    """
    Mengembalikan daftar manhole dengan **pagination** dan opsi **filter**.

    Gunakan endpoint `/api/ipal/manholes/filters` untuk melihat semua nilai filter yang tersedia.
    """
    items = _filter_manholes(desa, kecamatan, kondisi_mh, risiko, klasifikasi, status, bentuk, material_mh, sektor, wilayah, search)
    total = len(items)
    start = (page - 1) * per_page
    page_items = items[start: start + per_page]
    pagination = _build_pagination(request, page, per_page, total)
    return {
        "success": True,
        "data": {"current_page": page, "data": page_items, "per_page": per_page, "total": total, **pagination},
    }


@router.get(
    "/filters",
    summary="Opsi filter manhole",
    responses={
        200: {
            "description": "Daftar nilai unik untuk setiap field filter",
            "content": {"application/json": {"example": _FILTERS_EXAMPLE}},
        }
    },
)
def get_filters():
    """
    Mengembalikan semua **nilai unik** yang tersedia untuk setiap field filter manhole.

    Gunakan response ini untuk mengisi dropdown/select pada UI filter.
    """
    items = data_loader.manholes

    def distinct(field):
        return sorted({m[field] for m in items if m[field] is not None})

    return {
        "success": True,
        "data": {
            "kondisi_mh": distinct("kondisi_mh"),
            "risiko": distinct("risiko"),
            "klasifikasi": distinct("klasifikasi"),
            "kecamatan": distinct("kecamatan"),
            "bentuk": distinct("bentuk"),
            "material_mh": distinct("material_mh"),
            "status": distinct("status"),
            "sektor": sorted({m["sektor"] for m in items if m["sektor"] is not None}),
            "wilayah": distinct("wilayah"),
        },
    }


@router.get(
    "/geojson",
    summary="GeoJSON manhole untuk peta",
    responses={
        200: {
            "description": "GeoJSON FeatureCollection — langsung bisa dipakai di Leaflet / MapLibre",
            "content": {"application/json": {"example": _GEOJSON_EXAMPLE}},
        }
    },
)
def get_geojson(
    kecamatan: Optional[str] = Query(None, description="Filter kecamatan"),
    kondisi_mh: Optional[str] = Query(None, description="Filter kondisi manhole"),
    risiko: Optional[str] = Query(None, description="Filter tingkat risiko"),
    status: Optional[str] = Query(None, description="Filter status aset"),
    sektor: Optional[int] = Query(None, description="Filter sektor"),
    wilayah: Optional[str] = Query(None, description="Filter wilayah"),
):
    """
    Mengembalikan **GeoJSON FeatureCollection** semua manhole yang bisa langsung digunakan sebagai layer peta.

    - Geometry: `Point` [longitude, latitude] — koordinat WGS84
    - Properties mencakup: kode, kondisi, risiko, klasifikasi, status, kecamatan, sektor
    """
    items = _filter_manholes(kecamatan=kecamatan, kondisi_mh=kondisi_mh, risiko=risiko, status=status, sektor=sektor, wilayah=wilayah)
    features = [
        {
            "type": "Feature",
            "geometry": m["geometry"],
            "properties": {
                "id": m["id"],
                "kode_manhole": m["kode_manhole"],
                "bentuk": m["bentuk"],
                "material_mh": m["material_mh"],
                "kondisi_mh": m["kondisi_mh"],
                "risiko": m["risiko"],
                "klasifikasi": m["klasifikasi"],
                "status": m["status"],
                "desa": m["desa"],
                "kecamatan": m["kecamatan"],
                "sektor": m["sektor"],
                "aduan_count": m["aduan_count"],
            },
        }
        for m in items if m["geometry"]
    ]
    return {"type": "FeatureCollection", "features": features}


@router.get(
    "/{manhole_id}",
    summary="Detail manhole",
    responses={
        200: {
            "description": "Data lengkap satu manhole",
            "content": {"application/json": {"example": {"success": True, "data": _MH_ITEM_EXAMPLE}}},
        },
        404: {"description": "Manhole tidak ditemukan"},
    },
)
def get_manhole(manhole_id: int):
    """
    Mengembalikan **data lengkap** satu manhole berdasarkan ID numerik.

    ID manhole bisa diperoleh dari response endpoint list atau GeoJSON (`properties.id`).
    """
    for m in data_loader.manholes:
        if m["id"] == manhole_id:
            return {"success": True, "data": m}
    raise HTTPException(status_code=404, detail="Manhole not found")
