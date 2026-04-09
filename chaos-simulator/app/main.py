import asyncio
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

# Service health: 1 = up, 0 = down
SERVICE_HEALTH = Gauge(
    "chaos_service_health",
    "Service health status (1=up, 0=down)",
    ["service", "environment"],
)

# HTTP error rate (0.0 – 1.0)
HTTP_ERROR_RATE = Gauge(
    "chaos_http_error_rate",
    "Fraction of HTTP requests returning 5xx errors",
    ["service", "environment"],
)

# Response latency in milliseconds
RESPONSE_LATENCY_MS = Gauge(
    "chaos_response_latency_ms",
    "Average HTTP response latency in milliseconds",
    ["service", "environment"],
)

# CPU usage percent (0 – 100)
CPU_USAGE_PERCENT = Gauge(
    "chaos_cpu_usage_percent",
    "Simulated CPU usage percentage",
    ["service", "environment"],
)

# Memory usage percent (0 – 100)
MEMORY_USAGE_PERCENT = Gauge(
    "chaos_memory_usage_percent",
    "Simulated memory usage percentage",
    ["service", "environment"],
)

# Request throughput per second
REQUEST_RATE = Gauge(
    "chaos_request_rate",
    "Simulated requests per second",
    ["service", "environment"],
)

# Total chaos scenarios triggered (for audit)
CHAOS_TRIGGERS_TOTAL = Counter(
    "chaos_triggers_total",
    "Total number of chaos scenarios triggered",
    ["service", "scenario"],
)

# ---------------------------------------------------------------------------
# Simulated services — realistic microservice names
# ---------------------------------------------------------------------------

SERVICES = [
    "payment-service",
    "auth-service",
    "order-service",
    "notification-service",
    "inventory-service",
]

ENV = "production"

# Active chaos scenarios: {service: {scenario, ends_at}}
active_scenarios: dict[str, dict] = {}

# Background jitter task handle
_jitter_task: Optional[asyncio.Task] = None


def _init_baseline():
    """Set all services to healthy baseline on startup."""
    for svc in SERVICES:
        SERVICE_HEALTH.labels(service=svc, environment=ENV).set(1)
        HTTP_ERROR_RATE.labels(service=svc, environment=ENV).set(
            round(random.uniform(0.001, 0.015), 4)
        )
        RESPONSE_LATENCY_MS.labels(service=svc, environment=ENV).set(
            round(random.uniform(80, 250), 1)
        )
        CPU_USAGE_PERCENT.labels(service=svc, environment=ENV).set(
            round(random.uniform(15, 40), 1)
        )
        MEMORY_USAGE_PERCENT.labels(service=svc, environment=ENV).set(
            round(random.uniform(30, 55), 1)
        )
        REQUEST_RATE.labels(service=svc, environment=ENV).set(
            round(random.uniform(50, 300), 1)
        )


async def _jitter_loop():
    """
    Every 10s add small random noise to all healthy services so metrics
    look alive in Grafana — not flat lines.
    """
    while True:
        await asyncio.sleep(10)
        now = datetime.now(timezone.utc).timestamp()

        for svc in SERVICES:
            # Only jitter services not under an active chaos scenario
            scenario = active_scenarios.get(svc)
            if scenario and scenario["ends_at"] > now:
                continue

            # Small natural drift
            current_err = HTTP_ERROR_RATE.labels(
                service=svc, environment=ENV
            )._value.get()
            HTTP_ERROR_RATE.labels(service=svc, environment=ENV).set(
                max(0.001, min(0.03, current_err + random.uniform(-0.003, 0.003)))
            )
            current_lat = RESPONSE_LATENCY_MS.labels(
                service=svc, environment=ENV
            )._value.get()
            RESPONSE_LATENCY_MS.labels(service=svc, environment=ENV).set(
                max(50, min(400, current_lat + random.uniform(-20, 20)))
            )
            current_cpu = CPU_USAGE_PERCENT.labels(
                service=svc, environment=ENV
            )._value.get()
            CPU_USAGE_PERCENT.labels(service=svc, environment=ENV).set(
                max(5, min(70, current_cpu + random.uniform(-5, 5)))
            )
            current_mem = MEMORY_USAGE_PERCENT.labels(
                service=svc, environment=ENV
            )._value.get()
            MEMORY_USAGE_PERCENT.labels(service=svc, environment=ENV).set(
                max(20, min(75, current_mem + random.uniform(-3, 3)))
            )

        # Auto-resolve expired scenarios
        expired = [svc for svc, s in active_scenarios.items() if s["ends_at"] <= now]
        for svc in expired:
            _resolve_service(svc)
            del active_scenarios[svc]
            print(f"[chaos] auto-resolved scenario for {svc}")


