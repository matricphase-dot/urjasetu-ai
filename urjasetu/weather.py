"""
UrjaSetu AI — weather & solar models.
Deterministic, Mumbai-like curves used by the digital twin.
Swap `tout()` for live IMD/OpenWeather feeds and `solar_kw()` for a
trained irradiance model in production — the interfaces stay identical.
"""

import math

SOLAR_CAP = 130.0   # kWp rooftop + canopy PV


def tout(h: float) -> float:
    """Ambient temperature (°C) at hour-of-day `h` — Mumbai-like diurnal curve."""
    return max(25.0, 27.0 + 7.0 * math.sin(math.pi * (h - 6.0) / 14.0))


def solar_kw(h: float) -> float:
    """Rooftop PV output (kW) at hour-of-day `h` (clear-sky model with mild wobble)."""
    if h < 6.4 or h > 18.6:
        return 0.0
    x = (h - 6.4) / 12.2
    w = 0.9 + 0.08 * math.sin(h * 2.1) + 0.05 * math.sin(h * 4.7 + 1.0)
    return max(0.0, SOLAR_CAP * math.sin(math.pi * x) * w)


def cop_at(t_out: float) -> float:
    """Chiller COP degrades as ambient temperature rises (physics-informed)."""
    return max(2.2, 2.9 - (t_out - 30.0) * 0.05)
