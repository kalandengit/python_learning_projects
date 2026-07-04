"""Events: create, cursor-paginated listing, detail, tiers, publish.

Published events are public reads; drafts are visible only to their own
organization (IDOR check against JWT `org` claim).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2.functions import ST_X, ST_Y
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_optional_auth, require_organizer
from app.core.pagination import CursorError, decode_cursor, encode_cursor
from app.core.security import AuthContext
from app.db import get_session
from app.models import Event, TicketTier
from app.schemas.events import EventCreate, EventOut, EventPage, TierCreate, TierOut

router = APIRouter(prefix="/events", tags=["events"])

_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")


async def _event_out(session: AsyncSession, event: Event) -> EventOut:
    out = EventOut.model_validate(event)
    if event.location is not None:
        row = (
            await session.execute(
                select(ST_X(Event.location), ST_Y(Event.location)).where(Event.id == event.id)
            )
        ).one()
        out.longitude, out.latitude = float(row[0]), float(row[1])
    return out


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventCreate,
    auth: Annotated[AuthContext, Depends(require_organizer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventOut:
    event = Event(
        organization_id=auth.org_id,
        created_by=auth.user_id,
        title=body.title,
        description=body.description,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        venue_name=body.venue_name,
        location=(
            f"SRID=4326;POINT({body.longitude} {body.latitude})"
            if body.latitude is not None
            else None
        ),
        geofence_radius_m=body.geofence_radius_m,
    )
    session.add(event)
    await session.commit()
    return await _event_out(session, event)


@router.get("", response_model=EventPage)
async def list_events(
    session: Annotated[AsyncSession, Depends(get_session)],
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> EventPage:
    query = (
        select(Event)
        .where(Event.is_published.is_(True))
        .order_by(Event.created_at.desc(), Event.id.desc())
        .limit(limit + 1)
    )
    if cursor is not None:
        try:
            created_at, last_id = decode_cursor(cursor)
        except CursorError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid cursor"
            ) from exc
        query = query.where(tuple_(Event.created_at, Event.id) < (created_at, last_id))

    events = list((await session.scalars(query)).all())
    has_more = len(events) > limit
    events = events[:limit]
    next_cursor = (
        encode_cursor(events[-1].created_at, events[-1].id) if has_more and events else None
    )
    return EventPage(
        items=[await _event_out(session, e) for e in events], next_cursor=next_cursor
    )


@router.get("/{event_id}", response_model=EventOut)
async def get_event(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    auth: Annotated[AuthContext | None, Depends(get_optional_auth)],
) -> EventOut:
    event = await session.get(Event, event_id)
    if event is None:
        raise _NOT_FOUND
    if not event.is_published and (auth is None or auth.org_id != event.organization_id):
        raise _NOT_FOUND  # drafts are not enumerable
    return await _event_out(session, event)


@router.post("/{event_id}/tiers", response_model=TierOut, status_code=status.HTTP_201_CREATED)
async def create_tier(
    event_id: uuid.UUID,
    body: TierCreate,
    auth: Annotated[AuthContext, Depends(require_organizer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TierOut:
    event = await session.get(Event, event_id)
    if event is None or event.organization_id != auth.org_id:
        raise _NOT_FOUND
    tier = TicketTier(
        event_id=event.id,
        name=body.name,
        price_cents=body.price_cents,
        currency=body.currency,
        capacity=body.capacity,
        sales_starts_at=body.sales_starts_at,
        sales_ends_at=body.sales_ends_at,
    )
    session.add(tier)
    await session.commit()
    return TierOut.model_validate(tier)


@router.post("/{event_id}/publish", response_model=EventOut)
async def publish_event(
    event_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_organizer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventOut:
    event = await session.get(Event, event_id)
    if event is None or event.organization_id != auth.org_id:
        raise _NOT_FOUND
    if not event.is_published:
        event.is_published = True
        event.version += 1
        await session.commit()
    return await _event_out(session, event)
