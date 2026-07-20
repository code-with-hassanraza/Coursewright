"""
review_service.py — Orchestrates AI generation and review workflow.

Responsibility:
  - trigger_generation(): full pipeline from specialization → draft roadmap → pending review
  - Called exclusively by POST /admin/generate-roadmap/{specialization_id}

Pipeline sequence:
  1. Fetch specialization from DB         (404 if missing)
  2. RoadmapGenerator.generate_roadmap()  → validated node list
  3. ResourceCurator.curate_for_roadmap() → nodes with resources filled in
  4. crud_roadmap.create()                → Roadmap(status="draft", ai_generated=True)
  5. crud_review.create()                 → Review(status="pending")
  6. Return {"roadmap": Roadmap, "review": Review}

Error strategy:
  - Step 1 failure  → HTTP 404
  - Step 2 failure  → HTTP 422 (AI could not generate)
  - Step 3 failure  → non-fatal, log warning and continue with resources=[]
  - Step 4-5 failure → HTTP 500 (DB write failed)
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.crud import crud_roadmap, crud_review, crud_specialization
from app.schemas.roadmap import RoadmapCreate, RoadmapNode

logger = get_logger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# trigger_generation
# ══════════════════════════════════════════════════════════════════════════════

def trigger_generation(
    specialization_id: UUID,
    reviewer_id: UUID,
    db: Session,
) -> dict:
    """
    Full AI generation pipeline for a specialization roadmap.

    Args:
        specialization_id : UUID of the target specialization
        reviewer_id       : UUID of the admin triggering generation
        db                : SQLAlchemy Session from get_db()

    Returns:
        {
            "roadmap": Roadmap ORM object  (status="draft", ai_generated=True),
            "review":  Review ORM object   (status="pending"),
        }

    Raises:
        HTTPException 404 : specialization not found
        HTTPException 422 : AI generation or schema validation failed
        HTTPException 500 : database write failed
    """
    # Services are imported inside the function body per project rules
    from app.services.roadmap_generator import RoadmapGenerator
    from app.services.resource_curator import ResourceCurator

    # ── Step 1 — Fetch specialization ─────────────────────────────────────────
    logger.info(
        f"trigger_generation › fetching specialization_id={specialization_id}"
    )

    specialization = crud_specialization.get(db, specialization_id)

    if not specialization:
        logger.warning(
            f"trigger_generation › specialization {specialization_id} not found"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specialization {specialization_id} not found.",
        )

    logger.info(
        f"trigger_generation › found '{specialization.name}' — starting AI pipeline"
    )

    # ── Step 2 — Generate roadmap nodes via AI ─────────────────────────────────
    try:
        generator = RoadmapGenerator()
        nodes     = generator.generate_roadmap(specialization)
    except (RuntimeError, ValueError) as exc:
        logger.error(
            f"trigger_generation › roadmap generation failed for "
            f"'{specialization.name}': {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"AI roadmap generation failed: {str(exc)}",
        )

    logger.info(
        f"trigger_generation › {len(nodes)} nodes generated — "
        f"starting resource curation"
    )

    # ── Step 3 — Curate resources (non-fatal) ─────────────────────────────────
    try:
        curator = ResourceCurator()
        nodes   = curator.curate_for_roadmap(nodes, specialization.name)
    except Exception as exc:
        # Resource curation failure never blocks roadmap creation
        # Nodes already default to resources=[] so the roadmap is still valid
        logger.warning(
            f"trigger_generation › resource curation raised an unexpected error "
            f"(continuing with empty resources): {exc}"
        )

    # ── Step 4 — Convert node dicts → RoadmapNode schema objects ──────────────
    try:
        roadmap_nodes = [RoadmapNode(**node) for node in nodes]
    except Exception as exc:
        logger.error(
            f"trigger_generation › RoadmapNode schema validation failed: {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Generated nodes failed schema validation: {str(exc)}",
        )

    # ── Step 5 — Persist roadmap as draft ─────────────────────────────────────
    roadmap_in = RoadmapCreate(
        specialization_id=specialization_id,
        title=f"{specialization.name} Roadmap",
        nodes=roadmap_nodes,
        ai_generated=True,
    )

    try:
        roadmap = crud_roadmap.create(db, obj_in=roadmap_in)
    except Exception as exc:
        logger.error(
            f"trigger_generation › DB error saving roadmap for "
            f"'{specialization.name}': {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save generated roadmap to database.",
        )

    logger.info(
        f"trigger_generation › roadmap {roadmap.id} saved "
        f"(status=draft, ai_generated=True, nodes={len(nodes)})"
    )

    # ── Step 6 — Create pending review record ─────────────────────────────────
    try:
        review = crud_review.create(
            db,
            content_type="roadmap",
            content_id=roadmap.id,
            reviewer_id=reviewer_id,
        )
    except Exception as exc:
        logger.error(
            f"trigger_generation › DB error saving review for "
            f"roadmap {roadmap.id}: {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Roadmap saved but failed to create review record.",
        )

    logger.info(
        f"trigger_generation › review {review.id} created (status=pending)"
    )

    logger.info(
        f"trigger_generation › pipeline complete — "
        f"roadmap={roadmap.id}, review={review.id}"
    )

    return {
        "roadmap": roadmap,
        "review":  review,
    }