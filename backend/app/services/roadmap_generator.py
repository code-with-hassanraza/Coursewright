"""
roadmap_generator.py — Generates AI roadmap nodes for a specialization.

Responsibility:
  - Build a context-rich prompt from specialization data
  - Call AIService.generate_json() with the exact tested system prompt
  - Validate and sanitize the returned node list
  - Return a clean list[dict] ready for crud_roadmap.create()

Does NOT touch the DB — that is review_service's job.
"""

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# ── System prompt (exact, tested — do not modify) ─────────────────────────────

_ROADMAP_SYSTEM_PROMPT = """\
You are an expert curriculum designer for university students in Pakistan.
Return ONLY a valid JSON array. No markdown fences, no text outside the array.

Each element must exactly match this schema:
{
  "id": "snake_case_unique_id",
  "title": "Human Readable Title",
  "description": "2-3 sentences about what this covers and why it matters",
  "type": "topic",
  "order": 1,
  "parent_id": null,
  "estimated_hours": 10,
  "resources": []
}

Rules:
- type: topic | skill | project | milestone
- All IDs unique snake_case (e.g. linux_fundamentals, aws_iam_basics)
- order starts at 1, no gaps
- parent_id null for top-level, parent id string for sub-topics
- estimated_hours integer 2-40
- 15-25 nodes total
- At least 2 project nodes
- resources always []"""

# ── Validation constants ───────────────────────────────────────────────────────

_REQUIRED_FIELDS = {"id", "title", "type", "order", "resources"}
_VALID_TYPES     = {"topic", "skill", "project", "milestone"}
_MIN_NODES       = 5    # hard minimum after validation (warn below 15)
_MAX_HOURS       = 40
_MIN_HOURS       = 2
_DEFAULT_HOURS   = 10


# ══════════════════════════════════════════════════════════════════════════════
# RoadmapGenerator
# ══════════════════════════════════════════════════════════════════════════════

