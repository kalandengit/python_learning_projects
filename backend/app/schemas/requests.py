from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from ..models import RequestState, RequestType


class RequestCreate(BaseModel):
    type: RequestType
    title: str = ""
    body: str = ""
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class RequestUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class TransitionRequest(BaseModel):
    target: RequestState
    note: str | None = None


class HistoryOut(BaseModel):
    from_state: RequestState | None
    to_state: RequestState
    actor_id: str
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestOut(BaseModel):
    id: str
    type: RequestType
    state: RequestState
    title: str
    body: str
    starts_at: datetime | None
    ends_at: datetime | None
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RequestDetail(RequestOut):
    history: list[HistoryOut] = []
