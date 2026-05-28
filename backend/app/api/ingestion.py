from fastapi import APIRouter, HTTPException

from app.api.deps import AppSettings, DbSession
from app.schemas.pipeline import FetchLatestRequest, IngestionRunRequest, OperationSummary
from app.services.embeddings import EmbeddingService
from app.services.extraction import ExtractionService
from app.services.ingestion import IngestionService
from app.services.normalization import NormalizationService

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/runs", response_model=OperationSummary)
async def run_ingestion(
    payload: IngestionRunRequest,
    db: DbSession,
    settings: AppSettings,
) -> OperationSummary:
    try:
        count, warnings = await IngestionService(db, settings).run(payload.source, payload.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationSummary(status="completed", counts={"raw_items_inserted": count}, warnings=warnings)


@router.post("/fetch-latest", response_model=OperationSummary)
async def fetch_latest(
    payload: FetchLatestRequest,
    db: DbSession,
    settings: AppSettings,
) -> OperationSummary:
    warnings: list[str] = []
    raw_inserted = 0
    ingestion = IngestionService(db, settings)

    try:
        for source in payload.sources:
            count, source_warnings = await ingestion.run(
                source, payload.ingest_limit, use_checkpoint=payload.use_checkpoint
            )
            raw_inserted += count
            warnings.extend(source_warnings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    normalized = NormalizationService(db).process_pending(payload.normalize_limit)
    extracted = ExtractionService(db, settings).process_pending(payload.extract_limit)
    embedded = EmbeddingService(db, settings).process_pending(payload.embed_limit)

    return OperationSummary(
        status="completed",
        counts={
            "raw_items_inserted": raw_inserted,
            "normalized_issues": normalized,
            "ai_extractions": extracted,
            "issue_embeddings": embedded,
        },
        warnings=warnings,
    )
