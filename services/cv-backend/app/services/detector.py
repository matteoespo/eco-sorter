"""YOLO-World object detection service.

Wraps the Ultralytics YOLO-World model with eco-specific class
vocabulary and per-class confidence thresholds.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path

import numpy as np
from ultralytics import YOLOWorld

from app.core.config import (
    CLASS_THRESHOLDS,
    ECO_CATEGORY_MAP,
    ECO_CLASSES,
    Settings,
    get_settings,
)
from app.models.schemas import BoundingBox, Detection

logger = logging.getLogger("eco_sorter")


class DetectorService:
    """Thread-safe YOLO-World detection service."""

    def __init__(self, settings: Settings) -> None:
        """Load the YOLO-World model and configure eco-classes.

        Attempts to load weights from the local weights directory first;
        falls back to Ultralytics auto-download if the file is not found.

        Args:
            settings: Application settings instance.
        """
        self._settings = settings
        self._lock = threading.Lock()

        local_weights = Path(settings.YOLO_WEIGHTS_DIR) / settings.YOLO_MODEL_NAME
        if local_weights.exists():
            model_path = str(local_weights)
            logger.info("Loading YOLO weights from local path: %s", model_path)
        else:
            model_path = settings.YOLO_MODEL_NAME
            logger.info(
                "Local weights not found at %s — falling back to auto-download: %s",
                local_weights,
                model_path,
            )

        self._model = YOLOWorld(model_path)
        self._model.set_classes(ECO_CLASSES)
        logger.info("YOLO-World model loaded with %d eco-classes", len(ECO_CLASSES))

    def detect(self, image: np.ndarray) -> list[Detection]:
        """Run detection on a single image.

        Args:
            image: BGR image as a NumPy array (from ``cv2.imdecode``).

        Returns:
            List of :class:`Detection` objects sorted by confidence
            (highest first), filtered by per-class thresholds.
        """
        height, width = image.shape[:2]

        with self._lock:
            # Use a very low conf so we get all candidates; we filter below
            results = self._model(image, stream=False, verbose=False, conf=0.05)

        detections: list[Detection] = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                label = ECO_CLASSES[cls_id]

                # Apply per-class threshold (fall back to default)
                threshold = CLASS_THRESHOLDS.get(
                    label, self._settings.DEFAULT_CONFIDENCE
                )
                if confidence < threshold:
                    continue

                # Normalise bounding-box coordinates to 0-1 range
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                bbox = BoundingBox(
                    x1=x1 / width,
                    y1=y1 / height,
                    x2=x2 / width,
                    y2=y2 / height,
                )

                eco_category = ECO_CATEGORY_MAP.get(label, "Unknown")

                detections.append(
                    Detection(
                        label=label,
                        confidence=round(confidence, 4),
                        bbox=bbox,
                        eco_category=eco_category,
                    )
                )

        # Sort by confidence descending
        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections


# ── Module-level singleton ───────────────────────────────────────────
_detector: DetectorService | None = None


def get_detector() -> DetectorService:
    """Return the singleton :class:`DetectorService` instance.

    Lazily initialises the service on first call.
    """
    global _detector
    if _detector is None:
        _detector = DetectorService(get_settings())
    return _detector
