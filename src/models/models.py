"""Pydantic request / response models for the Agent 2 API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class StartRequest(BaseModel):
    service_id: str
    user_id: str = "demo_user"
    initial_values: dict[str, Any] | None = None


class ResumeRequest(BaseModel):
    session_id: str
    answer: str



class SessionResponse(BaseModel):
    session_id: str
    status: str                     # "collecting" | "done" | "cancelled"
    payload: dict[str, Any] | None = None
    final_json: dict[str, Any] | None = None
    agent_json: dict[str, Any] | None = None
