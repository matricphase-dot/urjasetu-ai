# UrjaSetu AI — System Architecture

## 1. Layered design

```
┌───────────────────────────── CLOUD BRAIN ─────────────────────────────┐
│  Forecasting (occupancy · weather · solar · TOD tariff)                │
│  Comfort-constrained optimizer (urjasetu/control.py)                   │
│  Anomaly detection & ₹-quantified work orders (urjasetu/anomaly.py)    │
│  FastAPI product surface (api/app.py)                                  │
└──────────────▲─────────────────────────────────────┬──────────────────┘
               │ TLS/MQTT or HTTPS                    │ control writes
┌──────────────┴───────────── EDGE AGENT ─────────────▼──────────────────┐
│  Local buffering · offline-safe fallback schedule · Modbus/TCP master   │
│  BACnet/IP client · OTA device management                               │
└──────────────▲─────────────────────────────────────┬──────────────────┘
               │ telemetry (15 s)                     │ setpoints (15 min)
┌──────────────┴───────────── FIELD LAYER ────────────▼──────────────────┐
│  Smart energy meter (already installed, mandated)                       │
│  ESP32 zone nodes: DHT22 + PIR + relay  ≈ ₹750/zone (firmware/)         │
│  Existing AHU/chiller controllers · battery inverter (if present)       │
└─────────────────────────────────────────────────────────────────────────┘
```

**Design principle: software-first, hardware-lite.** The building's existing
assets (meter, HVAC controllers) become sensors/actuators. New hardware is one
cheap node per zone — never a rip-and-replace BMS.

## 2. The 15-minute control cycle

| Step | Module | Input → Output |
|---|---|---|
| 1 · Forecast | `occupancy.weather.tariff` | horizon curves: occupancy frac, T_amb, PV kW, ₹/kWh |
| 2 · Optimize | `control.zone_policy + battery_dispatch` | curves → per-zone setpoint + mode + BESS dispatch, subject to **comfort ∈ [23, 26.5]°C** |
| 3 · Act | edge agent write-side | setpoints → AHUs (Modbus FC16), dispatch → inverter |
| 4 · Verify | `anomaly.cusum_detect` | expected vs actual kW → residuals → fault alert + work order |

The optimizer is deliberately *rule-informed optimization* (interpretable,
auditable, testable) rather than a black-box RL policy — a deliberate
engineering choice for buildings, where a wrong decision has human comfort
consequences and facility managers must trust the system.

## 3. Why the twin exists (and why it's the moat)

`building.py` is a physics simulator of the building: envelope gains,
occupant/equipment loads, COP degradation with ambient temperature, thermal
time-constants. It means:

- **Safe rehearsal** — every policy change is simulated for thousands of
  operating days before touching hardware (no trial-and-error on occupants).
- **Calibration** — `scripts/calibrate.py` fits the twin's SCALE parameter to
  a real meter export; after that, twin KPIs track the real building.
- **Shadow-mode verification** — in production the twin runs one cycle ahead;
  expected-vs-actual residuals are the fault detector *and* the savings meter
  (you can't claim savings you can't simulate).

## 4. API contract (v1)

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | liveness |
| `/api/config` | GET | tariff table, zones, comfort band, loop period |
| `/api/simulate` | POST | full-day twin run → curves + KPIs (`ai`, `fault_zone` flags) |
| `/api/report` | GET | baseline-vs-AI headline + annualized savings |
| `/api/ingest` | POST | meter readings `[{ts, kw}]` from gateways (Modbus/meter push) |
| `/api/optimize` | POST | next-cycle control decisions (what the edge writes) |
| `/api/calibrate` | POST | fit twin to `avg_daily_kwh` from real bills |

Swagger docs auto-generate at `/docs`.

## 5. Security & safety

- TLS on every hop (MQTT 8883 / HTTPS); per-node certificates in production.
- Nodes run **least privilege**: a zone node can only affect its own relay.
- **5-minute heartbeat fail-safe** in firmware: brain unreachable → node
  reverts to a local comfort schedule. The building never depends on the cloud.
- Mains-voltage actuation only through contactors installed by licensed
  electricians; dev hardware switches pilot loads only.
- Comfort is a *hard constraint* in code, not a preference — the optimizer
  cannot trade occupant wellbeing for savings even if asked.

## 6. Scaling path

1. **Now:** single-building twin + optimizer (this repo).
2. **Pilot:** one college block, live meter → `/api/ingest`, shadow mode, measured savings report.
3. **Multi-building:** tariff + weather as services; twin per building; fleet dashboard; DR-ready (discom demand-response events as an extra price signal).
4. **Grid layer:** aggregated batteries as a virtual power plant — buildings become a grid asset, not just a load.

## 7. What we'd build with Schneider mentorship

- BACnet write-side certification against EcoStruxure Building Operation.
- Chiller-plant physics: real Cop curves, staged sequencing, VFD modeling.
- Pilot building access + ESCO channel intros for share-the-savings deals.
