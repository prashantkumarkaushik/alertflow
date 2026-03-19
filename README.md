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
