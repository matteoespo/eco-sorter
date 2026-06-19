"""WebSocket endpoint for real-time video frame processing.

Receives base64-encoded frames, runs YOLO-World detection,
applies debounce logic, and optionally queries the LLM for
disposal guidance.
"""
from __future__ import annotations

import base64
import logging
import time

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.models.schemas import ErrorResponse, FrameResponse, LLMResult
from app.services.detector import get_detector
from app.services.llm import get_llm_service

logger = logging.getLogger("eco_sorter")

router = APIRouter()


class DetectionState:
    """Per-connection state for debounce and LLM caching."""

    def __init__(self) -> None:
        self.current_label: str | None = None
        self.first_detected_time: float = 0.0
        self.last_llm_response: LLMResult | None = None


@router.websocket("/process-frame")
async def process_frame(websocket: WebSocket) -> None:
    """Accept a WebSocket connection and process video frames in real time.

    Protocol:
        1. Client sends a base64-encoded image (optionally as a data URI).
        2. Server replies with a :class:`FrameResponse` JSON payload.
    """
    await websocket.accept()

    state = DetectionState()
    detector = get_detector()
    llm_service = get_llm_service()
    settings = get_settings()

    logger.info("WebSocket client connected")

    try:
        while True:
            # ── Receive frame ────────────────────────────────────────
            raw_data: str = await websocket.receive_text()

            # Strip data URI prefix if present (e.g. "data:image/jpeg;base64,...")
            if "," in raw_data:
                raw_data = raw_data.split(",", 1)[1]

            # ── Decode image ─────────────────────────────────────────
            try:
                img_bytes = base64.b64decode(raw_data)
                np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Image decode failed: %s", exc)
                error_resp = ErrorResponse(error="Invalid image data")
                await websocket.send_text(error_resp.model_dump_json())
                continue

            if img is None:
                error_resp = ErrorResponse(error="Image decode returned None")
                await websocket.send_text(error_resp.model_dump_json())
                continue

            # ── Run detection ────────────────────────────────────────
            detections = detector.detect(img)

            # Best detection is first (list is sorted by confidence)
            best = detections[0] if detections else None

            # ── Debounce logic ───────────────────────────────────────
            llm_result: LLMResult | None = None

            if best is not None:
                label = best.label

                if label != state.current_label:
                    # New object detected — reset state
                    state.current_label = label
                    state.first_detected_time = time.time()
                    state.last_llm_response = None
                else:
                    # Same object — check debounce timer
                    elapsed = time.time() - state.first_detected_time
                    if elapsed > settings.DEBOUNCE_SECONDS and state.last_llm_response is None:
                        state.last_llm_response = await llm_service.analyze(label)

                llm_result = state.last_llm_response
            else:
                # Nothing detected — clear state
                state.current_label = None

            # ── Build and send response ──────────────────────────────
            response = FrameResponse(
                detected=best.label if best else None,
                confidence=round(best.confidence, 4) if best else 0.0,
                detections=detections,
                llm_result=llm_result,
            )

            await websocket.send_text(response.model_dump_json())

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
