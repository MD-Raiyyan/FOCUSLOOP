import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=True, default="FocusLoop Explorer")
    username = Column(String(50), unique=True, index=True, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    timezone = Column(String(50), default="UTC")

    # Onboarding & structured user context
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    onboarding_completed_at = Column(DateTime, nullable=True)
    onboarding_step = Column(String(20), default="1", nullable=False)
    age_range = Column(String(50), nullable=True)
    gender = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    checkins = relationship("TaskCheckin", back_populates="user", cascade="all, delete-orphan")
    procrastination_events = relationship("ProcrastinationEvent", back_populates="user", cascade="all, delete-orphan")
    screen_usages = relationship("ScreenUsage", back_populates="user", cascade="all, delete-orphan")
    behavior_metrics = relationship("BehaviorMetric", back_populates="user", cascade="all, delete-orphan")
    behavior_patterns = relationship("BehaviorPattern", back_populates="user", cascade="all, delete-orphan")
    behavior_profile = relationship("BehaviorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    refresh_sessions = relationship("RefreshSession", back_populates="user", cascade="all, delete-orphan")
    sleep_records = relationship("SleepRecord", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("UserGoal", back_populates="user", cascade="all, delete-orphan")
    routine_context = relationship("UserRoutineContext", back_populates="user", uselist=False, cascade="all, delete-orphan")
    challenges = relationship("UserChallenge", back_populates="user", cascade="all, delete-orphan")
    interests = relationship("UserInterest", back_populates="user", cascade="all, delete-orphan")

