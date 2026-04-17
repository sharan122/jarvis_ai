"""
FastAPI application entry point.

Run with:
    uvicorn api.main:app --reload --port 8000
"""
"""
The main application
"""
import functools
import io
from agent.tracing import initialize_langfuse
import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_fastapi_instrumentator import PrometheusFastApiInstrumentator
from config.middleware import LogMiddleware
from config.settings import config
from controllers.example import example
from controllers.health import health

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


from controllers.routes import router
initialize_langfuse()
app = FastAPI()

app.add_middleware(LogMiddleware)
PrometheusFastApiInstrumentator().instrument(app).expose(app, endpoint="/observability/metrics")


@app.get("/openapi.yaml", include_in_schema=False)
@functools.lru_cache()
def read_openapi_yaml() -> Response:
    """Generates an OpenAPI YAML document using the JSON document"""
    openapi_json = app.openapi()
    yaml_s = io.StringIO()
    yaml.dump(openapi_json, yaml_s)
    return Response(yaml_s.getvalue(), media_type="text/yaml")


# health endpoint for containers
app.include_router(health)
# app endpoints
app.include_router(example)
app.include_router(router)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", log_config=None, port=int(config["PORT"]))
