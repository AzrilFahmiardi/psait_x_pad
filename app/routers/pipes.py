from fastapi import APIRouter, Query, Request, HTTPException
from typing import Optional
from app import data_loader

router = APIRouter(prefix="/api/ipal/pipes", tags=["pipes"])

_PIPE_ITEM_EXAMPLE = {
    "id": 1,
    "id_jalur": "ABBAH_3_J.6",
    "kode_pipa": "ABBAH_3_J.6-1",
    "pipe_dia": 20.0,
    "fungsi": "Lateral",
    "length_km": 0.78288021682,
    "tahun": 2011,
    "source": None,
    "material": None,
    "status": "baik",
    "wilayah": None,
    "aduan_count": 0,
    "geometry": {
        "type": "MultiLineString",
        "coordinates": [[[110.35254847, -7.77612845], [110.35330543, -7.77463210]]],
    },
}

_GEOJSON_EXAMPLE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "MultiLineString",
                "coordinates": [[[110.35254847, -7.77612845], [110.35330543, -7.77463210]]],
            },
            "properties": {
                "id": 1,
                "kode_pipa": "ABBAH_3_J.6-1",
                "id_jalur": "ABBAH_3_J.6",
                "pipe_dia": 20.0,
                "fungsi": "Lateral",
                "length_km": 0.78288021682,
                "tahun": 2011,
                "status": "baik",
                "aduan_count": 0,
            },
        }
    ],
}

_FILTERS_EXAMPLE = {
    "success": True,
    "data": {
        "fungsi": ["Lateral", "Induk", "Glontor"],
        "pipe_dia": [0.0, 20.0, 23.1, 40.0, 60.0, 80.0],
        "tahun": [0, 1994, 2008, 2009, 2011, 2014],
        "status": ["baik"],
        "material": [],
        "wilayah": [],
    },
}


def _filter_pipes(
    fungsi=None, pipe_dia=None, tahun=None, status=None,
    material=None, wilayah=None, search=None,
):
    items = data_loader.pipes
    if fungsi:
        items = [p for p in items if p["fungsi"] and p["fungsi"].lower() == fungsi.lower()]
    if pipe_dia is not None:
        items = [p for p in items if p["pipe_dia"] == pipe_dia]
    if tahun is not None:
        items = [p for p in items if p["tahun"] == tahun]
    if status:
        items = [p for p in items if p["status"] == status]
    if material:
        items = [p for p in items if p["material"] and material.lower() in p["material"].lower()]
    if wilayah:
        items = [p for p in items if p["wilayah"] and wilayah.lower() in p["wilayah"].lower()]
    if search:
        s = search.lower()
        items = [
            p for p in items
            if (p["kode_pipa"] and s in p["kode_pipa"].lower())
            or (p["id_jalur"] and s in p["id_jalur"].lower())
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
    summary="Daftar jaringan pipa",
    responses={
        200: {
            "description": "Daftar pipa dengan pagination",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "current_page": 1,
                            "data": [_PIPE_ITEM_EXAMPLE],
                            "per_page": 15,
                            "total": 458,
                            "last_page": 31,
                            "from": 1,
                            "to": 15,
                            "next_page_url": "https://psait-x-pad.onrender.com/api/ipal/pipes?page=2",
                        },
                    }
                }
            },
        }
    },
)
def list_pipes(
    request: Request,
    page: int = Query(1, ge=1, description="Nomor halaman"),
    per_page: int = Query(15, ge=1, le=500, description="Jumlah item per halaman (max 500)"),
    fungsi: Optional[str] = Query(None, description="Filter fungsi pipa"),
    pipe_dia: Optional[float] = Query(None, description="Filter diameter pipa (mm)"),
    tahun: Optional[int] = Query(None, description="Filter tahun pemasangan"),
    status: Optional[str] = Query(None, description="Filter status aset: `baik`, `perbaikan`, `rusak`"),
    material: Optional[str] = Query(None, description="Filter material pipa"),
    wilayah: Optional[str] = Query(None, description="Filter wilayah"),
    search: Optional[str] = Query(None, description="Cari berdasarkan kode pipa atau ID jalur"),
):
    """
    Mengembalikan daftar **jaringan pipa** dengan pagination dan opsi filter.

    Gunakan endpoint `/api/ipal/pipes/filters` untuk melihat semua nilai filter yang tersedia.
    """
    items = _filter_pipes(fungsi, pipe_dia, tahun, status, material, wilayah, search)
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
    summary="Opsi filter pipa",
    responses={
        200: {
            "description": "Daftar nilai unik untuk setiap field filter pipa",
            "content": {"application/json": {"example": _FILTERS_EXAMPLE}},
        }
    },
)
def get_filters():
    """
    Mengembalikan semua **nilai unik** yang tersedia untuk setiap field filter jaringan pipa.

    Gunakan response ini untuk mengisi dropdown/select pada UI filter.
    """
    items = data_loader.pipes

    def distinct_ordered(field):
        return sorted({p[field] for p in items if p[field] is not None})

    fungsi_order = ["Lateral", "Induk", "Glontor"]
    all_fungsi = {p["fungsi"] for p in items if p["fungsi"] is not None}
    fungsi_sorted = [f for f in fungsi_order if f in all_fungsi] + sorted(all_fungsi - set(fungsi_order))

    return {
        "success": True,
        "data": {
            "fungsi": fungsi_sorted,
            "pipe_dia": sorted({p["pipe_dia"] for p in items if p["pipe_dia"] is not None}),
            "tahun": sorted({p["tahun"] for p in items if p["tahun"] is not None}),
            "status": distinct_ordered("status"),
            "material": distinct_ordered("material"),
            "wilayah": distinct_ordered("wilayah"),
        },
    }


