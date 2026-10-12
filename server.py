#!/usr/bin/env python3
"""CompostMitra 2.0 — FastAPI + React PWA Production Server.

Replaces Streamlit with a high-performance, asynchronous FastAPI backend
that serves both the compiled React 19 PWA and agronomic API endpoints.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Add repo root to sys.path so scripts can be imported cleanly
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.blender import blend, load_catalog
from scripts.convex_optimizer import balance_available_wastes, synthesize_optimal_recipe
from scripts.kinetic_digital_twin import simulate_composting_pile

app = FastAPI(
    title="CompostMitra 2.0 API",
    description="Offline-first urban composting companion & biophysical decision support.",
    version="2.0.0",
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic Request / Response Models
# ---------------------------------------------------------------------------

class BlendRequest(BaseModel):
    weights: Dict[str, float] = Field(..., description="Wet weight proportions summing to 1.0")


class BalanceWasteRequest(BaseModel):
    waste_masses_kg: Dict[str, float] = Field(..., description="Available waste masses in kg")
    cn_min: float = 25.0
    cn_max: float = 35.0
    moist_min: float = 50.0
    moist_max: float = 65.0


class SimulationRequest(BaseModel):
    wet_mass_kg: float = 20.0
    moisture_pct: float = 58.0
    duration_days: float = 45.0
    ambient_temp_c: float = 26.0
    insulation: str = "moderate"


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Healthcheck endpoint for Docker and monitoring."""
    return {
      "status": "healthy",
      "service": "CompostMitra 2.0",
      "frontend": "React 19 + Tailwind PWA",
      "server": "FastAPI + Uvicorn",
      "offline_ready": True,
    }


@app.get("/api/ingredients")
def get_ingredients() -> Dict[str, Any]:
    """Return all verified feedstock ingredients."""
    catalog = load_catalog()
    return {"count": len(catalog), "ingredients": catalog}


@app.post("/api/blend")
def calculate_blend(req: BlendRequest) -> Dict[str, Any]:
    """Calculate deterministic Cornell mass-balance stoichiometry."""
    try:
        catalog = load_catalog()
        result = blend(req.weights, catalog)
        return {"success": True, "blend": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/balance-waste")
def balance_waste(req: BalanceWasteRequest) -> Dict[str, Any]:
    """Run Linear Programming to calculate minimal bulking agent addition."""
    try:
        opt_res = balance_available_wastes(
            waste_masses_kg=req.waste_masses_kg,
            cn_range=(req.cn_min, req.cn_max),
            moist_range=(req.moist_min, req.moist_max),
        )
        return opt_res.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/digital-twin")
def run_simulation(req: SimulationRequest) -> Dict[str, Any]:
    """Run biophysical dynamic kinetic ODE composting simulation."""
    try:
        sim_res = simulate_composting_pile(
            initial_wet_mass_kg=req.wet_mass_kg,
            initial_moisture_pct=req.moisture_pct,
            duration_days=req.duration_days,
            ambient_temp_c=req.ambient_temp_c,
            insulation_level=req.insulation,
        )
        return sim_res.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Static PWA Frontend Mounting
# ---------------------------------------------------------------------------

FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    # Mount compiled static assets
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    def fallback_index() -> Dict[str, Any]:
        return {
            "message": "CompostMitra 2.0 API is running. Build frontend with 'npm run build' inside frontend/ to serve PWA at root.",
            "health": "/api/health",
            "ingredients": "/api/ingredients",
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "3000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