class RoadmapGenerator:
    """
    Generates a structured roadmap (list of validated node dicts) for a
    given Specialization ORM object using the AI service.

    Usage (import inside function body as per project rules):
        from app.services.roadmap_generator import RoadmapGenerator
        generator = RoadmapGenerator()
        nodes = generator.generate_roadmap(specialization)
    """

    # ── Private: prompt builder ────────────────────────────────────────────────

    def _build_user_prompt(self, specialization) -> str:
        """
        Construct a rich generation prompt from all available
        specialization fields. Falls back gracefully if any field is missing.
        """
        # Resolve field name via ORM relationship (may not be loaded)
        field_name = "General"
        try:
            if specialization.field and specialization.field.name:
                field_name = specialization.field.name
        except Exception:
            pass

        # Resolve job roles (stored as JSON / list)
        job_roles_str = ""
        try:
            roles = specialization.job_roles
            if isinstance(roles, list) and roles:
                job_roles_str = ", ".join(str(r) for r in roles)
        except Exception:
            pass

        lines = [
            f"Generate a complete learning roadmap for the specialization: "
            f"'{specialization.name}'",
            f"Field of study: {field_name}",
        ]

        if specialization.description:
            lines.append(f"Overview: {specialization.description}")

        if job_roles_str:
            lines.append(f"Target job roles graduates pursue: {job_roles_str}")

        if specialization.prerequisites:
            lines.append(f"Prerequisites students should already have: {specialization.prerequisites}")

        if specialization.real_world_example:
            lines.append(f"Real-world context: {specialization.real_world_example}")

        if specialization.salary_range:
            lines.append(f"Expected salary range: {specialization.salary_range}")

        lines.append(
            "\nRequirements:"
            "\n- 15 to 25 nodes progressing from beginner to job-ready"
            "\n- At least 2 project nodes for hands-on practice"
            "\n- Cover theory, tools, skills, and real projects"
            "\n- Return the JSON array only, no extra text"
        )

        return "\n".join(lines)

    # ── Private: validator ─────────────────────────────────────────────────────

    def _validate_nodes(self, raw: Any) -> list[dict]:
        """
        Validate and sanitize AI-generated nodes.

        - Skips nodes missing required fields (logs warning)
        - Fixes minor type/value issues in-place
        - Deduplicates IDs and orders
        - Sorts by order ascending
        - Raises ValueError if result has fewer than _MIN_NODES valid nodes
        """
        if not isinstance(raw, list):
            raise ValueError(
                f"Expected JSON array from AI, got {type(raw).__name__}. "
                "Check system prompt — model may have returned an object."
            )

        validated: list[dict] = []
        seen_ids: set[str]   = set()

        for idx, node in enumerate(raw):
            if not isinstance(node, dict):
                logger.warning(f"_validate_nodes › skipping non-dict at index {idx}")
                continue

            # ── Required fields check ──────────────────────────────────────────
            missing = _REQUIRED_FIELDS - node.keys()
            if missing:
                logger.warning(
                    f"_validate_nodes › node[{idx}] missing {missing}, skipping"
                )
                continue

            # ── id ─────────────────────────────────────────────────────────────
            node_id = str(node["id"]).strip().lower().replace(" ", "_")
            if not node_id:
                logger.warning(f"_validate_nodes › node[{idx}] empty id, skipping")
                continue
            if node_id in seen_ids:
                logger.warning(f"_validate_nodes › duplicate id '{node_id}', skipping")
                continue
            seen_ids.add(node_id)
            node["id"] = node_id

            # ── title ──────────────────────────────────────────────────────────
            node["title"] = str(node.get("title", "Untitled")).strip() or "Untitled"

            # ── type ───────────────────────────────────────────────────────────
            node_type = str(node.get("type", "topic")).lower().strip()
            if node_type not in _VALID_TYPES:
                logger.warning(
                    f"_validate_nodes › node '{node_id}' invalid type "
                    f"'{node_type}', defaulting to 'topic'"
                )
                node_type = "topic"
            node["type"] = node_type

            # ── order ──────────────────────────────────────────────────────────
            try:
                node["order"] = int(node["order"])
            except (ValueError, TypeError):
                node["order"] = idx + 1
                logger.warning(
                    f"_validate_nodes › node '{node_id}' invalid order, "
                    f"assigned {node['order']}"
                )

            # ── estimated_hours ────────────────────────────────────────────────
            try:
                hours = int(node.get("estimated_hours", _DEFAULT_HOURS))
                node["estimated_hours"] = max(_MIN_HOURS, min(_MAX_HOURS, hours))
            except (ValueError, TypeError):
                node["estimated_hours"] = _DEFAULT_HOURS

            # ── description ────────────────────────────────────────────────────
            node["description"] = str(node.get("description", "")).strip()

            # ── parent_id ──────────────────────────────────────────────────────
            parent_id = node.get("parent_id")
            if parent_id is not None:
                parent_id = str(parent_id).strip()
                node["parent_id"] = parent_id if parent_id else None
            else:
                node["parent_id"] = None

            # ── resources — always reset to empty list ─────────────────────────
            # ResourceCurator fills this in the next step
            node["resources"] = []

            validated.append(node)

        # ── Minimum viable check ───────────────────────────────────────────────
        if len(validated) < _MIN_NODES:
            raise ValueError(
                f"Only {len(validated)} valid nodes after validation "
                f"(minimum {_MIN_NODES}). AI output may be malformed."
            )

        if len(validated) < 15:
            logger.warning(
                f"_validate_nodes › only {len(validated)} nodes "
                f"(expected 15-25). Continuing with what we have."
            )

        # Sort by order for clean storage
        validated.sort(key=lambda n: n["order"])
        return validated

    # ── Public: main entry point ───────────────────────────────────────────────

    def generate_roadmap(self, specialization) -> list[dict]:
        """
        Generate 15-25 validated roadmap nodes for a specialization.

        Args:
            specialization: Specialization ORM object.
                            The .field relationship should be loaded for best results.

        Returns:
            list[dict] — validated nodes, sorted by order, resources=[].
            Ready to pass directly to crud_roadmap.create() via RoadmapCreate schema.

        Raises:
            RuntimeError: AI generation failed across all providers/retries.
            ValueError:   AI output could not be validated into usable nodes.
        """
        from app.services.ai_service import AIService

        logger.info(
            f"RoadmapGenerator › starting generation for "
            f"specialization='{specialization.name}'"
        )

        ai          = AIService()
        user_prompt = self._build_user_prompt(specialization)

        logger.info("RoadmapGenerator › calling AIService.generate_json()")

        try:
            raw_nodes = ai.generate_json(
                user_prompt=user_prompt,
                system_prompt=_ROADMAP_SYSTEM_PROMPT,
            )
        except RuntimeError as exc:
            logger.error(f"RoadmapGenerator › AI failed: {exc}")
            raise

        raw_count = len(raw_nodes) if isinstance(raw_nodes, list) else "non-list"
        logger.info(f"RoadmapGenerator › AI returned {raw_count} raw nodes")

        nodes = self._validate_nodes(raw_nodes)

        logger.info(
            f"RoadmapGenerator › done — {len(nodes)} validated nodes "
            f"for '{specialization.name}'"
        )
        return nodes