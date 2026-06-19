"""Master API router that aggregates all endpoint routers."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints.process import router

api_router = APIRouter()
api_router.include_router(router)
