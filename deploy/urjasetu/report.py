"""
UrjaSetu AI — savings report (CLI).

Run:  python3 -m urjasetu.report
Prints the headline numbers used on the pitch deck, straight from the twin.
"""

from .twin import simulate_day, compare

DAYS_PER_YEAR = 312   # 6-day commercial week


def build_report(dt: float = 2.0, fault_zone: int = 1) -> dict:
    base = simulate_day(False, None, dt)
    ai = simulate_day(True, None, dt)
    fault = simulate_day(True, fault_zone, dt)
    cmp_ = compare(base, ai)
    cmp_["fault"] = {
        "zone": fault_zone,
        "extra_rs_per_day": round(fault.cost_final - ai.cost_final, 2),
        "note": "stuck AHU valve, +60% draw — detected & isolated by the AI in minutes",
    }
    cmp_["annual"] = {
        "saving_rs": round(cmp_["cost"]["saving_rs_per_day"] * DAYS_PER_YEAR),
        "co2_tonnes": round((base.co2 - ai.co2) * DAYS_PER_YEAR / 1000.0, 1),
    }
    return cmp_


def fmt_rs(x: float) -> str:
    return f"₹{x:,.0f}"


def main() -> None:
    r = build_report()
    line = "-" * 58
    print(line)
    print("UrjaSetu AI — digital-twin day report")
    print("90,000 sq ft Mumbai commercial building · TOD tariff · 130 kWp PV + 150 kWh BESS")
    print(line)
    rows = [
        ("Energy", f"{r['kwh']['baseline']:>8.0f} kWh", f"{r['kwh']['ai']:>8.0f} kWh", f"-{r['kwh']['saving_pct']:.1f}%"),
        ("Cost", fmt_rs(r['cost']['baseline']).rjust(10), fmt_rs(r['cost']['ai']).rjust(10), f"-{r['cost']['saving_pct']:.1f}%"),
        ("Peak demand", f"{r['peak_kw']['baseline']:>8.1f} kW", f"{r['peak_kw']['ai']:>8.1f} kW", f"-{r['peak_kw']['cut_pct']:.1f}%"),
        ("CO2", f"{r['co2_kg']['baseline']:>8.0f} kg", f"{r['co2_kg']['ai']:>8.0f} kg", f"-{r['co2_kg']['avoided_kg_per_day']:.0f} kg/d"),
        ("Comfort", f"{r['comfort_pct']['baseline']:>8.1f}%", f"{r['comfort_pct']['ai']:>8.1f}%", "improved" if r['comfort_pct']['improved'] else "check"),
    ]
    print(f"{'Metric':<12}{'Baseline':>18}{'UrjaSetu AI':>18}{'   Δ':>14}")
    for m, b, a, d in rows:
        print(f"{m:<12}{b:>18}{a:>18}{d:>14}")
    print(line)
    sav = r['annual']['saving_rs']
    print(f"Projected annual saving : {fmt_rs(sav)}  (≈ ₹{sav/1e5:.1f} Lakh · {DAYS_PER_YEAR} operating days)")
    print(f"Projected annual CO2 cut: {r['annual']['co2_tonnes']} tonnes")
    print(f"Untreated fault costs   : {fmt_rs(r['fault']['extra_rs_per_day'])}/day  ({r['fault']['note']})")
    print(line)


if __name__ == "__main__":
    main()
