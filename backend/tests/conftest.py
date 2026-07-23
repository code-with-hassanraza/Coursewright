import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.models.field import Field
from app.models.specialization import Specialization
from app.models.roadmap import Roadmap
from app.models.quiz import Quiz
from app.models.task import Task
from app.models.resource import Resource
from app.models.review import Review
from app.models.user_progress import UserProgress
from app.core.security import get_password_hash

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
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─── User Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def registered_user(client):
    payload = {
        "email": "testuser@coursewright.com",
        "full_name": "Test User",
        "password": "testpass123",
        "degree": "BSIT",
        "year_of_study": 2,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return {"payload": payload, "token": response.json()["access_token"]}


@pytest.fixture(scope="function")
def auth_headers(registered_user):
    return {"Authorization": f"Bearer {registered_user['token']}"}


@pytest.fixture(scope="function")
def admin_user(db):
    user = User(
        email="admin@test.com",
        password_hash=get_password_hash("adminpass123"),
        full_name="Admin User",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_headers(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.email, "password": "adminpass123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="function")
def reviewer_user(db):
    user = User(
        email="reviewer@test.com",
        password_hash=get_password_hash("reviewerpass123"),
        full_name="Reviewer User",
        role="reviewer",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def reviewer_headers(client, reviewer_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": reviewer_user.email, "password": "reviewerpass123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# ─── Data Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_field(db):
    field = Field(
        name="Test Field",
        description="A field for testing",
        category="Technology",
        icon_key="test",
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@pytest.fixture(scope="function")
def test_specialization(db, test_field, admin_user):
    spec = Specialization(
        field_id=test_field.id,
        name="Test Specialization",
        description="A specialization for testing",
        job_roles=["Developer", "Engineer"],
        salary_range="PKR 80,000 - 200,000",
        status="published",
        created_by=admin_user.id,
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


@pytest.fixture(scope="function")
def test_roadmap(db, test_specialization):
    roadmap = Roadmap(
        specialization_id=test_specialization.id,
        title="Test Roadmap",
        nodes=[
            {
                "id": "node-1",
                "title": "Introduction",
                "description": "Getting started",
                "type": "topic",
                "order": 1,
                "parent_id": None,
                "estimated_hours": 4,
                "resources": [],
            },
            {
                "id": "node-2",
                "title": "Advanced Topics",
                "description": "Going deeper",
                "type": "skill",
                "order": 2,
                "parent_id": None,
                "estimated_hours": 8,
                "resources": [],
            },
        ],
        status="published",
        ai_generated=False,
        version=1,
    )
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)
    return roadmap


@pytest.fixture(scope="function")
def test_quiz(db, test_specialization):
    quiz = Quiz(
        specialization_id=test_specialization.id,
        title="Test Quiz",
        questions=[
            {
                "id": "q1",
                "question": "What is Python?",
                "options": ["A language", "A snake", "A tool", "An OS"],
                "correct": "A language",
                "explanation": "Python is a programming language.",
            },
            {
                "id": "q2",
                "question": "What is FastAPI?",
                "options": ["A framework", "A database", "A server", "A language"],
                "correct": "A framework",
                "explanation": "FastAPI is a web framework.",
            },
            {
                "id": "q3",
                "question": "What is SQLAlchemy?",
                "options": ["An ORM", "A language", "A cloud service", "A test tool"],
                "correct": "An ORM",
                "explanation": "SQLAlchemy is an ORM.",
            },
        ],
        pass_score=70,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


@pytest.fixture(scope="function")
def test_task(db, test_specialization):
    task = Task(
        specialization_id=test_specialization.id,
        title="Build a REST API",
        description="Build your first API",
        instructions="Step 1: Set up FastAPI\nStep 2: Create endpoints",
        difficulty="beginner",
        suggested_tools=["FastAPI", "Postman"],
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture(scope="function")
def test_resource(db, test_roadmap):
    resource = Resource(
        roadmap_id=test_roadmap.id,
        node_id="node-1",
        title="Python Tutorial",
        url="https://docs.python.org",
        type="docs",
        is_free=True,
        verified=True,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@pytest.fixture(scope="function")
def test_progress(db, registered_user, test_specialization, test_roadmap):
    """Progress record for the registered_user on test_specialization."""
    from app.crud import crud_user
    user = crud_user.get_by_email(db, email=registered_user["payload"]["email"])
    progress = UserProgress(
        user_id=user.id,
        specialization_id=test_specialization.id,
        roadmap_id=test_roadmap.id,
        status="exploring",
        completed_nodes=[],
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


@pytest.fixture(scope="function")
def test_review(db, test_specialization, reviewer_user):
    review = Review(
        content_type="specialization",
        content_id=test_specialization.id,
        reviewer_id=reviewer_user.id,
        status="pending",
        notes=None,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review