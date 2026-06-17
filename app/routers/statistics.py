from fastapi import APIRouter, Query
from typing import Optional
from app import data_loader

router = APIRouter(prefix="/api/ipal", tags=["statistics"])

_STATS_EXAMPLE = {
    "success": True,
    "data": {
        "manhole": {
            "total": 5286,
            "by_status": {"baik": 5286, "perbaikan": 0, "rusak": 0},
            "by_kondisi": {
                "Lancar": 4654,
                "Tidak Diketahui": 248,
                "Kurang Lancar": 185,
                "Tidak Lancar": 199,
            },
        },
        "pipa": {
            "total": 458,
            "total_panjang_km": 187.61,
            "by_status": {"baik": 458, "perbaikan": 0, "rusak": 0},
            "by_fungsi": {"Lateral": 385, "Induk": 51, "Glontor": 22},
        },
    },
    "filters_applied": {"wilayah": None, "kecamatan": None},
}


@router.get(
    "/statistics",
    summary="Statistik jaringan IPAL",
    responses={
        200: {
            "description": "Statistik berhasil diambil",
            "content": {"application/json": {"example": _STATS_EXAMPLE}},
        }
    },
)
def get_statistics(
    wilayah: Optional[str] = Query(
        None,
        description="Filter berdasarkan wilayah/kecamatan (berlaku untuk manhole dan pipa)",
        example="Gondokusuman",
    ),
    kecamatan: Optional[str] = Query(
        None,
        description="Filter berdasarkan kecamatan (berlaku untuk manhole saja)",
        example="Wirobrajan",
    ),
):
    """
    Mengembalikan ringkasan statistik jaringan IPAL:

    - **Total manhole** dan distribusi berdasarkan status & kondisi
    - **Total pipa**, panjang jaringan (km), dan distribusi berdasarkan status & fungsi

    Gunakan parameter `wilayah` atau `kecamatan` untuk melihat statistik area tertentu.
    """
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
