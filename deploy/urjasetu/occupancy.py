"""
UrjaSetu AI — occupancy intelligence.
Piecewise occupancy profiles per zone type, fraction of zone capacity 0..1.
In production these come from bookings + Wi-Fi/CO2/PIR feeds; the twin uses
representative schedules so behaviour is reproducible.
"""

# [hour, fraction] piecewise points
OCC = {
    "office": [[0, 0], [7, 0], [8, .15], [9, .65], [10, .9], [13, .85], [13.5, .5],
               [14, .62], [18, .8], [19, .3], [20, .1], [21, .02], [24, 0]],
    "lobby":  [[0, 0], [6, 0], [7, .1], [9, .5], [11, .4], [14, .3],
               [17, .55], [20, .15], [22, .02], [24, 0]],
    "conf":   [[0, 0], [8, 0], [9, .1], [10.5, .95], [12, .15], [14.5, .9],
               [16, .25], [17.5, .6], [19, .05], [24, 0]],
    "cafe":   [[0, 0], [7, 0], [8, .15], [9, .4], [10, .15], [12, .4], [12.5, .9],
               [14, .8], [15, .15], [17, .08], [19, .03], [24, 0]],
    "server": [[0, 1], [24, 1]],
    "lab":    [[0, 0], [8, 0], [9, .5], [12, .7], [13, .35], [14, .6],
               [17, .45], [18, .08], [19, 0], [24, 0]],
}


def _interp(points, h: float) -> float:
    if h <= points[0][0]:
        return points[0][1]
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        if a[0] <= h <= b[0]:
            return a[1] + (b[1] - a[1]) * ((h - a[0]) / (b[0] - a[0]))
    return points[-1][1]


def occ_of(zone_type: str, h: float) -> float:
    """Occupancy fraction (0..1) for a zone type at hour-of-day `h`."""
    return _interp(OCC[zone_type], h)


def occ_ahead(zone_type: str, h: float, horizon: float = 1.0, step: float = 0.25) -> float:
    """Max occupancy over the next `horizon` hours — used to pre-cool before meetings."""
    m = 0.0
    t = h + step
    while t <= h + horizon + 1e-9:
        m = max(m, occ_of(zone_type, t))
        t += step
    return m
