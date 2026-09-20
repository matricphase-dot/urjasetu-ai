"""UrjaSetu AI — Vercel serverless function: GET /api/receipt
Shareable 'savings receipt' — twin-verified, print-ready numbers."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI  # noqa: E402

from urjasetu import simulate_day, __version__  # noqa: E402

app = FastAPI()


@app.api_route("/{path:path}", methods=["GET"])
def receipt(path: str):
    b = simulate_day(False, None, 4.0)
    a = simulate_day(True, None, 4.0)
    return {
        "building": "Twin Tower BKC · 90,000 sq ft Mumbai (digital twin)",
        "projected_full_day": {
            "energy_kwh": {"baseline": round(b.kwh, 1), "ai": round(a.kwh, 1),
                           "saving_pct": round(100 * (1 - a.kwh / b.kwh), 1)},
            "cost_rs": {"baseline": round(b.cost_final), "ai": round(a.cost_final),
                        "saving_pct": round(100 * (1 - a.cost_final / b.cost_final), 1)},
            "peak_kw": {"baseline": round(b.peak, 1), "ai": round(a.peak, 1),
                        "cut_pct": round(100 * (1 - a.peak / b.peak), 1)},
            "comfort_pct": {"baseline": round(b.comfort_pct, 1), "ai": round(a.comfort_pct, 1)},
            "co2_avoided_kg_per_day": round(b.co2 - a.co2, 1),
        },
        "annualized_saving_rs": round((b.cost_final - a.cost_final) * 312),
        "badge": f"comfort-constrained · audit-grade · twin v{__version__}",
        "live_demo": "https://urjasetu-ai-eta.vercel.app",
    }
