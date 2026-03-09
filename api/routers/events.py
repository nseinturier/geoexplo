import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Any
from sqlalchemy.orm import Session

from relational.database import get_db
from relational.models import Event, EventType

router = APIRouter()


class EventCreate(BaseModel):
    timestamp: Optional[datetime] = None
    scenario_id: str = "production"
    event_type: EventType
    actor_uid: str
    target_uid: str
    description: str = ""
    confirmed: bool = False
    confidence: float = 1.0
    casualties: Optional[int] = None
    properties: dict = {}


class EventPatch(BaseModel):
    confirmed: Optional[bool] = None
    description: Optional[str] = None
    confidence: Optional[float] = None
    casualties: Optional[int] = None


@router.get("")
def list_events(
    scenario_id: Optional[str] = Query(None),
    event_type: Optional[EventType] = Query(None),
    actor_uid: Optional[str] = Query(None),
    confirmed: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Event)
    if scenario_id:
        q = q.filter(Event.scenario_id == scenario_id)
    if event_type:
        q = q.filter(Event.event_type == event_type)
    if actor_uid:
        q = q.filter(Event.actor_uid == actor_uid)
    if confirmed is not None:
        q = q.filter(Event.confirmed == confirmed)
    events = q.order_by(Event.timestamp.desc()).all()
    return [_event_to_dict(e) for e in events]


@router.post("")
def create_event(body: EventCreate, db: Session = Depends(get_db)):
    event = Event(
        id=uuid.uuid4(),
        timestamp=body.timestamp or datetime.utcnow(),
        scenario_id=body.scenario_id,
        event_type=body.event_type,
        actor_uid=body.actor_uid,
        target_uid=body.target_uid,
        description=body.description,
        confirmed=body.confirmed,
        confidence=body.confidence,
        casualties=body.casualties,
        properties=body.properties,
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    if body.confirmed:
        _trigger_cascade(body.target_uid, body.confidence, body.scenario_id, db)

    return _event_to_dict(event)


@router.patch("/{event_id}")
def patch_event(event_id: str, body: EventPatch, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    was_confirmed = event.confirmed

    if body.confirmed is not None:
        event.confirmed = body.confirmed
    if body.description is not None:
        event.description = body.description
    if body.confidence is not None:
        event.confidence = body.confidence
    if body.casualties is not None:
        event.casualties = body.casualties

    db.commit()
    db.refresh(event)

    # Trigger cascade when newly confirmed
    if event.confirmed and not was_confirmed:
        _trigger_cascade(event.target_uid, event.confidence, event.scenario_id, db)

    return _event_to_dict(event)


def _trigger_cascade(target_uid: str, impact: float, scenario_id: str, db: Session):
    from services.cascade import run_cascade
    run_cascade(
        source_uid=target_uid,
        impact=impact * 0.8,
        max_depth=6,
        persist=True,
        scenario_id=scenario_id,
        db=db,
    )


def _event_to_dict(e: Event) -> dict:
    return {
        "id": str(e.id),
        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        "scenario_id": e.scenario_id,
        "event_type": e.event_type.value if e.event_type else None,
        "actor_uid": e.actor_uid,
        "target_uid": e.target_uid,
        "description": e.description,
        "confirmed": e.confirmed,
        "confidence": e.confidence,
        "casualties": e.casualties,
        "properties": e.properties,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }
