from fastapi import APIRouter, Query, Request, HTTPException
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


@router.get("")
def list_pipes(
    request: Request,
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
    start = (page - 1) * per_page
    page_items = items[start: start + per_page]

    pagination = _build_pagination(request, page, per_page, total)
    return {
        "success": True,
        "data": {
            "current_page": page,
            "data": page_items,
            "per_page": per_page,
            "total": total,
            **pagination,
        },
    }


@router.get("/filters")
def get_filters():
    items = data_loader.pipes

    def distinct_ordered(field):
        return sorted({p[field] for p in items if p[field] is not None})

    # Order fungsi by occurrence (most common first), then alpha fallback
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
