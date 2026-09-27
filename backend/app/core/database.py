from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Configure engine arguments based on DB dialect (e.g. SQLite vs PostgreSQL pooling)
engine_kwargs = {
    "pool_pre_ping": True,
}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pool settings for high reliability
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined in models and run lightweight column migrations if needed."""
    import app.models  # noqa: F401 - Register all models with Base.metadata
    Base.metadata.create_all(bind=engine)

    # Lightweight migration helper for SQLite local databases
    if settings.DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                user_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
                if "username" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(50)"))
                if "bio" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN bio TEXT"))
                if "avatar_url" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"))
                if "password_hash" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                if "is_active" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))

                # Check behavior_profiles columns
                profile_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(behavior_profiles)")).fetchall()]
                if "visibility_settings" not in profile_cols:
                    conn.execute(text("ALTER TABLE behavior_profiles ADD COLUMN visibility_settings JSON DEFAULT '{}'"))
                if "behavior_score" not in profile_cols:
                    conn.execute(text("ALTER TABLE behavior_profiles ADD COLUMN behavior_score FLOAT DEFAULT 0.0"))
                if "current_level" not in profile_cols:
                    conn.execute(text("ALTER TABLE behavior_profiles ADD COLUMN current_level VARCHAR(50) DEFAULT 'Level 1 — Foundation'"))
                if "improvement_score" not in profile_cols:
                    conn.execute(text("ALTER TABLE behavior_profiles ADD COLUMN improvement_score FLOAT DEFAULT 0.0"))
                if "experiment_effectiveness" not in profile_cols:
                    conn.execute(text("ALTER TABLE behavior_profiles ADD COLUMN experiment_effectiveness FLOAT DEFAULT 0.0"))
                if "consistency" not in profile_cols:
                    conn.execute(text("ALTER TABLE behavior_profiles ADD COLUMN consistency FLOAT DEFAULT 0.0"))
                conn.commit()
        except Exception:
            pass
