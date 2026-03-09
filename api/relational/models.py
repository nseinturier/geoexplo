import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Float, Integer,
    DateTime, Enum, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from relational.database import Base
import enum


class EventType(str, enum.Enum):
    strike = "strike"
    political = "political"
    economic = "economic"
    social = "social"
    diplomatic = "diplomatic"


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    scenario_id = Column(String, default="production", index=True)
    event_type = Column(Enum(EventType), nullable=False)
    actor_uid = Column(String, nullable=False)
    target_uid = Column(String, nullable=False)
    description = Column(Text, default="")
    confirmed = Column(Boolean, default=False)
    confidence = Column(Float, default=1.0)
    casualties = Column(Integer, nullable=True)
    properties = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class StabilitySnapshot(Base):
    __tablename__ = "stability_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    scenario_id = Column(String, default="production", index=True)
    object_uid = Column(String, nullable=False, index=True)
    stability_score = Column(Float, nullable=False)
    water_stress = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    forked_from = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_production = Column(Boolean, default=False)


class AnalystNote(Base):
    __tablename__ = "analyst_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_uid = Column(String, nullable=False, index=True)
    note = Column(Text, default="")
    author = Column(String, default="analyst")
    created_at = Column(DateTime, default=datetime.utcnow)
