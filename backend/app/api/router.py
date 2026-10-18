"""API Router consolidating version 1 routes."""

from fastapi import APIRouter

from app.api.routes import contracts, evaluations, health, reviews, runs

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(contracts.router)
api_router.include_router(evaluations.router)
api_router.include_router(runs.router)
api_router.include_router(reviews.router)
