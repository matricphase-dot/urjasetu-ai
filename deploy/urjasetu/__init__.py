"""
UrjaSetu AI — Autonomous Energy Intelligence for Indian Buildings.

A retrofit, software-first brain that connects to a building's existing smart
meter, cheap sensors and HVAC controls, then autonomously cuts energy cost
25–40% with a hard comfort constraint.

Submodules:
  tariff    — Time-of-Day tariff intelligence
  weather   — ambient temperature & rooftop solar models
  occupancy — zone occupancy schedules & forecasting hooks
  control   — the comfort-constrained optimization brain
  building  — physics-based digital twin of the building
  twin      — day simulator & A/B comparison
  anomaly   — fault detection & ₹-quantified work orders
  report    — CLI savings report
"""

__version__ = "1.0.0"

from .tariff import tariff_at, is_peak, TARIFF, GRID_CO2      # noqa: F401
from .weather import tout, solar_kw, cop_at                    # noqa: F401
from .occupancy import occ_of, occ_ahead                       # noqa: F401
from .control import BATT_CAP                                  # noqa: F401
from .building import make_state, step, ZDEF, COMF_LO, COMF_HI, set_scale  # noqa: F401
from .twin import simulate_day, compare, DayResult             # noqa: F401
# note: build_report lives in urjasetu.report (kept out of the package
# namespace so `python -m urjasetu.report` runs without a re-import warning)
