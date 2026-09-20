"""UrjaSetu AI — Vercel serverless function: POST /api/optimize
Returns the next 15-minute control cycle the edge would write over Modbus/BACnet."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI  # noqa: E402

from urjasetu import make_state, step  # noqa: E402

app = FastAPI()


@app.api_route("/{path:path}", methods=["POST", "GET"])
def optimize(path: str):
    s = make_state()
    step(s, 15.0, True)
    return {
        "cycle_min": 15,
        "zones": [{"zone": z.name, "setpoint_c": z.setp, "mode": z.mode,
                   "occupancy_frac": round(z.occ, 2), "hvac_kw": round(z.hvac, 2)}
                  for z in s.zones],
        "battery": {"soc_kwh": round(s.soc, 1), "power_kw": round(s.batt_pw, 1)},
        "comfort_band_c": [23.0, 26.5],
        "write_targets": ["AHU setpoints (Modbus FC16)", "battery inverter dispatch", "work orders"],
    }
