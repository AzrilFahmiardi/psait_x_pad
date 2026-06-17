from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app import data_loader

router = APIRouter(prefix="/api/ipal/pipes", tags=["pipes"])


def _filter_pipes(
    fungsi: Optional[str] = None,
    pipe_dia: Optional[float] = None,
    tahun: Optional[int] = None,
    status: Optional[str] = None,
    material: Optional[str] = None,
    wilayah: Optional[str] = None,
    search: Optional[str] = None,
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


@router.get("")
def list_pipes(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=500),
    fungsi: Optional[str] = None,
    pipe_dia: Optional[float] = None,
    tahun: Optional[int] = None,
    status: Optional[str] = None,
    material: Optional[str] = None,
    wilayah: Optional[str] = None,
    search: Optional[str] = None,
):
    items = _filter_pipes(fungsi, pipe_dia, tahun, status, material, wilayah, search)
    total = len(items)
    last_page = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    page_items = items[start: start + per_page]

    slim = [{k: v for k, v in p.items() if k != "geometry"} for p in page_items]
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
    items = data_loader.pipes

    def distinct(field):
        return sorted({p[field] for p in items if p[field] is not None})

    return {
        "success": True,
        "data": {
            "fungsi": distinct("fungsi"),
            "pipe_dia": sorted({p["pipe_dia"] for p in items if p["pipe_dia"] is not None}),
            "tahun": sorted({p["tahun"] for p in items if p["tahun"] is not None}),
            "status": distinct("status"),
            "material": distinct("material"),
            "wilayah": distinct("wilayah"),
        },
    }


@router.get("/geojson")
def get_geojson(
    fungsi: Optional[str] = None,
    tahun: Optional[int] = None,
    status: Optional[str] = None,
    wilayah: Optional[str] = None,
):
    items = _filter_pipes(fungsi=fungsi, tahun=tahun, status=status, wilayah=wilayah)
    features = []
    for p in items:
        if not p["geometry"]:
            continue
        features.append({
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
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/{pipe_id}")
def get_pipe(pipe_id: int):
    for p in data_loader.pipes:
        if p["id"] == pipe_id:
            return {"success": True, "data": p}
    raise HTTPException(status_code=404, detail="Pipe not found")