def _apply_scenario(service: str, scenario: str):
    """Apply metric changes for a given scenario."""
    if scenario == "service_down":
        SERVICE_HEALTH.labels(service=service, environment=ENV).set(0)
        HTTP_ERROR_RATE.labels(service=service, environment=ENV).set(1.0)
        RESPONSE_LATENCY_MS.labels(service=service, environment=ENV).set(30000)
        REQUEST_RATE.labels(service=service, environment=ENV).set(0)

    elif scenario == "high_error_rate":
        HTTP_ERROR_RATE.labels(service=service, environment=ENV).set(
            round(random.uniform(0.42, 0.65), 3)
        )
        RESPONSE_LATENCY_MS.labels(service=service, environment=ENV).set(
            round(random.uniform(800, 2000), 1)
        )

    elif scenario == "high_latency":
        RESPONSE_LATENCY_MS.labels(service=service, environment=ENV).set(
            round(random.uniform(4000, 8000), 1)
        )
        HTTP_ERROR_RATE.labels(service=service, environment=ENV).set(
            round(random.uniform(0.05, 0.15), 3)
        )

    elif scenario == "cpu_spike":
        CPU_USAGE_PERCENT.labels(service=service, environment=ENV).set(
            round(random.uniform(92, 99), 1)
        )
        RESPONSE_LATENCY_MS.labels(service=service, environment=ENV).set(
            round(random.uniform(1500, 3500), 1)
        )

    elif scenario == "memory_leak":
        MEMORY_USAGE_PERCENT.labels(service=service, environment=ENV).set(
            round(random.uniform(88, 97), 1)
        )
        CPU_USAGE_PERCENT.labels(service=service, environment=ENV).set(
            round(random.uniform(60, 80), 1)
        )

    elif scenario == "traffic_spike":
        REQUEST_RATE.labels(service=service, environment=ENV).set(
            round(random.uniform(2000, 5000), 1)
        )
        CPU_USAGE_PERCENT.labels(service=service, environment=ENV).set(
            round(random.uniform(75, 90), 1)
        )
        RESPONSE_LATENCY_MS.labels(service=service, environment=ENV).set(
            round(random.uniform(600, 1500), 1)
        )

    elif scenario == "degraded":
        # Partial degradation — not enough to page but clearly unhealthy
        HTTP_ERROR_RATE.labels(service=service, environment=ENV).set(
            round(random.uniform(0.08, 0.18), 3)
        )
        RESPONSE_LATENCY_MS.labels(service=service, environment=ENV).set(
            round(random.uniform(1200, 2500), 1)
        )
        CPU_USAGE_PERCENT.labels(service=service, environment=ENV).set(
            round(random.uniform(70, 85), 1)
        )


def _resolve_service(service: str):
    """Restore a service to healthy baseline."""
    SERVICE_HEALTH.labels(service=service, environment=ENV).set(1)
    HTTP_ERROR_RATE.labels(service=service, environment=ENV).set(
        round(random.uniform(0.001, 0.012), 4)
    )
    RESPONSE_LATENCY_MS.labels(service=service, environment=ENV).set(
        round(random.uniform(80, 220), 1)
    )
    CPU_USAGE_PERCENT.labels(service=service, environment=ENV).set(
        round(random.uniform(15, 40), 1)
    )
    MEMORY_USAGE_PERCENT.labels(service=service, environment=ENV).set(
        round(random.uniform(30, 55), 1)
    )
    REQUEST_RATE.labels(service=service, environment=ENV).set(
        round(random.uniform(50, 300), 1)
    )


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _jitter_task
    _init_baseline()
    _jitter_task = asyncio.create_task(_jitter_loop())
    print("[chaos] simulator started — all services healthy")
    yield
    _jitter_task.cancel()
    print("[chaos] simulator stopped")


