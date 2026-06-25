from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from gee_service import (
    analyze_area,
    build_report,
    earth_engine_config_status,
    get_tile_layer,
    initialize_earth_engine,
    list_areas,
)

app = FastAPI(
    title="CoolGrid Urban API",
    description="Physics-informed urban heat intelligence and cooling intervention optimization API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,https://urbanstaus.vercel.app",
        ).split(",")
        if origin.strip()
    ],
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health(deep: bool = Query(False, description="Verify live Earth Engine connectivity")) -> dict:
    config = earth_engine_config_status()
    if not deep:
        return {
            "status": "ok",
            "earth_engine": "configured" if config["has_project"] else "project-not-configured",
            "config": config,
        }
    try:
        initialize_earth_engine()
        gee = "ready"
    except RuntimeError as exc:
        gee = str(exc)
    return {"status": "ok", "earth_engine": gee, "config": config}


@app.get("/analyze")
def analyze(
    area: str = Query("mumbai", description="Area preset identifier"),
    start: str = Query("2024-03-01", description="Start date, YYYY-MM-DD"),
    end: str = Query("2024-05-31", description="End date, YYYY-MM-DD"),
) -> dict:
    try:
        return analyze_area(area=area, start=start, end=end)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc


@app.get("/areas")
def areas() -> list[dict]:
    return list_areas()


@app.get("/tiles/{layer}")
def tiles(layer: str) -> dict[str, str]:
    try:
        return get_tile_layer(layer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tile generation failed: {exc}") from exc


@app.get("/report", response_class=PlainTextResponse)
def report() -> PlainTextResponse:
    try:
        content = build_report()
        return PlainTextResponse(
            content,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=coolgrid-urban-decision-brief.md"},
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}") from exc


frontend_dist = Path(__file__).resolve().parent / "static"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
