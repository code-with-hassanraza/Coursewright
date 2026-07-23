"""
ai_service.py — Core AI engine for Coursewright.

Responsibilities:
  - chat_with_context()  : Student chatbot with roadmap context
  - generate_json()      : Structured JSON generation for roadmap + resources

Waterfall strategy:
  Roadmap/Resources → gemini-3-flash → llama-3.3-70b-versatile → openai/gpt-oss-120b
  Chatbot           → gemini-2.5-flash → llama-3.1-8b-instant

Rules enforced:
  - chat_with_context() NEVER raises — always returns a dict
  - generate_json() retries 3x per model on invalid JSON
  - API errors skip remaining retries for that model, try next
  - logger = get_logger(__name__) used throughout
"""

import json
import re
from typing import Any

from google import genai
from google.genai import types
from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Model constants ────────────────────────────────────────────────────────────

ROADMAP_PRIMARY    = "gemini-3.5-flash"
ROADMAP_FALLBACK_1 = "llama-3.3-70b-versatile"
ROADMAP_FALLBACK_2 = "openai/gpt-oss-120b"

CHAT_PRIMARY       = "gemini-2.5-flash"
CHAT_FALLBACK      = "llama-3.1-8b-instant"

GROQ_BASE_URL      = "https://api.groq.com/openai/v1"

# ── Chatbot system prompt ──────────────────────────────────────────────────────

_CHAT_SYSTEM_PROMPT = """\
You are a helpful learning assistant for Coursewright, a specialization
platform for university students in Pakistan.

Help students understand their roadmap, answer questions about topics,
explain concepts in simple terms, and guide them when stuck.

Guidelines:
- Be warm and encouraging
- Reference roadmap topic names when relevant
- Keep answers under 300 words
- End with one actionable next step
- Never invent URLs

Student's roadmap nodes:
{formatted_nodes}"""


# ══════════════════════════════════════════════════════════════════════════════
# AIService
# ══════════════════════════════════════════════════════════════════════════════

