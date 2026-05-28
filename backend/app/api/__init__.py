from fastapi import APIRouter

from app.api import analytics, ingestion, issues, pipeline, search

api_router = APIRouter(prefix="/api")
api_router.include_router(ingestion.router)
api_router.include_router(pipeline.router)
api_router.include_router(issues.router)
api_router.include_router(analytics.router)
api_router.include_router(search.router)
