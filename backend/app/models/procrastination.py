import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProcrastinationEvent(Base):
    __tablename__ = "procrastination_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    user_confirmed = Column(Boolean, default=True, nullable=False)  # User pressed "I'm procrastinating"
    trigger_reason = Column(String(100), nullable=True)  # "boredom", "overwhelmed", "unclear next step", etc.
    context_data = Column(JSON, nullable=True)  # apps opened, battery, device state
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="procrastination_events")
