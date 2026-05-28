from fastapi import APIRouter

from app.api.deps import AppSettings, DbSession
from app.schemas.pipeline import OperationSummary, PipelineProcessRequest
from app.services.embeddings import EmbeddingService
from app.services.extraction import ExtractionService
from app.services.normalization import NormalizationService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/process", response_model=OperationSummary)
def process_pipeline(
    payload: PipelineProcessRequest,
    db: DbSession,
    settings: AppSettings,
) -> OperationSummary:
    normalized = NormalizationService(db).process_pending(payload.normalize_limit)
    extracted = ExtractionService(db, settings).process_pending(payload.extract_limit)
    embedded = EmbeddingService(db, settings).process_pending(payload.embed_limit)
    return OperationSummary(
        status="completed",
        counts={
            "normalized_issues": normalized,
            "ai_extractions": extracted,
            "issue_embeddings": embedded,
        },
    )
