from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ATOPlan(Base):
    __tablename__ = "ato_plans"

    id = Column(String(36), primary_key=True, index=True)
    conversation_id = Column(ForeignKey("conversations.id"), nullable=True, index=True)
    user_request = Column(Text, nullable=False)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(40), nullable=False, default="pending_approval", index=True)
    clarification_questions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    jobs = relationship("ATOJob", back_populates="plan", cascade="all, delete-orphan", order_by="ATOJob.created_at")


class ATOJob(Base):
    __tablename__ = "ato_jobs"

    id = Column(String(36), primary_key=True, index=True)
    plan_id = Column(ForeignKey("ato_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    job_key = Column(String(80), nullable=False)
    job_type = Column(String(80), nullable=False)
    target_agent = Column(String(80), nullable=False)
    description = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    schedule = Column(JSON, nullable=False, default=dict)
    depends_on = Column(JSON, nullable=False, default=list)
    status = Column(String(40), nullable=False, default="awaiting_approval", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    plan = relationship("ATOPlan", back_populates="jobs")
