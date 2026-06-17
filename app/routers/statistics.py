from fastapi import APIRouter, Query
from typing import Optional
from app import data_loader

router = APIRouter(prefix="/api/ipal", tags=["statistics"])


@router.get("/statistics")
def get_statistics(
    wilayah: Optional[str] = Query(None),
    kecamatan: Optional[str] = Query(None),
):
    manholes = data_loader.manholes
    pipes = data_loader.pipes

    if wilayah:
        manholes = [m for m in manholes if m["wilayah"] and wilayah.lower() in m["wilayah"].lower()]
        pipes = [p for p in pipes if p["wilayah"] and wilayah.lower() in p["wilayah"].lower()]
    if kecamatan:
        manholes = [m for m in manholes if m["kecamatan"] and kecamatan.lower() in m["kecamatan"].lower()]

    def count_by(items, field):
        result = {}
        for item in items:
            val = item.get(field)
            if val:
                result[val] = result.get(val, 0) + 1
        return result

    total_panjang = sum(p["length_km"] or 0 for p in pipes)

    mh_by_status = count_by(manholes, "status")
    pipe_by_status = count_by(pipes, "status")

    # Always include all three status keys (match production format)
    for key in ("baik", "perbaikan", "rusak"):
        mh_by_status.setdefault(key, 0)
        pipe_by_status.setdefault(key, 0)

    return {
        "success": True,
        "data": {
            "manhole": {
                "total": len(manholes),
                "by_status": mh_by_status,
                "by_kondisi": count_by(manholes, "kondisi_mh"),
            },
            "pipa": {
                "total": len(pipes),
                "total_panjang_km": round(total_panjang, 2),
                "by_status": pipe_by_status,
                "by_fungsi": count_by(pipes, "fungsi"),
            },
        },
        "filters_applied": {
            "wilayah": wilayah,
            "kecamatan": kecamatan,
        },
    }
