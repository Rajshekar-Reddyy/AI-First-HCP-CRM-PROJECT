from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SQLAlchemyEnum, ForeignKey, Index, Integer, String, Text, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base."""


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class HCP(Base):
    __tablename__ = "hcp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    hospital: Mapped[str | None] = mapped_column(String(180), index=True)
    specialization: Mapped[str | None] = mapped_column(String(120), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    interactions: Mapped[list["Interaction"]] = relationship(back_populates="hcp", cascade="all, delete-orphan")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="hcp", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_hcp_name_hospital", "name", "hospital"),)


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hcp_id: Mapped[int] = mapped_column(ForeignKey("hcp.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_type: Mapped[str | None] = mapped_column(String(80))
    interaction_date: Mapped[date | None] = mapped_column(Date, index=True)
    interaction_time: Mapped[time | None] = mapped_column(Time)
    attendees: Mapped[str | None] = mapped_column(Text)
    topics_discussed: Mapped[str | None] = mapped_column(Text)
    voice_summary: Mapped[str | None] = mapped_column(Text)
    materials_shared: Mapped[str | None] = mapped_column(Text)
    samples_distributed: Mapped[str | None] = mapped_column(Text)
    sentiment: Mapped[Sentiment] = mapped_column(SQLAlchemyEnum(Sentiment), default=Sentiment.neutral, index=True)
    outcome: Mapped[str | None] = mapped_column(Text)
    follow_up: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    hcp: Mapped[HCP] = relationship(back_populates="interactions")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="interaction", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_interactions_hcp_date", "hcp_id", "interaction_date"),)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(140), unique=True, nullable=False, index=True)
    benefits: Mapped[str] = mapped_column(Text, nullable=False)
    dosage: Mapped[str] = mapped_column(Text, nullable=False)
    side_effects: Mapped[str] = mapped_column(Text, nullable=False)
    clinical_notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hcp_id: Mapped[int] = mapped_column(ForeignKey("hcp.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_id: Mapped[int | None] = mapped_column(ForeignKey("interactions.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hcp: Mapped[HCP] = relationship(back_populates="reminders")
    interaction: Mapped[Interaction | None] = relationship(back_populates="reminders")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class ToolLog(Base):
    __tablename__ = "tool_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    input_json: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
