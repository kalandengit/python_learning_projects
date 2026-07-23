"""Shared runtime singletons exposed as FastAPI dependencies."""
from __future__ import annotations

from fastapi import Request

from .dedup import DedupBackend
from .notifications import NotificationService


def get_dedup(request: Request) -> DedupBackend:
    return request.app.state.dedup


def get_notifier(request: Request) -> NotificationService:
    return request.app.state.notifier
