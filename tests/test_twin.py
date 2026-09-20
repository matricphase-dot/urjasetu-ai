"""
UrjaSetu AI — physics verification suite.
These tests ARE the feasibility argument: run `pytest -q` and the twin must
prove, mechanically, that the AI building saves >25% energy & >30% cost,
never violates comfort, and cuts peak demand — before a judge asks.
"""

import math

import pytest

from urjasetu import (
    simulate_day, compare, make_state, step, tariff_at, is_peak,
    BATT_CAP, COMF_LO, COMF_HI,
)


@pytest.fixture(scope="module")
def days():
    return simulate_day(False, None, 2.0), simulate_day(True, None, 2.0)


# ---------- tariff intelligence ----------
def test_tariff_boundaries():
    assert tariff_at(3.0) == 6.2
    assert tariff_at(7.0) == 8.0
    assert tariff_at(12.0) == 9.2
    assert tariff_at(17.999) == 9.2
    assert tariff_at(18.0) == 13.4
    assert tariff_at(21.999) == 13.4
    assert tariff_at(22.0) == 6.2
    assert is_peak(19.0) and not is_peak(15.0)


# ---------- headline results ----------
def test_energy_saving_above_25pct(days):
    b, a = days
    assert (1 - a.kwh / b.kwh) > 0.25


def test_cost_saving_above_30pct(days):
    b, a = days
    assert (1 - a.cost_final / b.cost_final) > 0.30


def test_peak_demand_cut(days):
    b, a = days
    assert a.peak < b.peak * 0.95


def test_comfort_improves_not_degrades(days):
    b, a = days
    assert a.comfort_pct >= 99.0
    assert a.comfort_pct > b.comfort_pct


def test_battery_stays_within_bounds():
    s = make_state()
    while s.time < 1440.0:
        step(s, 2.0, True)
        assert -1e-6 <= s.soc <= BATT_CAP + 1e-6


# ---------- physics sanity ----------
def test_grid_never_negative_and_energy_balance():
    s = make_state()
    while s.time < 1440.0:
        step(s, 2.0, True)
        assert s.grid_kw >= 0.0
        # load + charge − solar_used − discharge must equal grid (within eps)
        lhs = s.hvac_kw + s.base_kw + max(0.0, -s.batt_pw) - s.solar_use - max(0.0, s.batt_pw)
        assert abs(lhs - s.grid_kw) < 1e-6


def test_zones_cool_during_occupied_hours():
    s = make_state()
    seen_cool = False
    while s.time < 1440.0:
        step(s, 2.0, True)
        h = s.time / 60.0
        if 11.0 <= h <= 12.0:
            office = s.zones[1]
            if office.mode in ("COOL", "PRE-COOL") and office.Tin < COMF_HI + 1.0:
                seen_cool = True
    assert seen_cool


def test_determinism():
    r1, r2 = simulate_day(True, None, 4.0), simulate_day(True, None, 4.0)
    assert math.isclose(r1.cost_final, r2.cost_final, rel_tol=1e-12)


def test_compare_structure(days):
    b, a = days
    c = compare(b, a)
    assert c["cost"]["saving_rs_per_day"] > 0
    assert c["co2_kg"]["avoided_kg_per_day"] > 0
    assert c["comfort_pct"]["improved"] is True
