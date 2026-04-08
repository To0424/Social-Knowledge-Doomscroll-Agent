"""Pydantic request/response models for the API."""

from pydantic import BaseModel


class TargetCreate(BaseModel):
    username: str
    display_name: str | None = None


class ScheduleUpdate(BaseModel):
    interval_seconds: int | None = None
    is_active: bool | None = None


class CredentialsUpdate(BaseModel):
    auth_token: str
    ct0: str
