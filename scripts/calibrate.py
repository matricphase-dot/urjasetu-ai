#!/usr/bin/env python3
"""
UrjaSetu AI — calibrate the digital twin to YOUR building's real meter data.

Usage:
    python3 scripts/calibrate.py data/sample_meter.csv
    python3 scripts/calibrate.py my_college_export.csv --days 14

Input CSV format (hourly or sub-hourly), one row per reading:
    timestamp,kw
    2026-10-11 00:00,28.4
    2026-10-11 01:00,26.9
    ...

Output: the SCALE factor that makes the twin's baseline match your building,
the projected AI savings at your scale, and a calibration.json you can persist.
Then run:  python3 -m urjasetu.report   (after set_scale in a shell/session)
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from urjasetu import simulate_day, set_scale  # noqa: E402


def load_avg_daily_kwh(path: Path) -> float:
    total_kw = 0.0
    n = 0
    stamps = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            total_kw += float(row["kw"])
            n += 1
            stamps.add(str(row.get("timestamp", ""))[:10])
    if n == 0:
        raise SystemExit("No rows found — expected columns: timestamp,kw")
    days = max(1, len(stamps))
    readings_per_day = n / days
    avg_interval_h = 24.0 / readings_per_day     # 1.0 for hourly data
    kwh_per_day = total_kw * avg_interval_h / days
    return kwh_per_day


def main() -> None:
    ap = argparse.ArgumentParser(description="Fit the UrjaSetu twin to a real meter export")
    ap.add_argument("csv", type=Path, help="meter export CSV with columns timestamp,kw")
    args = ap.parse_args()

    kwh_per_day = load_avg_daily_kwh(args.csv)
    print(f"Parsed {args.csv.name}: {kwh_per_day:,.0f} kWh/day average")

    twin_default = simulate_day(False, None, 4.0)
    scale = kwh_per_day / twin_default.kwh
    set_scale(scale)

    base = simulate_day(False, None, 4.0)
    ai = simulate_day(True, None, 4.0)
    saving_pct = 100.0 * (1 - ai.kwh / base.kwh)
    saving_cost = base.cost_final - ai.cost_final

    print(f"Twin baseline (SCALE=1.0) : {twin_default.kwh:,.0f} kWh/day")
    print(f"Calibration SCALE factor  : {scale:.4f}")
    print(f"Verified twin @ your scale: {base.kwh:,.0f} kWh/day")
    print(f"Projected AI consumption  : {ai.kwh:,.0f} kWh/day  (−{saving_pct:.1f}%)")
    print(f"Projected cost saving     : ₹{saving_cost:,.0f}/day → ₹{saving_cost*312/1e5:.1f} Lakh/yr")

    out = {
        "calibrated_from": args.csv.name,
        "avg_daily_kwh": round(kwh_per_day, 1),
        "scale": round(scale, 4),
        "ai_saving_pct": round(saving_pct, 1),
        "ai_saving_rs_per_day": round(saving_cost),
    }
    Path("calibration.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Wrote calibration.json ✓")


if __name__ == "__main__":
    main()
