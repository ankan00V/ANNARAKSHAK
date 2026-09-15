"""ORM tables.

Two invariants live in the schema rather than in Python, because a Python guard
is the first thing skipped at 3 a.m. before a demo:

- an Alert cannot be stored without at least one inspection task;
- one weather/phenology alert per farm, target and day (the risk job is
  idempotent by constraint, not by a SELECT-then-INSERT race).
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Farm(Base):
    __tablename__ = "farm"

    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    lang: Mapped[str] = mapped_column(String(2), default="mr")
    crop: Mapped[str] = mapped_column(String(20))
    variety: Mapped[str | None] = mapped_column(String(80))
    sowing_date: Mapped[date] = mapped_column(Date)
    district: Mapped[str] = mapped_column(String(60))
    village: Mapped[str | None] = mapped_column(String(80))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    area_acres: Mapped[float] = mapped_column(Float, default=1.0)
    soil: Mapped[str | None] = mapped_column(String(40))
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    problems: Mapped[list[Problem]] = relationship(back_populates="farm")


class Problem(Base):
    """One thing going wrong on one farm, from first photo to resolution."""

    __tablename__ = "problem"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farm.id"))
    target: Mapped[str | None] = mapped_column(String(60))
    """Current best label. Null while nobody — model or human — has settled it."""
    status: Mapped[str] = mapped_column(String(20), default="open")
    severity: Mapped[str] = mapped_column(String(10), default="medium")
    opened_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    farm: Mapped[Farm] = relationship(back_populates="problems")
    diagnoses: Mapped[list[Diagnosis]] = relationship(order_by="Diagnosis.id")
    observations: Mapped[list[Observation]] = relationship(order_by="Observation.id")


class Diagnosis(Base):
    __tablename__ = "diagnosis"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problem.id"))
    image_path: Mapped[str | None] = mapped_column(String(255))
    topk: Mapped[list] = mapped_column(JSON)
    gate_outcome: Mapped[str] = mapped_column(String(10))
    gate_reason: Mapped[str] = mapped_column(String(30))
    confidence: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(40))
    is_stub: Mapped[bool] = mapped_column(default=True)
    heatmap: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Observation(Base):
    """A farmer's field answer. Doubt Doctor answers land here and travel into
    the expert's case bundle — without that the question is theatre."""

    __tablename__ = "observation"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problem.id"))
    kind: Mapped[str] = mapped_column(String(20))
    cue_id: Mapped[str | None] = mapped_column(String(60))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Advisory(Base):
    __tablename__ = "advisory"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problem.id"))
    target: Mapped[str] = mapped_column(String(60))
    source: Mapped[str] = mapped_column(String(20))
    """'model' when the gate advised, 'doubt_doctor' when a cue resolved it,
    'expert' when an agronomist confirmed or corrected."""
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FollowUp(Base):
    __tablename__ = "followup"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problem.id"))
    due_on: Mapped[date] = mapped_column(Date)
    response: Mapped[str | None] = mapped_column(String(20))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime)


class Case(Base):
    """An escalation waiting for a human expert."""

    __tablename__ = "case"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problem.id"))
    status: Mapped[str] = mapped_column(String(20), default="open")
    reason: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)


class Confirmation(Base):
    """An expert's verdict. The labelled record that 'learns from field
    confirmations' reads — hotspots, the local prior and field accuracy."""

    __tablename__ = "confirmation"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("case.id"))
    problem_id: Mapped[int] = mapped_column(ForeignKey("problem.id"))
    verdict: Mapped[str] = mapped_column(String(20))
    model_label: Mapped[str | None] = mapped_column(String(60))
    """What the model predicted, frozen at confirm time. A correction overwrites
    Problem.target, so the model's guess is unrecoverable afterwards."""
    final_label: Mapped[str] = mapped_column(String(60))
    expert_name: Mapped[str] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)
    referred_to_lab: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("verdict IN ('confirmed', 'corrected')", name="ck_confirmation_verdict"),
    )


class Alert(Base):
    __tablename__ = "alert"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farm.id"))
    target: Mapped[str] = mapped_column(String(60))
    trigger: Mapped[str] = mapped_column(String(20))
    level: Mapped[str] = mapped_column(String(10))
    reason: Mapped[dict] = mapped_column(JSON)
    """Per-language sentence saying WHY, frozen at issue time."""
    tasks: Mapped[dict] = mapped_column(JSON)
    """Per-language list of 'go look here' tasks."""
    issued_on: Mapped[date] = mapped_column(Date)
    outcome: Mapped[str | None] = mapped_column(String(20))
    outcome_at: Mapped[datetime | None] = mapped_column(DateTime)
    source_case_id: Mapped[int | None] = mapped_column(ForeignKey("case.id"))

    __table_args__ = (
        # COALESCE: a missing '$.en' yields NULL, and a CHECK on NULL passes.
        CheckConstraint(
            "COALESCE(json_array_length(json_extract(tasks, '$.en')), 0) > 0",
            name="ck_alert_has_task",
        ),
        UniqueConstraint("farm_id", "target", "trigger", "issued_on", name="uq_alert_daily"),
    )


class TrapReading(Base):
    """Pheromone / light / sticky trap count — the PS's pest-trap input."""

    __tablename__ = "trap_reading"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farm.id"))
    target: Mapped[str] = mapped_column(String(60))
    trap_type: Mapped[str] = mapped_column(String(20))
    count: Mapped[int] = mapped_column(Integer)
    traps: Mapped[int] = mapped_column(Integer, default=1)
    nights: Mapped[int] = mapped_column(Integer, default=1)
    recorded_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("count >= 0 AND traps > 0 AND nights > 0", name="ck_trap_positive"),
    )


class SensorReading(Base):
    """A daily summary from an in-field sensor. When present it overrides the
    regional forecast for that farm and day — the canopy is what the fungus
    feels, not the district."""

    __tablename__ = "sensor_reading"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farm.id"))
    on: Mapped[date] = mapped_column(Date)
    rh_max: Mapped[float | None] = mapped_column(Float)
    t_min: Mapped[float | None] = mapped_column(Float)
    t_max: Mapped[float | None] = mapped_column(Float)
    rain_mm: Mapped[float | None] = mapped_column(Float)
    leaf_wetness_h: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (UniqueConstraint("farm_id", "on", name="uq_sensor_daily"),)


class LabelPrior(Base):
    __tablename__ = "label_prior"

    district: Mapped[str] = mapped_column(String(60), primary_key=True)
    crop: Mapped[str] = mapped_column(String(20), primary_key=True)
    target: Mapped[str] = mapped_column(String(60), primary_key=True)
    confirmed: Mapped[int] = mapped_column(Integer, default=0)
    corrected: Mapped[int] = mapped_column(Integer, default=0)
