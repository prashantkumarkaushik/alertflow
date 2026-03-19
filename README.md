# AlertFlow

A production-inspired incident management and alert routing platform — a lite version of PagerDuty + ServiceNow. Built to demonstrate real-world backend engineering patterns: async APIs, Redis deduplication, SLA tracking, background workers, multi-tenancy, and audit logging.

---

## Features

- **Alert Ingestion** — webhook endpoint for monitoring systems (Prometheus, Grafana, Datadog)
- **Redis Deduplication** — SHA-256 fingerprinting with 10-minute TTL suppression window
- **Incident Lifecycle** — enforced state machine (triggered → acknowledged → resolved)
- **SLA Tracking** — configurable policies per priority (P1–P4) with automatic breach detection
- **Escalation Engine** — step-based auto-escalation with configurable delays and targets
- **Maintenance Windows** — suppress alerts during planned downtime
- **Audit Log** — append-only timeline of every incident event
- **Multi-tenancy** — all data scoped to teams via JWT claims

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (async) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Cache / Dedup | Redis 7 |
| Auth | JWT (python-jose) + bcrypt |
| Background Jobs | APScheduler (in-process) |
| Package Manager | uv |
| Containerisation | Docker + Docker Compose |
| Testing | pytest-asyncio + HTTPX |

---

## Quick Start

**Prerequisites:** Docker Desktop, Git
```bash
git clone https://github.com/yourusername/alertflow.git
cd alertflow
cp .env.example .env
docker compose up -d --build
```

| Service | URL | Description |
|---|---|---|
| Frontend | http://localhost:3000 | React dashboard |
| Backend API | http://localhost:8000 | FastAPI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Prometheus | http://localhost:9090 | Metrics + alert rules |
| Alertmanager | http://localhost:9093 | Alert routing |
| Adminer | http://localhost:8080 | Database UI |

## First Time Setup

After starting the stack:

1. Open http://localhost:3000/register
2. Create your account and team
3. Go to http://localhost:8000/docs → Authorize → create an SLA policy
4. Alerts from Prometheus will automatically create incidents

## Development

Run frontend in dev mode with hot reload:
```bash
cd frontend
npm install
npm run dev
```

Run backend with hot reload (already configured in Docker):
```bash
docker compose up backend -d
docker compose logs backend -f
```

Run tests:
```bash
cd backend
uv run pytest -v
```
---

## Project Structure
```
alertflow/
├── backend/
│   └── app/
│       ├── core/          # config, database, auth, dependencies
│       ├── models/        # SQLAlchemy ORM models
│       ├── schemas/       # Pydantic request/response schemas
│       ├── api/v1/        # FastAPI routers
│       ├── services/      # business logic layer
│       └── workers/       # APScheduler background jobs
├── compose.yml
├── compose.override.yml
└── .env.example
```

---

## Architecture
```
Monitoring Systems (Prometheus / Grafana / Datadog)
              │
              │  POST /api/v1/alerts/ingest
              ▼
        ┌─────────────────────────────────┐
        │         FastAPI Backend         │
        │                                 │
        │  1. Compute SHA-256 fingerprint │
        │  2. Redis dedup check (SET NX)  │
        │  3. Maintenance window check    │
        │  4. Save Alert                  │
        │  5. Find/create Incident        │
        │  6. Calculate SLA deadline      │
        │  7. Write Audit Log             │
        └──────────┬──────────────────────┘
                   │
         ┌─────────┴──────────┐
         ▼                    ▼
   PostgreSQL 16           Redis 7
   (persistent data)    (dedup cache)

Background Workers (APScheduler — every 60s):
  • SLA Checker    → marks breached incidents
  • Escalation     → fires notifications by policy
```

---

## API Reference

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Create user + team |
| POST | `/api/v1/auth/login` | Login, returns JWT |
| GET  | `/api/v1/auth/me` | Current user |

### Alerts
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/alerts/ingest` | Ingest alert from monitoring system |

### Incidents
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/incidents` | List incidents (filter: status, priority, sla_breached) |
| GET | `/api/v1/incidents/{id}` | Incident detail with alerts + audit log |
| PATCH | `/api/v1/incidents/{id}/status` | Transition status |
| GET | `/api/v1/incidents/{id}/audit` | Full audit timeline |

### SLA Policies
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/sla-policies` | Create SLA policy |
| GET | `/api/v1/sla-policies` | List policies |
| PUT | `/api/v1/sla-policies/{id}` | Update policy |
| DELETE | `/api/v1/sla-policies/{id}` | Delete policy |

### Escalation Policies
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/escalation-policies` | Create policy with steps |
| GET | `/api/v1/escalation-policies` | List policies |
| POST | `/api/v1/escalation-policies/{id}/steps` | Add step |

### Maintenance Windows
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/maintenance` | Create window |
| GET | `/api/v1/maintenance` | List windows |
| PATCH | `/api/v1/maintenance/{id}/cancel` | Cancel early |

---

## Alert Ingestion Flow
```
POST /api/v1/alerts/ingest
         │
         ▼
Compute fingerprint (SHA-256 of source+name+labels)
         │
         ▼
Redis SET NX with 10min TTL
  duplicate? → return 200 deduplicated
         │
         ▼
Active maintenance window for service?
  yes → save suppressed alert, return 201
         │
         ▼
Save Alert (status=open)
         │
         ▼
Find open incident for team or create new one
         │
         ▼
Calculate SLA deadline from policy
         │
         ▼
Write audit log → return 201
```

---

## Incident State Machine
```
TRIGGERED ──► ACKNOWLEDGED ──► RESOLVED
                                   │
                              re-open ▼
                             TRIGGERED
```

Invalid transitions return `HTTP 422` with allowed transitions listed.

---

## Environment Variables

Create `.env` from `.env.example`:
```env
PROJECT_NAME=AlertFlow
ENVIRONMENT=local
SECRET_KEY=your-secret-key-min-32-chars

POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_USER=alertflow
POSTGRES_PASSWORD=alertflow
POSTGRES_DB=alertflow

REDIS_URL=redis://redis:6379/0

FIRST_SUPERUSER_EMAIL=admin@alertflow.com
FIRST_SUPERUSER_PASSWORD=alertflow123
```

---

## Running Tests
```bash
cd backend
uv run pytest -v
```

---

## What I'd add in production

- **Celery + Redis** as task broker for workers (scale independently)
- **Webhook delivery** for escalation notifications (Slack, PagerDuty)
- **Rate limiting** on alert ingest endpoint
- **Prometheus metrics** endpoint for self-monitoring
- **Kubernetes manifests** for deployment

---

## License

MIT
