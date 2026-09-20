"""UrjaSetu AI — Vercel serverless function: POST /api/simulate
Full-day digital-twin run (curves + KPIs) with optional fault injection."""
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from urjasetu import simulate_day  # noqa: E402

app = FastAPI()


class SimRequest(BaseModel):
    ai: bool = True
    fault_zone: Optional[int] = None
    downsample_min: float = Field(15.0, ge=1, le=60)


@app.api_route("/{path:path}", methods=["POST", "GET"])
def simulate(path: str, req: Optional[SimRequest] = None):
    r = req or SimRequest()
    res = simulate_day(r.ai, r.fault_zone, dt=2.0)
    stride = max(1, int(r.downsample_min / res.dt))
    return {
        "ai": res.ai,
        "t_min": res.t[::stride],
        "grid_kw": [round(v, 2) for v in res.grid[::stride]],
        "solar_kw": [round(v, 2) for v in res.solar[::stride]],
        "cost_rs": [round(v, 1) for v in res.cost[::stride]],
        "kpi": {
            "kwh": round(res.kwh, 1), "cost_rs": round(res.cost_final, 1),
            "peak_kw": round(res.peak, 1), "co2_kg": round(res.co2, 1),
            "comfort_pct": round(res.comfort_pct, 2),
            "battery_soc_kwh_final": round(res.soc_final, 1),
        },
    }
