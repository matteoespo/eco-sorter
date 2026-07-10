"""Application settings and environment configuration.

Loads configuration from environment variables with sensible defaults
for the Eco-Sorter CV Backend service.
"""
from __future__ import annotations

import functools

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Backend
    LLM_URL: str = "http://llm-backend:11434/api/generate"
    LLM_MODEL: str = "gemma:2b"
    LLM_TIMEOUT: float = 15.0

    # YOLO Model
    YOLO_MODEL_NAME: str = "yolov8x-world.pt"
    YOLO_WEIGHTS_DIR: str = "/app/weights"

    # Detection Tuning
    DEFAULT_CONFIDENCE: float = 0.20
    DEBOUNCE_SECONDS: float = 1.5

    # Logging
    LOG_LEVEL: str = "INFO"


# Optimised YOLO-World class vocabulary
ECO_CLASSES: list[str] = [
    "plastic bottle",
    "glass bottle",
    "aluminum can",
    "cardboard box",
    "paper sheet",
    "plastic bag",
    "plastic container",
    "glass jar",
    "carton",
    "aerosol can",
    "electronic device",
    "power cable",
    "battery",
    "light bulb",
    "fruit or vegetable",
    "food scraps",
    "bread",
    "coffee cup",
    "clothing item",
    "shoe",
    "toy",
    "book",
    "bag",
    "cup or mug",
    "plate or bowl",
    "cutlery",
    "water bottle",
    "napkin or tissue",
    "cleaning product",
    "medicine bottle",
    "paint can",
]

# Per-class confidence thresholds (override DEFAULT_CONFIDENCE)
CLASS_THRESHOLDS: dict[str, float] = {
    "plastic bottle": 0.15,
    "aluminum can": 0.15,
    "glass bottle": 0.18,
    "cardboard box": 0.15,
    "plastic bag": 0.20,
    "electronic device": 0.25,
    "battery": 0.25,
    "fruit or vegetable": 0.22,
    "food scraps": 0.25,
    "clothing item": 0.25,
}

# Eco-category lookup (class name → disposal category)
# Built by inverting a category→classes mapping for O(1) lookups.
_CATEGORY_TO_CLASSES: dict[str, list[str]] = {
    "Plastic & Metal": [
        "plastic bottle",
        "aluminum can",
        "plastic bag",
        "plastic container",
        "carton",
        "water bottle",
    ],
    "Paper & Cardboard": [
        "cardboard box",
        "paper sheet",
        "book",
    ],
    "Glass": [
        "glass bottle",
        "glass jar",
    ],
    "Organic": [
        "fruit or vegetable",
        "food scraps",
        "bread",
    ],
    "Residual Waste": [
        "napkin or tissue",
        "toy",
        "shoe",
        "clothing item",
        "bag",
        "cup or mug",
        "plate or bowl",
        "cutlery",
        "coffee cup",
    ],
    "Hazardous": [
        "aerosol can",
        "electronic device",
        "power cable",
        "battery",
        "light bulb",
        "cleaning product",
        "medicine bottle",
        "paint can",
    ],
}

ECO_CATEGORY_MAP: dict[str, str] = {
    cls: category
    for category, classes in _CATEGORY_TO_CLASSES.items()
    for cls in classes
}


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
