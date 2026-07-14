import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Separate in-memory SQLite DB for tests
# Never touch the real PostgreSQL DB during testing
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """Create all tables once for the entire test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Fresh DB session per test function.
    Rolls back after each test so tests don't bleed into each other.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    """
    TestClient with get_db overridden to use the test DB session.
    This ensures every HTTP request in tests hits the test DB, not prod.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def registered_user(client):
    """Register a test user and return their credentials + token."""
    payload = {
        "email": "testuser@coursewright.com",
        "full_name": "Test User",
        "password": "testpass123",
        "degree": "BSIT",
        "year_of_study": 2,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"payload": payload, "token": token}


@pytest.fixture(scope="function")
def auth_headers(registered_user):
    """Authorization headers ready to pass into any protected request."""
    return {"Authorization": f"Bearer {registered_user['token']}"}