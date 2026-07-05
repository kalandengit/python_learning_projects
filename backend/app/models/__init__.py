"""SQLAlchemy models. Importing this package registers every table on ``Base``."""

from .attachment import Attachment, ScanStatus
from .audit import AuditLog
from .base import Base
from .ics import IcsToken
from .notification import Notification
from .request import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    Request,
    RequestState,
    RequestStatusHistory,
    RequestType,
)
from .shift import Shift
from .tenant import FeatureFlag, Tenant
from .user import AuthToken, AuthTokenKind, User, UserRole, UserStatus

__all__ = [
    "Base",
    "Tenant",
    "FeatureFlag",
    "User",
    "UserRole",
    "UserStatus",
    "AuthToken",
    "AuthTokenKind",
    "Shift",
    "Request",
    "RequestType",
    "RequestState",
    "RequestStatusHistory",
    "ALLOWED_TRANSITIONS",
    "TERMINAL_STATES",
    "Notification",
    "AuditLog",
    "IcsToken",
    "Attachment",
    "ScanStatus",
]
