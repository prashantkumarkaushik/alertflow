# AlertFlow Chaos Simulator

A lightweight FastAPI service that simulates realistic infrastructure failures
by exposing Prometheus-format metrics that can be dynamically controlled via API.

Designed to drive real P1/P2 alerts through the full AlertFlow pipeline:
**Chaos Simulator → Prometheus → Alertmanager → AlertFlow → Slack**

---

## Quick Start

```bash
# From the alertflow root directory
docker compose up -d --build

# Verify simulator is running
curl http://localhost:8001/health

# View all services and their current metrics
curl http://localhost:8001/services | python3 -m json.tool

# Open Swagger UI
open http://localhost:8001/docs
```

---

## Demo Scenarios

### 1. P1 — Service Down (fires in ~30 seconds)

```bash
curl -X POST http://localhost:8001/chaos/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "service": "payment-service",
    "scenario": "service_down",
    "duration_seconds": 120
  }'
```

**What happens:**
1. Metrics update immediately
2. Prometheus scrapes in ~15s
3. `ServiceDown` alert fires after 30s (`for: 30s` in rules.yml)
4. Alertmanager routes to AlertFlow `/api/v1/alerts/ingest`
5. AlertFlow creates a P1 incident with SLA deadline
6. Slack card posted to team channel
7. Service auto-restores after 120s

---

### 2. P2 — High Error Rate Storm (fires in ~1 minute)

```bash
curl -X POST http://localhost:8001/chaos/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "service": "auth-service",
    "scenario": "high_error_rate",
    "duration_seconds": 180
  }'
```

---

### 3. Demo Redis Deduplication — Hit ALL Services

```bash
# Trigger same scenario on all 5 services simultaneously
# Watch AlertFlow group duplicate alerts — one incident per service
curl -X POST "http://localhost:8001/chaos/trigger-all?scenario=high_error_rate&duration_seconds=120"
```

**Interview talking point:** "AlertFlow receives 15+ alerts in 30 seconds but Redis SHA-256
deduplication groups them — one incident per service, not 15 separate noise tickets."

---

### 4. SLA Breach Demo

```bash
# 1. Trigger an alert
curl -X POST http://localhost:8001/chaos/trigger \
  -d '{"service": "order-service", "scenario": "service_down", "duration_seconds": 600}'

# 2. Do NOT acknowledge the incident in AlertFlow UI
# 3. Wait for APScheduler to detect SLA breach (depends on your P1 SLA policy)
# 4. Watch escalation fire and audit log update
# 5. Call AI summary endpoint to see the full breach timeline
```

---

### 5. Resolve Manually

```bash
# Resolve a specific service
curl -X POST http://localhost:8001/chaos/resolve \
  -H "Content-Type: application/json" \
  -d '{"service": "payment-service"}'

# Resolve everything
curl -X POST http://localhost:8001/chaos/resolve-all
```

---

## Available Scenarios

| Scenario | Severity | Alert fires after | What changes |
|---|---|---|---|
| `service_down` | P1 | 30s | Health=0, error=100%, latency=30s |
| `high_error_rate` | P2 | 1m | Error rate 42–65% |
| `high_latency` | P2 | 2m | Latency 4–8 seconds |
| `cpu_spike` | P2 | 2m | CPU 92–99% |
| `memory_leak` | P1 | 2m | Memory 88–97% |
| `traffic_spike` | P3 | 2m | 10x normal request rate |
| `degraded` | P3 | 3m | Partial degradation across all metrics |

---

## Simulated Services

- `payment-service`
- `auth-service`
- `order-service`
- `notification-service`
- `inventory-service`

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Service info and endpoint list |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus scrape endpoint |
| GET | `/services` | Current state of all services |
| GET | `/scenarios` | Available scenarios with descriptions |
| POST | `/chaos/trigger` | Inject scenario into one service |
| POST | `/chaos/trigger-all` | Inject scenario into all services |
| POST | `/chaos/resolve` | Resolve one service |
| POST | `/chaos/resolve-all` | Resolve all active scenarios |

---

## Architecture

```
POST /chaos/trigger
        │
        ▼
Metrics updated in-process (prometheus_client gauges)
        │
        ▼  (every 15s)
Prometheus scrapes /metrics
        │
        ▼  (after `for:` duration)
Alert rule fires → Alertmanager
        │
        ▼
POST /api/v1/alerts/ingest → AlertFlow
        │
        ├── Redis dedup check (SHA-256 fingerprint)
        ├── Find/create incident
        ├── Set SLA deadline
        └── Write audit log → Slack notification
```
