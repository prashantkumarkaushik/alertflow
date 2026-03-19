from fastapi import APIRouter

from app.api.v1 import (
    alerts,
    auth,
    escalation_policies,
    incidents,
    maintenance,
    sla_policies,
    webhooks,
)

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(alerts.router)
router.include_router(incidents.router)
router.include_router(sla_policies.router)
router.include_router(maintenance.router)
router.include_router(escalation_policies.router)
router.include_router(webhooks.router)
