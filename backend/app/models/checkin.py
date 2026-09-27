import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class TaskCheckin(Base):
    __tablename__ = "task_checkins"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    status = Column(String(20), nullable=False)  # done, partial, missed
    completed_at = Column(DateTime, nullable=True)
    actual_start_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    start_delay_minutes = Column(Integer, nullable=True)  # calculated delay from planned_time
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("task_id", "date", name="uq_task_checkin_task_date"),
    )

    # Relationships
    user = relationship("User", back_populates="checkins")
    task = relationship("Task", back_populates="checkins")
