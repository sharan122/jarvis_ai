"""
The preferred output for logging is JSON.
The Base, HTTP Request, and HTTP Response can be customized.
"""
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class BaseJsonLogSchema(BaseModel):
    """
    Main log in JSON format
    """

    model_config = ConfigDict(populate_by_name=True)

    thread: int | str
    level_name: str
    message: str
    source_log: str
    timestamp: str = Field(..., alias="@timestamp")
    app_name: str
    exceptions: Optional[List[str] | str] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_id: Optional[str] = None


class RequestJsonLogSchema(BaseModel):
    """
    Schema for request
    """

    correlation_id: str
    request_uri: str
    request_method: str
    request_path: str
    request_host: str
    request_size: int
    request_headers: dict


class ResponseJsonLogSchema(BaseModel):
    """
    Schema for response
    """

    correlation_id: str
    response_status_code: int
    response_size: Optional[int]
    response_headers: dict
    duration: int
