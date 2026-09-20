"""
UrjaSetu AI — anomaly detection & fault economics.

Production concept: every 15-minute cycle compares *expected* power (predicted
by the twin running shadow-mode with yesterday's model) against *actual* meter
power. Persistent residuals outside a CUSUM band = equipment fault.

Here we ship: (1) a CUSUM residual detector you can run on any kW series,
and (2) the fault-cost estimator that turns a stuck valve into "₹ per day" —
because maintenance budgets move when you speak in rupees.
"""

from typing import List, Tuple


def cusum_detect(values: List[float], expected: List[float],
                 threshold: float = 3.0, drift: float = 0.5) -> List[int]:
    """Return indices where cumulative positive residuals cross `threshold`.

    values/expected: same-length kW series. `drift` absorbs small noise.
    """
    if len(values) != len(expected):
        raise ValueError("series must be same length")
    s_pos = 0.0
    alerts: List[int] = []
    for i, (a, e) in enumerate(zip(values, expected)):
        resid = max(0.0, a - e - drift)
        s_pos = max(0.0, s_pos + resid)
        if s_pos > threshold:
            alerts.append(i)
            s_pos = 0.0
    return alerts


def estimate_daily_fault_cost(ai_day_cost: float, fault_day_cost: float) -> float:
    """₹/day a fault is burning = cost(fault day) − cost(same day, fault fixed)."""
    return max(0.0, fault_day_cost - ai_day_cost)


def work_order(zone_name: str, symptom: str, rs_per_day: float, severity: str = "HIGH") -> dict:
    """The deliverable facilities teams actually receive."""
    return {
        "title": f"[{severity}] {zone_name}: {symptom}",
        "estimated_loss_rs_per_day": round(rs_per_day, 2),
        "estimated_loss_rs_per_month": round(rs_per_day * 26, 2),
        "recommended_action": "Dispatch technician · inspect valve/actuator · verify with twin after repair",
        "sla": "24 hours" if severity == "HIGH" else "72 hours",
    }
