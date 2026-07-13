import logging
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.core.config import settings
from app.models.field import Field
from app.models.user import User

logger = logging.getLogger(__name__)

QUEST_FIELDS = [
    {
        "name": "Information Technology",
        "description": "Covers networking, systems, databases, and software applications.",
        "category": "Technology",
        "icon_key": "it",
    },
    {
        "name": "Computer Science",
        "description": "Focuses on algorithms, programming, AI, and theoretical computing.",
        "category": "Technology",
        "icon_key": "cs",
    },
    {
        "name": "Software Engineering",
        "description": "Covers software design, development methodologies, and project management.",
        "category": "Technology",
        "icon_key": "se",
    },
    {
        "name": "Data Science / AI",
        "description": "Focuses on machine learning, data analysis, and intelligent systems.",
        "category": "Technology",
        "icon_key": "ds",
    },
    {
        "name": "Electrical Engineering",
        "description": "Covers circuits, power systems, electronics, and embedded systems.",
        "category": "Engineering",
        "icon_key": "ee",
    },
    {
        "name": "Civil Engineering",
        "description": "Focuses on infrastructure, structural design, and construction management.",
        "category": "Engineering",
        "icon_key": "ce",
    },
    {
        "name": "Business Administration",
        "description": "Covers management, finance, marketing, and organizational behavior.",
        "category": "Business",
        "icon_key": "ba",
    },
    {
        "name": "Environmental Engineering",
        "description": "Focuses on environmental protection, sustainability, and resource management.",
        "category": "Engineering",
        "icon_key": "enve",
    },
]


def seed_fields(db: Session) -> None:
    existing = db.query(Field).count()
    if existing > 0:
        logger.info("Fields already seeded — skipping.")
        return
    for field_data in QUEST_FIELDS:
        db.add(Field(**field_data))
    db.commit()
    logger.info(f"Seeded {len(QUEST_FIELDS)} QUEST fields.")


def seed_admin(db: Session) -> None:
    email = getattr(settings, "FIRST_ADMIN_EMAIL", None)
    password = getattr(settings, "FIRST_ADMIN_PASSWORD", None)
    if not email or not password:
        logger.warning("FIRST_ADMIN_EMAIL or FIRST_ADMIN_PASSWORD not set — skipping admin seed.")
        return
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        logger.info("Admin user already exists — skipping.")
        return
    admin = User(
        email=email,
        password_hash=get_password_hash(password),
        full_name="Coursewright Admin",
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    logger.info(f"Admin user seeded: {email}")


def init_db(db: Session) -> None:
    seed_fields(db)
    seed_admin(db)
    