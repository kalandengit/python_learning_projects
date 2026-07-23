"""Seed a demo tenant, admin user, site/zone/camera, and the default rule set."""
from __future__ import annotations

from sqlalchemy.orm import Session

from . import models
from .database import SessionLocal, init_db
from .rule_engine import DEFAULT_RULES
from .security import hash_password

DEMO_ADMIN_EMAIL = "admin@demo.pids"
DEMO_ADMIN_PASSWORD = "changeme123"


def seed(db: Session) -> dict:
    if db.query(models.Tenant).first():
        return {"status": "already-seeded"}

    tenant = models.Tenant(name="Demo Tenant")
    db.add(tenant)
    db.flush()

    admin = models.User(
        tenant_id=tenant.id,
        email=DEMO_ADMIN_EMAIL,
        password_hash=hash_password(DEMO_ADMIN_PASSWORD),
        role="super_admin",
    )
    db.add(admin)

    site = models.Site(tenant_id=tenant.id, name="HQ Perimeter", lat=48.8566, lon=2.3522)
    db.add(site)
    db.flush()

    parking = models.Zone(site_id=site.id, name="Parking")
    north = models.Zone(site_id=site.id, name="Clôture Nord")
    db.add_all([parking, north])
    db.flush()

    cam = models.Camera(
        tenant_id=tenant.id,
        site_id=site.id,
        name="CAM-Parking-01",
        protocol="ONVIF",
        model="AI-Cam T-series",
        status="online",
    )
    cam.zones = [parking]
    db.add(cam)

    for r in DEFAULT_RULES:
        db.add(models.Rule(tenant_id=tenant.id, **r))

    db.commit()
    return {
        "status": "seeded",
        "tenant_id": tenant.id,
        "admin_email": DEMO_ADMIN_EMAIL,
        "camera_id": cam.id,
    }


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        print(seed(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
