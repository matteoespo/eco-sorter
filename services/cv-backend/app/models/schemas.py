"""Pydantic schemas for API requests, responses, and internal data transfer."""
from __future__ import annotations

from pydantic import BaseModel


class BoundingBox(BaseModel):
    """Normalised bounding box with coordinates in the 0-1 range."""

    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    """A single object detection result."""

    label: str
    confidence: float
    bbox: BoundingBox
    eco_category: str


class LLMResult(BaseModel):
    """Structured response from the LLM analysis."""

    item: str
    category: str
    action_required: str
    fun_fact: str


class FrameResponse(BaseModel):
    """WebSocket response payload for a processed video frame."""

    detected: str | None = None
    confidence: float = 0.0
    detections: list[Detection] = []
    llm_result: LLMResult | None = None


class ErrorResponse(BaseModel):
    """Generic error payload."""

    error: str
