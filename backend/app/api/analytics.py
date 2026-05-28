from fastapi import APIRouter

from app.api.deps import DbSession
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview(db: DbSession) -> dict:
    return AnalyticsService(db).overview()


@router.get("/resolutions")
def resolutions(db: DbSession) -> dict:
    return AnalyticsService(db).resolutions()
