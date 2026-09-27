import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ScreenUsage(Base):
    __tablename__ = "screen_usage"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    app_identifier = Column(String(200), nullable=False)  # e.g., "com.instagram.android"
    app_name = Column(String(100), nullable=False)  # e.g., "Instagram"
    category = Column(String(50), nullable=True)  # "Social", "Entertainment", "Productivity"
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    source = Column(String(50), default="device_stats")  # "device_stats", "manual_log"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="screen_usages")
