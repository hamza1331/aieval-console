"""API Router consolidating version 1 routes."""

from fastapi import APIRouter

from app.api.routes import evaluations, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(evaluations.router)
