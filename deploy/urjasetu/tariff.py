"""
UrjaSetu AI — tariff intelligence.
Representative Mumbai commercial Time-of-Day (TOD) tariff, ₹/kWh.
Replace with your discom's actual TOD table (it's just a list of (hour, ₹/kWh)).
"""

# (start_hour, rate) — last row's rate extends to 24:00
TARIFF = [
    (0, 6.2),
    (6, 8.0),
    (10, 9.2),
    (18, 13.4),   # evening peak — the single most expensive window
    (22, 6.2),
]

# India average grid emission factor, kg CO2 per grid kWh (CEA-style value)
GRID_CO2 = 0.71


def tariff_at(h: float) -> float:
    """₹/kWh in effect at hour-of-day `h` (0–24)."""
    for i in range(len(TARIFF) - 1):
        if TARIFF[i][0] <= h < TARIFF[i + 1][0]:
            return TARIFF[i][1]
    return TARIFF[-1][1]


def is_peak(h: float) -> bool:
    """True inside the evening peak window (18:00–22:00)."""
    return 18.0 <= h < 22.0