class AIService:
    """
    Central AI client for Coursewright.

    Usage (always import inside the calling function body):
        from app.services.ai_service import AIService
        ai = AIService()
        result = ai.generate_json(user_prompt, system_prompt)
        reply  = ai.chat_with_context(message, nodes)
    """

    # ── Private: API callers ───────────────────────────────────────────────────

    def _call_gemini(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Call Google Gemini via the new google-genai SDK.
        Returns the raw text response.
        Raises any SDK/network exception to the caller.
        """
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=4096,
            ),
        )
        return response.text

    def _call_groq(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Call Groq via the OpenAI-compatible SDK (custom base_url).
        Returns the raw text response.
        Raises any SDK/network exception to the caller.
        """
        client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content

    # ── Private: Helpers ───────────────────────────────────────────────────────

    def _strip_json_fences(self, text: str) -> str:
        """
        Strip markdown code fences from model output before JSON parsing.
        Handles: ```json ... ``` and ``` ... ```
        """
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def _format_nodes(self, nodes: list[dict]) -> str:
        """
        Format roadmap node dicts into a human-readable string
        for injection into the chatbot system prompt.
        """
        if not nodes:
            return "No roadmap nodes available yet."

        lines: list[str] = []
        for node in nodes:
            order       = node.get("order", "?")
            title       = node.get("title", "Untitled")
            node_type   = node.get("type", "topic").upper()
            hours       = node.get("estimated_hours", "?")
            description = node.get("description", "").strip()
            line = f"{order}. [{node_type}] {title} (~{hours}h)"
            if description:
                line += f" — {description}"
            lines.append(line)

        return "\n".join(lines)

    def _resolve_caller(self, provider: str, model_name: str):
        """
        Return the correct API caller function for a given provider string.
        """
        if provider == "gemini":
            return self._call_gemini
        if provider == "groq":
            return self._call_groq
        raise ValueError(f"Unknown provider: {provider}")

    # ── Public: JSON generation ────────────────────────────────────────────────

    def generate_json(
        self,
        user_prompt: str,
        system_prompt: str,
    ) -> Any:
        """
        Generate and parse a JSON response from the LLM.

        Waterfall:
            1. gemini-3-flash          (primary)
            2. llama-3.3-70b-versatile (Groq fallback 1)
            3. openai/gpt-oss-120b     (Groq fallback 2)

        Per model: up to 3 retries on JSONDecodeError.
        API errors (network, auth, rate-limit) skip to next model immediately.

        Returns:
            Parsed Python object (list or dict).

        Raises:
            RuntimeError — only when ALL providers and retries are exhausted.
        """
        providers = [
            ("gemini", ROADMAP_PRIMARY),
            ("groq",   ROADMAP_FALLBACK_1),
            ("groq",   ROADMAP_FALLBACK_2),
        ]

        for provider, model_name in providers:
            call_fn = self._resolve_caller(provider, model_name)
            logger.info(f"generate_json › trying {provider}/{model_name}")

            for attempt in range(1, 4):  # 3 attempts per model
                try:
                    raw     = call_fn(model_name, system_prompt, user_prompt)
                    cleaned = self._strip_json_fences(raw)
                    parsed  = json.loads(cleaned)
                    logger.info(
                        f"generate_json › success via {provider}/{model_name} "
                        f"(attempt {attempt})"
                    )
                    return parsed

                except json.JSONDecodeError as exc:
                    logger.warning(
                        f"generate_json › invalid JSON from {provider}/{model_name} "
                        f"attempt {attempt}/3 — {exc}"
                    )
                    # Retry same model with next attempt

                except Exception as exc:
                    logger.error(
                        f"generate_json › API error from {provider}/{model_name} "
                        f"attempt {attempt}/3 — {exc}"
                    )
                    break  # Non-JSON error → skip to next provider immediately

        raise RuntimeError(
            "generate_json: all providers and retries exhausted. "
            "Verify API keys (GEMINI_API_KEY, GROQ_API_KEY) and model availability."
        )

    # ── Public: Chatbot ────────────────────────────────────────────────────────

    def chat_with_context(
        self,
        message: str,
        nodes: list[dict],
    ) -> dict:
        """
        Answer a student's question using their roadmap nodes as context.

        Waterfall:
            1. gemini-2.5-flash     (primary)
            2. llama-3.1-8b-instant (Groq fallback)

        NEVER raises an exception — always returns a valid dict.

        Returns:
            {
                "reply":  str,   # AI-generated answer
                "source": str,   # e.g. "gemini/gemini-2.5-flash"
            }
        """
        formatted_nodes = self._format_nodes(nodes)
        system_prompt   = _CHAT_SYSTEM_PROMPT.format(
            formatted_nodes=formatted_nodes
        )

        providers = [
            ("gemini", CHAT_PRIMARY),
            ("groq",   CHAT_FALLBACK),
        ]

        for provider, model_name in providers:
            call_fn = self._resolve_caller(provider, model_name)
            logger.info(f"chat_with_context › trying {provider}/{model_name}")

            try:
                reply = call_fn(model_name, system_prompt, message)
                logger.info(
                    f"chat_with_context › success via {provider}/{model_name}"
                )
                return {
                    "reply":  reply.strip(),
                    "source": f"{provider}/{model_name}",
                }

            except Exception as exc:
                logger.error(
                    f"chat_with_context › error from {provider}/{model_name}: {exc}"
                )
                # Continue to next provider

        # ── All providers failed — graceful fallback, never raise ──────────────
        logger.error("chat_with_context › all providers failed, returning static fallback")
        return {
            "reply": (
                "I'm having trouble connecting to the AI service right now. "
                "Please try again in a moment. In the meantime, your next step is "
                "to review the first topic in your roadmap and start reading there — "
                "consistent progress beats waiting for perfect conditions!"
            ),
            "source": "fallback",
        }