"""
Example endpoint
"""
from fastapi import APIRouter
from starlette.requests import Request

from config.logger import logger

example = APIRouter(prefix="/api/v1")


@example.get("/example")
async def read_example(request: Request):
    """
    Example of logging with a correlation_id
    """
    logger.info(
        "This is info logged from the controller",
        extra={
            "correlation_id": request.state.correlation_id,
        },
    )
    return {"message": "hello"}
