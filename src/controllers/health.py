"""
Application health endpoint. Update the health check to verify that the resources
an application needs are available.
"""
from fastapi import APIRouter

health = APIRouter(prefix="/api")


@health.get("/health")
async def read_health():
    """
    Returns a response since the web server is healthy
    """
    return {"message": "service is healthy"}
