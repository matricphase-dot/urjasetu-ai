"""
UrjaSetu AI — the building & the digital-twin physics step.

This is the same physics that powers the live dashboard demo. Every cycle:
  1. occupancy is set per zone
  2. the control brain picks setpoints + battery dispatch
  3. zone thermal dynamics integrate (envelope gains, people/equipment gains,
     COP-degraded cooling power, exponential drive toward setpoint)
  4. energy balance closes: grid = load + charge − solar_used − discharge (≥ 0)
  5. cost / CO2 / comfort / peak accumulators update
"""

import math

from .tariff import tariff_at, is_peak, GRID_CO2
from .weather import tout, solar_kw, cop_at
from .occupancy import occ_of
from .control import zone_policy, battery_dispatch, BATT_CAP

# 8 zones · 4 floors · ~90,000 sq ft Mumbai commercial building
ZDEF = [
    dict(name="Lobby & Reception", floor="Ground",  type="lobby",  cap=60),
    dict(name="Open Office L1",    floor="Floor 1", type="office", cap=80),
    dict(name="Conference Nimbus", floor="Floor 1", type="conf",   cap=16),
    dict(name="Open Office L2",    floor="Floor 2", type="office", cap=80),
    dict(name="Conference Monsoon",floor="Floor 2", type="conf",   cap=16),
    dict(name="Server & UPS Room", floor="Floor 2", type="server", cap=0),
    dict(name="Cafeteria",         floor="Ground",  type="cafe",   cap=70),
    dict(name="Lab Annex",         floor="Floor 3", type="lab",    cap=45),
]

COMF_LO, COMF_HI = 23.0, 26.5   # comfort band °C (ECBC/ISHRAE-aligned)

# Calibration hook: multiply all thermal/base loads after fitting to a real meter.
SCALE = 1.0


def set_scale(v: float) -> None:
    """Scale building loads to match a real meter (see scripts/calibrate.py)."""
    global SCALE
    SCALE = float(v)


class ZoneState:
    __slots__ = ("name", "floor", "type", "cap", "Tin", "hvac", "mode", "setp", "occ")

    def __init__(self, d):
        self.name, self.floor, self.type, self.cap = d["name"], d["floor"], d["type"], d["cap"]
        self.Tin = 27.0
        self.hvac = 0.0
        self.mode = "OFF"
        self.setp = 0.0
        self.occ = 0.0


class BuildingState:
    """Everything the twin remembers. Reset daily via make_state()."""

    def __init__(self):
        self.time = 360.0            # sim-minutes since midnight (06:00 start)
        self.soc = 0.32 * BATT_CAP   # battery starts at 32%
        self.zones = [ZoneState(d) for d in ZDEF]
        self.cum_kwh = 0.0
        self.cum_cost = 0.0
        self.cum_co2 = 0.0
        self.cum_solar_kwh = 0.0
        self.comfort_ok = 0.0
        self.comfort_tot = 0.0
        self.peak_grid = 0.0
        self.grid_kw = 0.0
        self.solar_kw = 0.0
        self.solar_use = 0.0
        self.batt_pw = 0.0           # + discharge / − charge
        self.hvac_kw = 0.0
        self.base_kw = 0.0
        self.fault = None            # {"zone": i, "active": True, "fixed": False}


def make_state() -> BuildingState:
    return BuildingState()


def step(s: BuildingState, dt: float, ai_on: bool) -> BuildingState:
    """Advance the twin by `dt` sim-minutes."""
    h = s.time / 60.0
    hvac = 0.0
    base = (14.0 + 12.0) * SCALE          # lifts/pumps/AHU aux + IT (server)

    for i, z in enumerate(s.zones):
        z.occ = occ_of(z.type, h)
        setp, mode = zone_policy(z, h, ai_on)
        z.setp, z.mode = setp, mode
        to = tout(h)

        if mode == "OFF":
            z.hvac = 0.0
            z.Tin += (to - z.Tin) * (1.0 - math.exp(-dt / 45.0))
        else:
            kenv = (0.18 + z.cap * 0.030) * SCALE                    # envelope coupling, kW-th/°C
            thermal = kenv * max(0.0, to - setp) + z.occ * z.cap * 0.12 * SCALE
            if z.type == "server":
                thermal = kenv * max(0.0, to - setp) + 8.0 * SCALE   # IT heat load
            cap_therm = 12.0 if z.type == "server" else (20.0 + z.cap * 0.55) * SCALE
            delivered = min(thermal, cap_therm)

            fault_mul, overcool = 1.0, False
            if s.fault and s.fault.get("zone") == i and s.fault.get("active") and not s.fault.get("fixed"):
                fault_mul, overcool = 1.6, True                      # stuck valve: +60% draw, over-cooling
            z.hvac = delivered / cop_at(to) * fault_mul

            if overcool:
                z.Tin += ((setp - 2.2) - z.Tin) * (1.0 - math.exp(-dt / 25.0))
            else:
                tau = max(6.0, 16.0 - abs(z.Tin - setp) * 2.0)
                z.Tin += (setp - z.Tin) * (1.0 - math.exp(-dt / tau))

        hvac += z.hvac
        if z.type != "server":
            base += 1.8 * SCALE + z.occ * z.cap * 0.045 * SCALE      # lighting & plug loads

    load = hvac + base
    sol = solar_kw(h)
    charge, dis, solar_use = battery_dispatch(s, load, sol, h, ai_on)
    grid = max(0.0, load + charge - solar_use - dis)

    dth = dt / 60.0
    s.cum_kwh += grid * dth
    s.cum_cost += grid * tariff_at(h) * dth
    s.cum_co2 += grid * GRID_CO2 * dth
    s.cum_solar_kwh += solar_use * dth
    s.peak_grid = max(s.peak_grid, grid)

    for z in s.zones:
        if z.occ > 0.06:
            s.comfort_tot += dt
            if COMF_LO - 0.4 <= z.Tin <= COMF_HI + 0.6:
                s.comfort_ok += dt

    s.soc = max(0.0, min(BATT_CAP, s.soc + (charge - dis) * dth))
    s.grid_kw, s.solar_kw, s.solar_use = grid, sol, solar_use
    s.batt_pw, s.hvac_kw, s.base_kw = dis - charge, hvac, base
    s.time += dt
    return s
