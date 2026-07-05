"""HTTP API routers grouped by resource.

Kept in one module for the MVP; split into a ``routers/`` package as the surface grows.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .dedup import DedupBackend
from .deps import get_dedup, get_notifier
from .notifications import NotificationService
from .pipeline import process_detection
from .rule_engine import RuleEngine, build_context, validate_rule
from .schemas import (
    AlertOut,
    AlertStatusUpdate,
    CameraCreate,
    CameraOut,
    DashboardStats,
    DetectionEventIn,
    IngestResult,
    RuleIn,
    RuleOut,
    SiteCreate,
    SiteOut,
    Token,
    UserCreate,
    UserOut,
    ZoneCreate,
    ZoneOut,
)
from .security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
)

# --------------------------------------------------------------------------- auth
auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@auth_router.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    token = create_access_token(subject=user.id, role=user.role, tenant_id=user.tenant_id)
    return Token(access_token=token)


@auth_router.get("/me", response_model=UserOut)
def me(user: models.User = Depends(get_current_user)) -> models.User:
    return user


@auth_router.post("/users", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> models.User:
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")
    user = models.User(
        tenant_id=admin.tenant_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    return user


# --------------------------------------------------------------------------- sites
sites_router = APIRouter(prefix="/api/v1/sites", tags=["sites"])


@sites_router.post("", response_model=SiteOut, status_code=201)
def create_site(
    payload: SiteCreate,
    user: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> models.Site:
    site = models.Site(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(site)
    db.commit()
    return site


@sites_router.get("", response_model=list[SiteOut])
def list_sites(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Site).filter(models.Site.tenant_id == user.tenant_id).all()


# --------------------------------------------------------------------------- zones
zones_router = APIRouter(prefix="/api/v1/zones", tags=["zones"])


@zones_router.post("", response_model=ZoneOut, status_code=201)
def create_zone(
    payload: ZoneCreate,
    user: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> models.Zone:
    zone = models.Zone(**payload.model_dump())
    db.add(zone)
    db.commit()
    return zone


# --------------------------------------------------------------------------- cameras
cameras_router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])


@cameras_router.post("", response_model=CameraOut, status_code=201)
def create_camera(
    payload: CameraCreate,
    user: models.User = Depends(require_role("technician")),
    db: Session = Depends(get_db),
) -> models.Camera:
    data = payload.model_dump(exclude={"zone_ids"})
    camera = models.Camera(tenant_id=user.tenant_id, **data)
    if payload.zone_ids:
        camera.zones = db.query(models.Zone).filter(models.Zone.id.in_(payload.zone_ids)).all()
    db.add(camera)
    db.commit()
    return camera


@cameras_router.get("", response_model=list[CameraOut])
def list_cameras(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Camera).filter(models.Camera.tenant_id == user.tenant_id).all()


# --------------------------------------------------------------------------- events (ingest)
events_router = APIRouter(prefix="/api/v1/events", tags=["events"])


@events_router.post("", response_model=IngestResult, status_code=202)
def ingest_event(
    payload: DetectionEventIn,
    db: Session = Depends(get_db),
    dedup: DedupBackend = Depends(get_dedup),
    notifier: NotificationService = Depends(get_notifier),
) -> IngestResult:
    """Receive a detection from a camera/gateway and run the pipeline.

    Authenticated in production via a per-camera/gateway credential (mTLS or an ingest key).
    """
    try:
        return process_detection(db, payload, dedup=dedup, notifier=notifier)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# --------------------------------------------------------------------------- rules
rules_router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


@rules_router.post("", response_model=RuleOut, status_code=201)
def create_rule(
    payload: RuleIn,
    user: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> models.Rule:
    try:
        validate_rule(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    rule = models.Rule(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(rule)
    db.commit()
    return rule


@rules_router.get("", response_model=list[RuleOut])
def list_rules(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Rule).filter(models.Rule.tenant_id == user.tenant_id).order_by(models.Rule.priority).all()


@rules_router.post("/dry-run")
def dry_run_rules(
    contexts: list[dict],
    user: models.User = Depends(require_role("operator")),
    db: Session = Depends(get_db),
):
    """Evaluate candidate contexts against the tenant's active rules without side effects."""
    rows = db.query(models.Rule).filter(models.Rule.tenant_id == user.tenant_id).all()
    engine = RuleEngine(
        rules=[
            {"name": r.name, "priority": r.priority, "conditions": r.conditions, "action": r.action, "enabled": r.enabled}
            for r in rows
        ]
    )
    return [vars(o) for o in engine.dry_run(contexts)]


# --------------------------------------------------------------------------- alerts
alerts_router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@alerts_router.get("", response_model=list[AlertOut])
def list_alerts(
    status_filter: str | None = None,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(models.Alert).filter(models.Alert.tenant_id == user.tenant_id)
    if status_filter:
        q = q.filter(models.Alert.status == status_filter)
    return q.order_by(models.Alert.created_at.desc()).all()


@alerts_router.patch("/{alert_id}", response_model=AlertOut)
def update_alert_status(
    alert_id: str,
    update: AlertStatusUpdate,
    user: models.User = Depends(require_role("operator")),
    db: Session = Depends(get_db),
) -> models.Alert:
    alert = db.get(models.Alert, alert_id)
    if alert is None or alert.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "alert not found")
    old = alert.status
    alert.status = update.status
    db.add(
        models.AlertHistory(
            alert_id=alert.id,
            from_status=old,
            to_status=update.status,
            actor=user.email,
            reason=update.reason,
        )
    )
    db.commit()
    return alert


# --------------------------------------------------------------------------- dashboard
dashboard_router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@dashboard_router.get("/stats", response_model=DashboardStats)
def dashboard_stats(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)) -> DashboardStats:
    tid = user.tenant_id
    cams = db.query(models.Camera).filter(models.Camera.tenant_id == tid)
    total = cams.count()
    online = cams.filter(models.Camera.status == "online").count()
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    intrusions_today = (
        db.query(func.count(models.Alert.id))
        .filter(models.Alert.tenant_id == tid, models.Alert.created_at >= start_of_day)
        .scalar()
    )
    critical = (
        db.query(func.count(models.Alert.id))
        .filter(models.Alert.tenant_id == tid, models.Alert.criticality == "critical")
        .scalar()
    )
    open_alerts = (
        db.query(func.count(models.Alert.id))
        .filter(models.Alert.tenant_id == tid, models.Alert.status.in_(["NEW", "IN_PROGRESS"]))
        .scalar()
    )
    return DashboardStats(
        cameras_total=total,
        cameras_online=online,
        cameras_offline=total - online,
        intrusions_today=intrusions_today or 0,
        critical_alerts=critical or 0,
        open_alerts=open_alerts or 0,
    )


ALL_ROUTERS = [
    auth_router,
    sites_router,
    zones_router,
    cameras_router,
    events_router,
    rules_router,
    alerts_router,
    dashboard_router,
]