app = FastAPI(
    title="AlertFlow Chaos Simulator",
    description="Injects realistic failure scenarios into Prometheus metrics for AlertFlow demo and testing.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

VALID_SCENARIOS = [
    "service_down",
    "high_error_rate",
    "high_latency",
    "cpu_spike",
    "memory_leak",
    "traffic_spike",
    "degraded",
]


class TriggerRequest(BaseModel):
    service: str
    scenario: str
    duration_seconds: int = 120

    model_config = {
        "json_schema_extra": {
            "example": {
                "service": "payment-service",
                "scenario": "service_down",
                "duration_seconds": 120,
            }
        }
    }


class ResolveRequest(BaseModel):
    service: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """Prometheus scrape endpoint."""
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/services")
def list_services():
    """List all simulated services and their current state."""
    now = datetime.now(timezone.utc).timestamp()
    result = []
    for svc in SERVICES:
        scenario = active_scenarios.get(svc)
        active = scenario and scenario["ends_at"] > now
        result.append(
            {
                "service": svc,
                "healthy": not active,
                "active_scenario": scenario["scenario"] if active else None,
                "scenario_ends_at": (
                    datetime.fromtimestamp(
                        scenario["ends_at"], tz=timezone.utc
                    ).isoformat()
                    if active
                    else None
                ),
                "metrics": {
                    "health": SERVICE_HEALTH.labels(
                        service=svc, environment=ENV
                    )._value.get(),
                    "error_rate": round(
                        HTTP_ERROR_RATE.labels(
                            service=svc, environment=ENV
                        )._value.get(),
                        4,
                    ),
                    "latency_ms": round(
                        RESPONSE_LATENCY_MS.labels(
                            service=svc, environment=ENV
                        )._value.get(),
                        1,
                    ),
                    "cpu_percent": round(
                        CPU_USAGE_PERCENT.labels(
                            service=svc, environment=ENV
                        )._value.get(),
                        1,
                    ),
                    "memory_percent": round(
                        MEMORY_USAGE_PERCENT.labels(
                            service=svc, environment=ENV
                        )._value.get(),
                        1,
                    ),
                    "request_rate": round(
                        REQUEST_RATE.labels(service=svc, environment=ENV)._value.get(),
                        1,
                    ),
                },
            }
        )
    return {
        "services": result,
        "active_scenarios": len([r for r in result if not r["healthy"]]),
    }


@app.get("/scenarios")
def list_scenarios():
    """List all available chaos scenarios with descriptions."""
    return {
        "scenarios": [
            {
                "name": "service_down",
                "severity": "P1",
                "description": "Service health → 0, error rate → 100%, latency → 30s. Fires ServiceDown alert immediately.",
            },
            {
                "name": "high_error_rate",
                "severity": "P2",
                "description": "HTTP error rate spikes to 42–65%. Fires HighErrorRate alert after 1 minute.",
            },
            {
                "name": "high_latency",
                "severity": "P2",
                "description": "Response latency spikes to 4–8 seconds. Fires HighLatency alert after 2 minutes.",
            },
            {
                "name": "cpu_spike",
                "severity": "P2",
                "description": "CPU climbs to 92–99%. Fires HighCPU alert after 2 minutes.",
            },
            {
                "name": "memory_leak",
                "severity": "P2",
                "description": "Memory climbs to 88–97%. Fires HighMemory alert after 2 minutes.",
            },
            {
                "name": "traffic_spike",
                "severity": "P3",
                "description": "Request rate spikes 10x with elevated CPU and latency.",
            },
            {
                "name": "degraded",
                "severity": "P3",
                "description": "Partial degradation — elevated errors, latency and CPU but not critical thresholds.",
            },
        ]
    }


@app.post("/chaos/trigger", status_code=202)
def trigger_chaos(req: TriggerRequest):
    """
    Inject a chaos scenario into a service.
    Metrics update immediately — Prometheus picks them up on next scrape (15s).
    Alert fires after the 'for' duration in rules.yml.
    """
    if req.service not in SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown service '{req.service}'. Valid: {SERVICES}",
        )
    if req.scenario not in VALID_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{req.scenario}'. Valid: {VALID_SCENARIOS}",
        )
    if req.duration_seconds < 30 or req.duration_seconds > 3600:
        raise HTTPException(
            status_code=400,
            detail="duration_seconds must be between 30 and 3600",
        )

    ends_at = datetime.now(timezone.utc).timestamp() + req.duration_seconds
    active_scenarios[req.service] = {
        "scenario": req.scenario,
        "ends_at": ends_at,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }

    _apply_scenario(req.service, req.scenario)
    CHAOS_TRIGGERS_TOTAL.labels(service=req.service, scenario=req.scenario).inc()

    print(
        f"[chaos] triggered '{req.scenario}' on '{req.service}' for {req.duration_seconds}s"
    )

    return {
        "status": "triggered",
        "service": req.service,
        "scenario": req.scenario,
        "duration_seconds": req.duration_seconds,
        "auto_resolves_at": datetime.fromtimestamp(
            ends_at, tz=timezone.utc
        ).isoformat(),
        "next_steps": [
            "Wait 15s for Prometheus to scrape updated metrics",
            f"Wait for alert 'for' duration (ServiceDown=30s, others=1-2m)",
            "Check Prometheus at http://localhost:9090/alerts",
            "AlertFlow incident created automatically via Alertmanager",
        ],
    }


