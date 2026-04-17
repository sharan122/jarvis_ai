"""
Adds http request logging and correlation-id middleware
"""
import http
import math
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

from config.logger import logger
from config.settings import config
from schemas.json_logs import RequestJsonLogSchema, ResponseJsonLogSchema

EMPTY_VALUE = ""
PASS_ROUTES = [
    "/docs",
    "/openapi.json",
    "/openapi.yaml",
    "/api/health",
]


class LogMiddleware(BaseHTTPMiddleware):
    """
    Manages the correlation-id and measures the request/response time
    """

    async def dispatch(self, request, call_next):
        if request.url.path in PASS_ROUTES:
            logger.info("Request %s", request.url.path)
            return await call_next(request)

        # Request processing has started
        start_time = time.time()
        # Make the correlation id for this request
        correlation_id = ""
        if "X-Correlation-Id" in request.headers:
            correlation_id = request.headers["X-Correlation-Id"]
        else:
            correlation_id = str(uuid.uuid4())
        # Store in the request so id can be used later
        request.state.correlation_id = correlation_id
        # Log the request
        server: tuple = request.get("server", ("localhost", config["PORT"]))
        request_headers: dict = dict(request.headers.items())
        request_json_fields = RequestJsonLogSchema(
            correlation_id=correlation_id,
            request_uri=str(request.url),
            request_method=request.method,
            request_path=request.url.path,
            request_host=f"{server[0]}:{server[1]}",
            request_size=int(request_headers.get("content-length", 0)),
            request_headers=request_headers,
        ).model_dump()

        logger.info(
            "Request",
            extra={
                "request_json_fields": request_json_fields,
                "to_mask": True,
            },
        )

        # Execute the request
        exception_object = None
        response_status_code = None
        try:
            response = await call_next(request)
            response_status_code = response.status_code
        except Exception as ex:
            logger.error("Exception %s", ex)
            response_status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR.real
            exception_object = ex
            response_headers = {}
        else:
            # Share headers back to the client
            response.headers["X-Correlation-Id"] = correlation_id
            response_headers = dict(response.headers.items())

        # Request processing is done
        duration: int = math.ceil((time.time() - start_time) * 1000)

        # Log the response
        response_json_fields = ResponseJsonLogSchema(
            correlation_id=correlation_id,
            response_status_code=response_status_code,
            response_size=int(response_headers.get("content-length", 0)),
            response_headers=response_headers,
            duration=duration,
        ).model_dump()

        message = f'{"Error" if exception_object else "Response"}'

        logger.info(
            message,
            extra={
                "response_json_fields": response_json_fields,
                "to_mask": True,
            },
            exc_info=exception_object,
        )
        return response
