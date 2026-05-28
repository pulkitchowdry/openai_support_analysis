from datetime import UTC, datetime

from fastapi import APIRouter, Query
from sqlalchemy import desc, select

from app.api.deps import DbSession
from app.models import AiExtraction, NormalizedIssue
from app.schemas.extraction import ExtractionResult
from app.schemas.issues import IssueWithExtraction

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/semantic", response_model=list[IssueWithExtraction])
def semantic_search(
    db: DbSession,
    q: str = Query(min_length=2),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[IssueWithExtraction]:
    # MVP fallback: lexical search keeps the API usable until pgvector distance search is enabled.
    pattern = f"%{q}%"
    year_start = datetime(datetime.now(UTC).year, 1, 1, tzinfo=UTC)
    stmt = (
        select(NormalizedIssue)
        .where(NormalizedIssue.source_created_at >= year_start)
        .where(NormalizedIssue.normalized_text.ilike(pattern))
        .order_by(NormalizedIssue.source_created_at.desc().nullslast())
        .limit(limit)
    )
    issues = list(db.execute(stmt).scalars())
    results: list[IssueWithExtraction] = []
    for issue in issues:
        latest = db.execute(
            select(AiExtraction)
            .where(AiExtraction.normalized_issue_id == issue.id)
            .order_by(desc(AiExtraction.created_at))
            .limit(1)
        ).scalar_one_or_none()
        item = IssueWithExtraction.model_validate(issue)
        if latest:
            item.latest_extraction = ExtractionResult.model_validate(latest.extracted_json)
        results.append(item)
    return results
