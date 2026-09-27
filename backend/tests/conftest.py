import pytest
import os
import sys

# Ensure backend root is on Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app as fastapi_app
import app.models as _app_models  # noqa: F401 - ensure all models are registered
from app.models.user import User
from app.core.security import create_access_token

# Test DB: In-memory SQLite by default, or PostgreSQL via TEST_DATABASE_URL env var
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

connect_args = {}
if TEST_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

_test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(scope="session")
def test_engine():
    return _test_engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def db_session():
    connection = _test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    user = db_session.query(User).filter(User.id == "00000000-0000-0000-0000-000000000001").first()
    if not user:
        user = User(
            id="00000000-0000-0000-0000-000000000001",
            name="FocusLoop Explorer",
            email="user@focusloop.local",
            username="explorer",
            timezone="UTC",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def client(db_session, test_user):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    token = create_access_token(user_id=test_user.id)
    with TestClient(fastapi_app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client
    fastapi_app.dependency_overrides.clear()
