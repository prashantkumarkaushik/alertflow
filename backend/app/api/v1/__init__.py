from fastapi import APIRouter

from app.api.v1 import alerts, auth, incidents, maintenance, sla_policies

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(alerts.router)
router.include_router(incidents.router)
router.include_router(sla_policies.router)
router.include_router(maintenance.router)
