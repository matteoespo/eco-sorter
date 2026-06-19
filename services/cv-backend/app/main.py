"""Eco-Sorter CV Backend — FastAPI application entrypoint.

Initialises logging, the YOLO detector, and the LLM client during
startup, then exposes the WebSocket API and a health-check endpoint.
"""
from __future__ import annotations

import contextlib
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.detector import get_detector
from app.services.llm import get_llm_service

logger: logging.Logger | None = None


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown hooks."""
    global logger

    settings = get_settings()

    # ── Startup ──────────────────────────────────────────────────────
    logger = setup_logging(settings.LOG_LEVEL)

    logger.info("═" * 50)
    logger.info("Eco-Sorter CV Backend v2.0.0 starting")
    logger.info("═" * 50)
    logger.info("LLM URL      : %s", settings.LLM_URL)
    logger.info("LLM Model    : %s", settings.LLM_MODEL)
    logger.info("LLM Timeout  : %.1fs", settings.LLM_TIMEOUT)
    logger.info("YOLO Model   : %s", settings.YOLO_MODEL_NAME)
    logger.info("Weights Dir  : %s", settings.YOLO_WEIGHTS_DIR)
    logger.info("Default Conf : %.2f", settings.DEFAULT_CONFIDENCE)
    logger.info("Debounce     : %.1fs", settings.DEBOUNCE_SECONDS)
    logger.info("Log Level    : %s", settings.LOG_LEVEL)

    # Eagerly initialise the detector so model loading happens at startup
    get_detector()
    logger.info("YOLO-World model loaded and ready")

    # Eagerly initialise the LLM HTTP client
    get_llm_service()
    logger.info("LLM client ready")

    logger.info("═" * 50)
    logger.info("Startup complete — accepting connections")
    logger.info("═" * 50)

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    logger.info("Shutting down Eco-Sorter CV Backend …")
    await get_llm_service().close()
    logger.info("Shutdown complete")


# ── Application instance ─────────────────────────────────────────────
app = FastAPI(
    title="Eco-Sorter CV Backend",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────
app.include_router(api_router)


# ── Health check ─────────────────────────────────────────────────────
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe for orchestration / load balancers."""
    return {"status": "healthy", "version": "2.0.0"}
