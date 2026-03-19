from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Basic Prometheus metrics endpoint.
    In production use prometheus-fastapi-instrumentator for full metrics.
    """
    return """# HELP alertflow_up AlertFlow backend status
# TYPE alertflow_up gauge
alertflow_up 1
# HELP alertflow_info AlertFlow build info
# TYPE alertflow_info gauge
alertflow_info{version="1.0.0"} 1
"""
