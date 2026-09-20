<div align="center">

# ⚡ UrjaSetu AI

### Autonomous Energy Intelligence for Indian Buildings

**A retrofit, software-first brain that cuts a building's energy cost 30%+ — without a BMS retrofit, without rewiring, and without a single comfort complaint.**

`Yuva Yodha Energy Tech Hackathon 2026 · Schneider Electric · Smart Buildings Track`

**🌐 LIVE DEMO:** [urjasetu-ai-eta.vercel.app](https://urjasetu-ai-eta.vercel.app) — live dashboard + working cloud API
**⚙️ Cloud API:** [`/api/health`](https://urjasetu-ai-eta.vercel.app/api/health) · [`/api/report`](https://urjasetu-ai-eta.vercel.app/api/report) (live savings) · `POST /api/simulate` `{"ai":true,"fault_zone":1}` (fault injection) · `POST /api/optimize` (next control cycle) · [`/api/receipt`](https://urjasetu-ai-eta.vercel.app/api/receipt) (savings receipt)

</div>

---

## What it does

Most buildings bleed energy three ways: they **cool empty rooms** (timer schedules),
they **run hardest exactly when tariffs peak** (18:00–22:00 @ ₹13.4/kWh), and
**equipment faults burn money silently** for months. UrjaSetu closes that loop
autonomously, every 15 minutes:

```
      ┌──────────────  THE 15-MINUTE AUTONOMY LOOP  ──────────────┐
      │                                                            │
      ▼                                                            │
① FORECAST ──► ② OPTIMIZE ──► ③ ACT ──► ④ VERIFY ─────────────────┘
 occupancy      cost-min setpoints   write setpoints   expected vs actual
 weather        + battery dispatch   dispatch BESS     → fault? ₹/day lost
 solar          subject to HARD      shed non-critical   → work order
 TOD tariff     COMFORT CONSTRAINT   loads               → auto-isolate
```

**Verified by the built-in physics test-suite** (`pytest -q`):

| Metric (one operating day, 90k sq ft Mumbai office) | Baseline | UrjaSetu AI | Δ |
|---|---|---|---|
| Energy | 602 kWh | 408 kWh | **−32%** |
| Energy cost | ₹6,159 | ₹3,742 | **−39% (₹7.5L/yr)** |
| Peak demand | 77 kW | 62 kW | **−19%** |
| Comfort (occupied minutes in band) | 82.5% | **99.8%** | **improved** |
| CO₂ | 428 kg | 290 kg | **−138 kg/day** |

> Comfort goes **up**, not down — pre-cooled mornings are more stable than
> 23°C over-cooling. That's the whole trick: the optimizer is only allowed to
> save money *inside* the 23–26.5°C comfort band.


## What's genuinely new (novelty)

1. **Comfort-constrained TOD arbitrage** — savings are earned *inside* the 23–26.5°C band against Indian Time-of-Day tariffs; comfort ends *up* at 99.8%.
2. **Rupee-quantified anomalies** — faults become ₹/day figures with auto-isolation and work orders (`urjasetu/anomaly.py`).
3. **Explainable autonomy** — every zone decision carries a human-readable WHY (tariff / booking / solar), live on the dashboard.
4. **Twin-first methodology** — one physics engine powers the demo, the test suite and the claims: `pytest -q && python3 -m urjasetu.report`.

## Quickstart (60 seconds)

```bash
pip install -r requirements.txt

pytest -q                      # physics verification suite — the feasibility proof
python3 -m urjasetu.report     # CLI savings report, straight from the twin

uvicorn api.app:app --reload   # product API + auto Swagger docs on :8000/docs
```

Live dashboard demo: open `dashboard/index.html` in any browser (zero dependencies).
Press ▶ → **⚡ Jump to 17:30** → **🚨 Inject fault** → **toggle AI OFF**.

## Repository map

```
urjasetu-ai/
├── urjasetu/                 # the product core (pure Python, no heavy deps)
│   ├── tariff.py             # Time-of-Day tariff intelligence
│   ├── weather.py            # ambient temp + rooftop PV + COP models
│   ├── occupancy.py          # zone occupancy profiles & lookahead
│   ├── control.py            # ★ the comfort-constrained optimization brain
│   ├── building.py           # physics digital twin (8 zones, thermal dynamics)
│   ├── twin.py               # day simulator + baseline-vs-AI comparison
│   ├── anomaly.py            # CUSUM fault detection + ₹-quantified work orders
│   └── report.py             # CLI: python3 -m urjasetu.report
├── api/app.py                # FastAPI product API (simulate/report/ingest/optimize/calibrate)
├── dashboard/index.html      # self-contained live demo (same physics, in JS)
├── deploy/                   # Vercel deployment (serverless API + dashboard)
├── firmware/                 # ESP32 zone node — real hardware-in-the-loop (₹750 BOM)
├── scripts/calibrate.py      # fit the twin to YOUR building's real meter data
├── data/sample_meter.csv     # example meter export format
├── tests/test_twin.py        # the feasibility proof, mechanized
└── docs/ARCHITECTURE.md      # system design, integration & scaling
```

## Hardware-in-the-loop (proof it acts on reality)

| Part | Cost |
|---|---|
| ESP32 DevKit v1 | ₹380–450 |
| DHT22 temp/RH sensor | ₹180–250 |
| PIR occupancy sensor | ₹60–80 |
| Relay module (fan/pilot) | ₹50–80 |
| 5V charger + wiring | ₹80 |
| **Per-zone total** | **≈ ₹750** |

Flash `firmware/esp32_zone_node.ino`, and the cloud brain starts steering a
*physical* fan via MQTT — with a 5-minute heartbeat fail-safe that reverts to
local comfort control if the network dies. **Safety:** low-voltage pilot loads
only; mains via licensed electrician + contactor.

## Integration with Schneider Electric ecosystems

The field layer speaks **Modbus/TCP and BACnet/IP** — first-class citizens of
**EcoStruxure™ Building Operation** and **Wiser**. UrjaSetu is designed as the
*intelligence layer on top* of a Schneider deployment — Schneider provides the
muscles (meters, actuators, gateways), UrjaSetu is the brain that makes them
30% cheaper to run. `/api/ingest` is the landing point for meter gateways;
`/api/optimize` returns the write-backs an EcoStruxure integrator executes.

## Honest engineering notes

- The twin is a **calibrated simulation** (Mumbai climate, TOD tariff,
  representative occupancy). It is not yet run on a live building — that's
  exactly what the prototype-phase pilot (our own college block) validates.
- `scripts/calibrate.py` fits the twin to real bill data in one command, so
  every number on the pitch can be re-derived from *your* meter.
- All savings figures are reproducible: `pytest -q && python3 -m urjasetu.report`.

## Team

Built end-to-end by **[Your Name]** — [Branch, College].
*Digital twin, optimizer, anomaly detection, API, firmware, dashboard: one codebase, one builder. [Add teammates + roles if any]*

---

*Licensed under MIT. Built for the Yuva Yodha Energy Tech Hackathon 2026 — but the mission is bigger than the hackathon: every smart meter in India should power a self-optimizing building.*