@app.post("/chaos/trigger-all", status_code=202)
def trigger_all_services(
    scenario: str = "high_error_rate", duration_seconds: int = 120
):
    """
    Trigger the same scenario on ALL services simultaneously.
    Great for demoing Redis deduplication — multiple alerts group into incidents.
    """
    if scenario not in VALID_SCENARIOS:
        raise HTTPException(
            status_code=400, detail=f"Unknown scenario. Valid: {VALID_SCENARIOS}"
        )

    ends_at = datetime.now(timezone.utc).timestamp() + duration_seconds
    triggered = []
    for svc in SERVICES:
        active_scenarios[svc] = {
            "scenario": scenario,
            "ends_at": ends_at,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
        }
        _apply_scenario(svc, scenario)
        CHAOS_TRIGGERS_TOTAL.labels(service=svc, scenario=scenario).inc()
        triggered.append(svc)

    print(
        f"[chaos] triggered '{scenario}' on ALL {len(SERVICES)} services for {duration_seconds}s"
    )
    return {
        "status": "triggered",
        "scenario": scenario,
        "services_affected": triggered,
        "duration_seconds": duration_seconds,
        "note": "Watch Redis deduplication group duplicate alerts into single incidents per service",
    }


@app.post("/chaos/resolve")
def resolve_chaos(req: ResolveRequest):
    """Manually resolve a chaos scenario and restore service to healthy state."""
    if req.service not in SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown service '{req.service}'. Valid: {SERVICES}",
        )

    was_active = req.service in active_scenarios
    active_scenarios.pop(req.service, None)
    _resolve_service(req.service)

    print(f"[chaos] manually resolved '{req.service}'")
    return {
        "status": "resolved",
        "service": req.service,
        "was_active": was_active,
        "note": "Service metrics restored to healthy baseline. Alert will auto-resolve in Prometheus within 1 scrape cycle.",
    }


@app.post("/chaos/resolve-all")
def resolve_all():
    """Resolve all active chaos scenarios and restore all services."""
    resolved = list(active_scenarios.keys())
    active_scenarios.clear()
    for svc in SERVICES:
        _resolve_service(svc)
    print(f"[chaos] resolved all scenarios — {len(resolved)} services restored")
    return {"status": "all_resolved", "services_restored": resolved}


@app.get("/")
def root():
    return {
        "service": "AlertFlow Chaos Simulator",
        "version": "1.0.0",
        "docs": "http://localhost:8001/docs",
        "metrics": "http://localhost:8001/metrics",
        "endpoints": {
            "GET  /services": "Current state of all simulated services",
            "GET  /scenarios": "Available chaos scenarios",
            "POST /chaos/trigger": "Inject a scenario into a service",
            "POST /chaos/trigger-all": "Inject a scenario into all services",
            "POST /chaos/resolve": "Manually resolve a service",
            "POST /chaos/resolve-all": "Resolve everything",
            "GET  /metrics": "Prometheus scrape endpoint",
        },
    }