@router.get(
    "/geojson",
    summary="GeoJSON pipa untuk peta",
    responses={
        200: {
            "description": "GeoJSON FeatureCollection — langsung bisa dipakai di Leaflet / MapLibre",
            "content": {"application/json": {"example": _GEOJSON_EXAMPLE}},
        }
    },
)
def get_geojson(
    fungsi: Optional[str] = Query(None, description="Filter fungsi pipa"),
    tahun: Optional[int] = Query(None, description="Filter tahun pemasangan"),
    status: Optional[str] = Query(None, description="Filter status aset"),
    wilayah: Optional[str] = Query(None, description="Filter wilayah"),
):
    """
    Mengembalikan **GeoJSON FeatureCollection** semua segmen pipa yang bisa langsung digunakan sebagai layer peta.

    - Geometry: `MultiLineString` — koordinat WGS84 (dikonversi otomatis dari UTM Zone 49S)
    - Properties mencakup: kode, ID jalur, diameter, fungsi, panjang, tahun, status
    """
    items = _filter_pipes(fungsi=fungsi, tahun=tahun, status=status, wilayah=wilayah)
    features = [
        {
            "type": "Feature",
            "geometry": p["geometry"],
            "properties": {
                "id": p["id"],
                "kode_pipa": p["kode_pipa"],
                "id_jalur": p["id_jalur"],
                "pipe_dia": p["pipe_dia"],
                "fungsi": p["fungsi"],
                "length_km": p["length_km"],
                "tahun": p["tahun"],
                "status": p["status"],
                "aduan_count": p["aduan_count"],
            },
        }
        for p in items if p["geometry"]
    ]
    return {"type": "FeatureCollection", "features": features}


@router.get(
    "/{pipe_id}",
    summary="Detail pipa",
    responses={
        200: {
            "description": "Data lengkap satu segmen pipa",
            "content": {"application/json": {"example": {"success": True, "data": _PIPE_ITEM_EXAMPLE}}},
        },
        404: {"description": "Pipa tidak ditemukan"},
    },
)
def get_pipe(pipe_id: int):
    """
    Mengembalikan **data lengkap** satu segmen pipa berdasarkan ID numerik, termasuk geometry MultiLineString.

    ID pipa bisa diperoleh dari response endpoint list atau GeoJSON (`properties.id`).
    """
    for p in data_loader.pipes:
        if p["id"] == pipe_id:
            return {"success": True, "data": p}
    raise HTTPException(status_code=404, detail="Pipe not found")
