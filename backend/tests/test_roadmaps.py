import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.field import Field
from app.models.specialization import Specialization
from app.models.roadmap import Roadmap
from app.models.user import User
from app.core.security import get_password_hash


@pytest.fixture
def admin_user(db: Session):
    """Create an admin user directly in the test DB."""
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


@pytest.fixture
def admin_headers(client: TestClient, admin_user):
    """Login as admin and return auth headers."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user.email,
            "password": "adminpass123",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_field(db: Session):
    """Create a test field directly in DB."""
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


@pytest.fixture
def test_specialization(db: Session, test_field, admin_user):
    """Create a published test specialization directly in DB."""
    spec = Specialization(
        field_id=test_field.id,
        name="Test Specialization",
        description="A specialization for testing",
        job_roles=["Developer", "Engineer"],
        status="published",
        created_by=admin_user.id,
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


@pytest.fixture
def test_roadmap(db: Session, test_specialization):
    """Create a published test roadmap directly in DB."""
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
            }
        ],
        status="published",
        ai_generated=False,
        version=1,
    )
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)
    return roadmap


# ─── Roadmap Tests ────────────────────────────────────────────────────────────

def test_get_roadmap_by_specialization(
    client: TestClient, test_roadmap, auth_headers
):
    response = client.get(
        f"/api/v1/roadmaps/specialization/{test_roadmap.specialization_id}",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Roadmap"
    assert data["status"] == "published"
    assert len(data["nodes"]) == 1


def test_get_roadmap_not_found(client: TestClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/roadmaps/specialization/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "No published roadmap found for this specialization"


def test_get_roadmap_by_id(
    client: TestClient, test_roadmap, auth_headers
):
    response = client.get(
        f"/api/v1/roadmaps/{test_roadmap.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert str(test_roadmap.id) == data["id"]


def test_create_roadmap_as_admin(
    client: TestClient, test_specialization, admin_headers
):
    response = client.post(
        "/api/v1/roadmaps",
        json={
            "specialization_id": str(test_specialization.id),
            "title": "New Roadmap",
            "nodes": [],
            "ai_generated": False,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Roadmap"
    assert data["status"] == "draft"
    assert data["version"] == 1


def test_create_roadmap_as_student_forbidden(
    client: TestClient, test_specialization, auth_headers
):
    response = client.post(
        "/api/v1/roadmaps",
        json={
            "specialization_id": str(test_specialization.id),
            "title": "Unauthorized Roadmap",
            "nodes": [],
            "ai_generated": False,
        },
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_update_roadmap_as_admin(
    client: TestClient, test_roadmap, admin_headers
):
    response = client.put(
        f"/api/v1/roadmaps/{test_roadmap.id}",
        json={"title": "Updated Roadmap Title"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Roadmap Title"


# ─── Fields Tests ─────────────────────────────────────────────────────────────

def test_list_fields(client: TestClient, test_field):
    response = client.get("/api/v1/fields")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


def test_get_field_by_id(client: TestClient, test_field):
    response = client.get(f"/api/v1/fields/{test_field.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Field"


def test_get_field_not_found(client: TestClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/fields/{fake_id}")
    assert response.status_code == 404


# ─── Specializations Tests ────────────────────────────────────────────────────

def test_list_specializations(client: TestClient, test_specialization):
    response = client.get("/api/v1/specializations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_get_specialization_by_id(client: TestClient, test_specialization):
    response = client.get(
        f"/api/v1/specializations/{test_specialization.id}"
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Specialization"


def test_create_specialization_as_admin(
    client: TestClient, test_field, admin_headers
):
    response = client.post(
        "/api/v1/specializations",
        json={
            "name": "New Specialization",
            "description": "A new one",
            "field_id": str(test_field.id),
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Specialization"
    assert data["status"] == "draft"


def test_create_specialization_as_student_forbidden(
    client: TestClient, test_field, auth_headers
):
    response = client.post(
        "/api/v1/specializations",
        json={
            "name": "Forbidden Spec",
            "field_id": str(test_field.id),
        },
        headers=auth_headers,
    )
    assert response.status_code == 403