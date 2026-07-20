"""
resource_curator.py — Curates free learning resources for each roadmap node.

Responsibility:
  - Accept the validated node list from RoadmapGenerator
  - For each node, call AIService.generate_json() to get 3-5 free resources
  - Validate each resource (url, type, is_free)
  - Return the same node list with resources[] populated
  - Failures on individual nodes are logged and skipped (never crash the whole batch)

Does NOT touch the DB — that is review_service's job.
"""

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# ── System prompt (exact, tested — do not modify) ─────────────────────────────

_RESOURCE_SYSTEM_PROMPT = """\
You are a learning resource expert. Suggest 3-5 FREE resources.
Return ONLY a valid JSON array. No markdown, no text outside the array.

Each resource:
{"title":"...","url":"https://...","type":"youtube","is_free":true,"description":"one sentence"}

type: youtube | article | course | docs | github

Priority: official docs → freeCodeCamp → YouTube educators (NetworkChuck,
Traversy Media, Fireship, StatQuest) → free Coursera/edX → GitHub learning repos.

Only suggest resources you are confident exist. Do not invent URLs."""

# ── Validation constants ───────────────────────────────────────────────────────

_REQUIRED_RESOURCE_FIELDS = {"title", "url", "type", "is_free", "description"}
_VALID_RESOURCE_TYPES      = {"youtube", "article", "course", "docs", "github"}
_MIN_RESOURCES_PER_NODE    = 0   # 0 = keep node even if no resources found
_MAX_RESOURCES_PER_NODE    = 5


# ══════════════════════════════════════════════════════════════════════════════
# ResourceCurator
# ══════════════════════════════════════════════════════════════════════════════

