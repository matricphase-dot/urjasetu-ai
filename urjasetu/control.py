"""
UrjaSetu AI — the control brain.

zone_policy(): per-zone HVAC setpoint decision, made fresh every cycle.
  - BASELINE policy: what a "dumb" building does today (timer, 23°C, zero awareness).
  - URJASETU policy: occupancy-aware, tariff-aware, comfort-constrained.

battery_dispatch(): solar-first charging, pre-peak grid top-up, peak discharge.
Every decision here honours one hard rule: *comfort is a constraint, never a casualty*.
"""

from .tariff import is_peak
from .occupancy import occ_ahead

BATT_CAP = 150.0   # kWh
BATT_MAX = 40.0    # kW max charge/discharge
GRID_TOPUP_UNTIL = 126.0   # stop grid charging above this SoC (kWh)
TOPUP_RATE = 25.0          # kW grid charging cap


def zone_policy(z, h: float, ai_on: bool):
    """Return (setpoint °C, mode) for a zone at hour-of-day `h`.

    Modes: OFF · SETBACK (drift, no cooling) · COOL · PRE-COOL (banking coolth).
    """
    if not ai_on:
        # ---------------- BASELINE: timer-scheduled, zero awareness ----------------
        if z.type == "server":
            return 22.0, "COOL"                       # over-cooled 24/7 out of fear
        if 6.0 <= h < 22.0:
            return 23.0, "COOL"                       # flat-out whether empty or full
        return 0.0, "OFF"

    # ---------------- URJASETU: occupancy + tariff + comfort-constrained ----------------
    if z.type == "server":
        return 24.0, "COOL"                           # IT-safe, minus the fear margin

    if z.occ > 0.06:                                  # zone is occupied
        if is_peak(h):
            return 26.0, "COOL"                       # coast through ₹13.4 peak
        if 16.5 <= h < 18.0:
            return 24.5, "PRE-COOL"                   # bank coolth before peak
        return 25.5, "COOL"                           # efficient comfort band

    if occ_ahead(z.type, h) > 0.30:                   # meeting starting within 1 h
        return 24.3, "PRE-COOL"
    if 5.5 <= h < 22.5:
        return 28.5, "SETBACK"                        # empty → let it drift
    return 0.0, "OFF"


def battery_dispatch(s, load: float, sol: float, h: float, ai_on: bool):
    """Return (charge_kw, discharge_kw) for this cycle. Baseline batteries sit idle."""
    charge = 0.0
    dis = 0.0
    solar_use = min(sol, load)

    if ai_on:
        if sol > load and s.soc < BATT_CAP:
            # 1) free solar surplus first — never let sunshine export itself
            charge = min(BATT_MAX, sol - load, (BATT_CAP - s.soc) * 2.0)
        elif 16.0 <= h < 18.0 and s.soc < GRID_TOPUP_UNTIL:
            # 2) top up on ₹9.2 pre-peak grid power
            charge = min(TOPUP_RATE, GRID_TOPUP_UNTIL - s.soc)

        net_load = load + charge - solar_use
        if is_peak(h) and s.soc > 10.0:
            # 3) shave the ₹13.4/kWh evening peak
            dis = min(BATT_MAX, (s.soc - 8.0) * 4.0, net_load)

    return charge, dis, solar_use
