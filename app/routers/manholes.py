from fastapi import APIRouter, Query
from typing import Optional
from app import data_loader

router = APIRouter(prefix="/api/ipal/manholes", tags=["manholes"])


def _filter_manholes(
    desa: Optional[str] = None,
    kecamatan: Optional[str] = None,
    kondisi_mh: Optional[str] = None,
    risiko: Optional[str] = None,
    klasifikasi: Optional[str] = None,
    status: Optional[str] = None,
    bentuk: Optional[str] = None,
    material_mh: Optional[str] = None,
    sektor: Optional[int] = None,
    wilayah: Optional[str] = None,
    search: Optional[str] = None,
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


@router.get("")
def list_manholes(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=500),
    desa: Optional[str] = None,
    kecamatan: Optional[str] = None,
    kondisi_mh: Optional[str] = None,
    risiko: Optional[str] = None,
    klasifikasi: Optional[str] = None,
    status: Optional[str] = None,
    bentuk: Optional[str] = None,
    material_mh: Optional[str] = None,
    sektor: Optional[int] = None,
    wilayah: Optional[str] = None,
    search: Optional[str] = None,
):
    items = _filter_manholes(desa, kecamatan, kondisi_mh, risiko, klasifikasi, status, bentuk, material_mh, sektor, wilayah, search)
    total = len(items)
    last_page = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    page_items = items[start: start + per_page]

    # Exclude heavy geometry from list
    slim = [{k: v for k, v in m.items() if k != "geometry"} for m in page_items]
    return {
        "success": True,
        "data": {
            "data": slim,
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page,
        },
    }


@router.get("/filters")
def get_filters():
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


@router.get("/geojson")
def get_geojson(
    kecamatan: Optional[str] = None,
    kondisi_mh: Optional[str] = None,
    risiko: Optional[str] = None,
    status: Optional[str] = None,
    sektor: Optional[int] = None,
    wilayah: Optional[str] = None,
):
    items = _filter_manholes(kecamatan=kecamatan, kondisi_mh=kondisi_mh, risiko=risiko, status=status, sektor=sektor, wilayah=wilayah)
    features = []
    for m in items:
        if not m["geometry"]:
            continue
        features.append({
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
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/{manhole_id}")
def get_manhole(manhole_id: int):
    for m in data_loader.manholes:
        if m["id"] == manhole_id:
            return {"success": True, "data": m}
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Manhole not found")
