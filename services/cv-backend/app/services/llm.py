"""Async LLM client for eco-classification analysis.

Sends detected item labels to the LLM backend and returns
structured disposal guidance.
"""
from __future__ import annotations

import json
import logging

import httpx

from app.core.config import Settings, get_settings
from app.models.schemas import LLMResult

logger = logging.getLogger("eco_sorter")


class LLMService:
    """Async HTTP client for the Ollama-compatible LLM backend."""

    def __init__(self, settings: Settings) -> None:
        """Initialise the HTTP client.

        Args:
            settings: Application settings instance.
        """
        self._settings = settings
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.LLM_TIMEOUT),
        )

    async def analyze(self, label: str) -> LLMResult | None:
        """Ask the LLM to classify an item and provide disposal guidance.

        Args:
            label: The detected object label (e.g. ``"plastic bottle"``).

        Returns:
            A validated :class:`LLMResult` or ``None`` if the request
            fails or the response cannot be parsed.
        """
        prompt = (
            f'You are an eco-sorting assistant following European recycling rules. Classify the item "{label}" '
            "and respond ONLY with valid JSON containing these exact keys:\n"
            '- "item": the item name\n'
            '- "category": one of "Plastic & Metal", "Paper & Cardboard", "Glass", "Organic", "Residual Waste", or "Hazardous"\n'
            '- "action_required": a short instruction on how to dispose of it (e.g., "Put in the yellow plastic/metal container")\n'
            '- "fun_fact": a brief interesting fact about recycling this item\n'
            "Respond with JSON only, no extra text."
        )

        payload = {
            "model": self._settings.LLM_MODEL,
            "prompt": prompt,
            "format": "json",
            "stream": False,
        }

        try:
            response = await self._client.post(self._settings.LLM_URL, json=payload)
            response.raise_for_status()

            data = response.json()
            raw_response = data.get("response", "")

            # Parse the nested JSON string from the LLM response
            parsed = json.loads(raw_response)
            result = LLMResult(**parsed)
            logger.debug("LLM analysis for '%s': %s", label, result)
            return result

        except httpx.HTTPStatusError as exc:
            logger.error(
                "LLM HTTP error %d for '%s': %s",
                exc.response.status_code,
                label,
                exc,
            )
        except httpx.RequestError as exc:
            logger.error("LLM request failed for '%s': %s", label, exc)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.error("Failed to parse LLM response for '%s': %s", label, exc)
        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected LLM error for '%s': %s", label, exc)

        return None

    async def close(self) -> None:
        """Gracefully close the underlying HTTP client."""
        await self._client.aclose()
        logger.info("LLM HTTP client closed")


# ── Module-level singleton ───────────────────────────────────────────
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Return the singleton :class:`LLMService` instance.

    Lazily initialises the service on first call.
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(get_settings())
    return _llm_service