class ResourceCurator:
    """
    Curates free learning resources for a list of roadmap nodes.

    Usage (import inside function body as per project rules):
        from app.services.resource_curator import ResourceCurator
        curator  = ResourceCurator()
        nodes_with_resources = curator.curate_for_roadmap(nodes, specialization_name)
    """

    # ── Private: prompt builder ────────────────────────────────────────────────

    def _build_resource_prompt(self, node: dict, specialization_name: str) -> str:
        """
        Build a curation prompt for a single roadmap node.
        """
        title       = node.get("title", "Unknown Topic")
        description = node.get("description", "")
        node_type   = node.get("type", "topic")
        hours       = node.get("estimated_hours", 10)

        lines = [
            f"Find 3-5 FREE learning resources for the following topic:",
            f"Topic: {title}",
            f"Part of specialization: {specialization_name}",
            f"Type: {node_type} (~{hours} hours of study)",
        ]

        if description:
            lines.append(f"Description: {description}")

        lines.append(
            "Return only resources that are genuinely free and likely to still exist. "
            "Prefer official documentation, freeCodeCamp, and trusted YouTube educators. "
            "Return the JSON array only."
        )

        return "\n".join(lines)

    # ── Private: resource validator ────────────────────────────────────────────

    def _validate_resources(
        self,
        raw: Any,
        node_title: str,
    ) -> list[dict]:
        """
        Validate and sanitize AI-generated resources for a single node.
        Never raises — returns an empty list on total failure.
        """
        if not isinstance(raw, list):
            logger.warning(
                f"_validate_resources › expected list for '{node_title}', "
                f"got {type(raw).__name__}"
            )
            return []

        validated: list[dict] = []
        seen_urls: set[str]   = set()

        for idx, resource in enumerate(raw):
            if not isinstance(resource, dict):
                logger.warning(
                    f"_validate_resources › non-dict resource at index {idx} "
                    f"for '{node_title}', skipping"
                )
                continue

            # ── Required fields ────────────────────────────────────────────────
            missing = _REQUIRED_RESOURCE_FIELDS - resource.keys()
            if missing:
                logger.warning(
                    f"_validate_resources › resource[{idx}] for '{node_title}' "
                    f"missing {missing}, skipping"
                )
                continue

            # ── URL ────────────────────────────────────────────────────────────
            url = str(resource.get("url", "")).strip()
            if not url.startswith("http"):
                logger.warning(
                    f"_validate_resources › invalid URL '{url}' for '{node_title}', "
                    f"skipping"
                )
                continue
            if url in seen_urls:
                logger.warning(
                    f"_validate_resources › duplicate URL '{url}', skipping"
                )
                continue
            seen_urls.add(url)
            resource["url"] = url

            # ── title ──────────────────────────────────────────────────────────
            resource["title"] = str(resource.get("title", "")).strip() or "Resource"

            # ── type ───────────────────────────────────────────────────────────
            res_type = str(resource.get("type", "article")).lower().strip()
            if res_type not in _VALID_RESOURCE_TYPES:
                logger.warning(
                    f"_validate_resources › unknown type '{res_type}' for "
                    f"'{node_title}', defaulting to 'article'"
                )
                res_type = "article"
            resource["type"] = res_type

            # ── is_free ────────────────────────────────────────────────────────
            # Always enforce free — this is our policy
            resource["is_free"] = True

            # ── description ────────────────────────────────────────────────────
            resource["description"] = str(
                resource.get("description", "")
            ).strip()

            validated.append(resource)

            # Cap at max resources per node
            if len(validated) >= _MAX_RESOURCES_PER_NODE:
                break

        return validated

    # ── Private: single node curator ──────────────────────────────────────────

    def _curate_node(self, node: dict, specialization_name: str) -> list[dict]:
        """
        Curate resources for a single node.
        Returns empty list on failure — never raises.
        """
        from app.services.ai_service import AIService

        node_title  = node.get("title", "Unknown")
        user_prompt = self._build_resource_prompt(node, specialization_name)
        ai          = AIService()

        try:
            raw_resources = ai.generate_json(
                user_prompt=user_prompt,
                system_prompt=_RESOURCE_SYSTEM_PROMPT,
            )
            resources = self._validate_resources(raw_resources, node_title)
            logger.info(
                f"_curate_node › '{node_title}' → {len(resources)} resources"
            )
            return resources

        except RuntimeError as exc:
            # All AI providers exhausted — log and return empty
            logger.error(
                f"_curate_node › AI failed for '{node_title}': {exc}. "
                f"Node will have empty resources."
            )
            return []

        except Exception as exc:
            logger.error(
                f"_curate_node › unexpected error for '{node_title}': {exc}. "
                f"Node will have empty resources."
            )
            return []

    # ── Public: main entry point ───────────────────────────────────────────────

    def curate_for_roadmap(
        self,
        nodes: list[dict],
        specialization_name: str = "the specialization",
    ) -> list[dict]:
        """
        Curate free learning resources for every node in the roadmap.

        Processes nodes one by one. If curation fails for any individual node,
        that node keeps resources=[] and processing continues — the whole batch
        never fails due to a single node error.

        Args:
            nodes:                list[dict] from RoadmapGenerator.generate_roadmap()
            specialization_name:  used for context in the prompt

        Returns:
            The same list[dict] with resources[] populated on each node.
            Original list is modified in-place AND returned.
        """
        total = len(nodes)
        logger.info(
            f"ResourceCurator › starting curation for {total} nodes "
            f"[specialization='{specialization_name}']"
        )

        success_count = 0
        empty_count   = 0

        for idx, node in enumerate(nodes):
            node_title = node.get("title", f"node_{idx}")
            logger.info(
                f"ResourceCurator › [{idx + 1}/{total}] curating '{node_title}'"
            )

            resources = self._curate_node(node, specialization_name)
            node["resources"] = resources

            if resources:
                success_count += 1
            else:
                empty_count += 1

        logger.info(
            f"ResourceCurator › done — {success_count}/{total} nodes got resources, "
            f"{empty_count} empty"
        )

        return nodes