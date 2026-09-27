import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pattern_id = Column(String(36), ForeignKey("behavior_patterns.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    hypothesis = Column(Text, nullable=False)  # "If I schedule tasks for 10am instead of 2pm, start delay will drop"
    intervention_type = Column(String(100), nullable=True)  # "time_shift", "micro_commitment", "app_lock"
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=True)
    target_metric = Column(String(100), nullable=False)  # "start_delay_minutes", "completion_rate"
    baseline_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)
    status = Column(String(50), default="suggested")  # "suggested", "active", "completed", "dismissed"
    pattern_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="experiments")
    pattern = relationship("BehaviorPattern", back_populates="experiments")
    results = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    before_value = Column(Float, nullable=True)
    after_value = Column(Float, nullable=True)
    change_value = Column(Float, nullable=True)  # after_value - before_value
    percent_change = Column(Float, nullable=True)
    conclusion = Column(String(50), default="inconclusive")  # "positive", "neutral", "negative", "inconclusive"
    result_summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    experiment = relationship("Experiment", back_populates="results")
