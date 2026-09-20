"""
UrjaSetu AI — digital-twin day simulator & A/B comparison.

simulate_day() runs 06:00 → 24:00 at `dt`-minute resolution and returns
curves + KPIs for either the baseline building or the AI building.
This is the function the API, the CLI report and the tests all share.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .building import make_state, step, ZDEF


@dataclass
class DayResult:
    ai: bool
    dt: float
    t: List[float] = field(default_factory=list)      # sim-minutes
    grid: List[float] = field(default_factory=list)   # kW
    solar: List[float] = field(default_factory=list)  # kW
    cost: List[float] = field(default_factory=list)   # ₹ cumulative
    kwh: float = 0.0
    cost_final: float = 0.0
    co2: float = 0.0
    peak: float = 0.0
    comfort_pct: float = 100.0
    soc_final: float = 0.0
    solar_kwh: float = 0.0


def simulate_day(ai_on: bool, fault_zone: Optional[int] = None, dt: float = 2.0) -> DayResult:
    """Simulate one operating day. `fault_zone` injects a stuck AHU valve in that zone."""
    s = make_state()
    if fault_zone is not None:
        s.fault = {"zone": fault_zone, "active": True, "fixed": False}
    r = DayResult(ai=ai_on, dt=dt)
    while s.time < 1440.0:
        step(s, dt, ai_on)
        r.t.append(s.time)
        r.grid.append(s.grid_kw)
        r.solar.append(s.solar_kw)
        r.cost.append(s.cum_cost)
    r.kwh = s.cum_kwh
    r.cost_final = s.cum_cost
    r.co2 = s.cum_co2
    r.peak = s.peak_grid
    r.comfort_pct = 100.0 * s.comfort_ok / s.comfort_tot if s.comfort_tot > 0 else 100.0
    r.soc_final = s.soc
    r.solar_kwh = s.cum_solar_kwh
    return r


def compare(base: DayResult, ai: DayResult) -> dict:
    """Headline KPI comparison — the numbers that go on the slide."""
    return {
        "kwh": {"baseline": base.kwh, "ai": ai.kwh,
                "saving_pct": 100.0 * (1 - ai.kwh / base.kwh)},
        "cost": {"baseline": base.cost_final, "ai": ai.cost_final,
                 "saving_pct": 100.0 * (1 - ai.cost_final / base.cost_final),
                 "saving_rs_per_day": base.cost_final - ai.cost_final},
        "peak_kw": {"baseline": base.peak, "ai": ai.peak,
                    "cut_pct": 100.0 * (1 - ai.peak / base.peak)},
        "co2_kg": {"baseline": base.co2, "ai": ai.co2,
                   "avoided_kg_per_day": base.co2 - ai.co2},
        "comfort_pct": {"baseline": base.comfort_pct, "ai": ai.comfort_pct,
                        "improved": ai.comfort_pct >= base.comfort_pct},
    }


def zones() -> list:
    """Zone configuration exposed for the API/UI."""
    return ZDEF
