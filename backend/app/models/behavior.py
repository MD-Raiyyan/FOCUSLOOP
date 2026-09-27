import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class BehaviorMetric(Base):
    __tablename__ = "behavior_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False, index=True)  # "completion_rate", "avg_start_delay", "focus_ratio"
    metric_value = Column(Float, nullable=False)
    time_window_start = Column(DateTime, nullable=True)
    time_window_end = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="behavior_metrics")


class BehaviorPattern(Base):
    __tablename__ = "behavior_patterns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pattern_type = Column(String(100), nullable=False)  # "time_of_day_delay", "post_lunch_slump", "distraction_loop"
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    confidence = Column(String(20), default="moderate")  # "low", "moderate", "high"
    sample_size = Column(Integer, default=1)
    first_detected = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_detected = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(30), default="active")  # "active", "improving", "resolved", "archived"
    supporting_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="behavior_patterns")


DEFAULT_PROFILE_VISIBILITY = {
    "current_level": False,
    "behavior_score": False,
    "improvement_score": True,
    "experiment_effectiveness": True,
    "consistency": True,
    "behavioral_patterns": False,
}


class BehaviorProfile(Base):
    __tablename__ = "behavior_profiles"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    profile_data = Column(JSON, nullable=False, default=dict)
    visibility_settings = Column(JSON, nullable=False, default=lambda: dict(DEFAULT_PROFILE_VISIBILITY))
    
    # Progress and grading metrics
    behavior_score = Column(Float, nullable=True, default=0.0)
    current_level = Column(String(50), nullable=True, default="Level 1 — Foundation")
    improvement_score = Column(Float, nullable=True, default=0.0)
    experiment_effectiveness = Column(Float, nullable=True, default=0.0)
    consistency = Column(Float, nullable=True, default=0.0)

    model_version = Column(String(50), default="v1.0")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="behavior_profile")
