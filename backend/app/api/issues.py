from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.models import AiExtraction, NormalizedIssue
from app.schemas.extraction import ExtractionResult
from app.schemas.issues import IssueDetail, IssueWithExtraction

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("", response_model=list[IssueWithExtraction])
def list_issues(
    db: DbSession,
    source: str | None = None,
    status: str | None = None,
    category: str | None = None,
    skill: str | None = None,
    technology: str | None = None,
    resolved: bool | None = None,
    severity: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[IssueWithExtraction]:
    year_start = datetime(datetime.now(UTC).year, 1, 1, tzinfo=UTC)
    stmt = (
        select(NormalizedIssue)
        .where(NormalizedIssue.source_created_at >= year_start)
        .order_by(desc(NormalizedIssue.created_at))
        .limit(limit)
    )
    if source:
        stmt = stmt.where(NormalizedIssue.source == source)
    if status:
        stmt = stmt.where(NormalizedIssue.status == status)
    if any(value is not None for value in [category, skill, technology, resolved, severity]):
        stmt = stmt.join(AiExtraction).distinct(NormalizedIssue.id)
    if category:
        stmt = stmt.where(AiExtraction.extracted_json["issue_category"].astext == category)
    if skill:
        stmt = stmt.where(AiExtraction.extracted_json["skills_required"].contains([skill]))
    if technology:
        stmt = stmt.where(AiExtraction.extracted_json["technologies_involved"].contains([technology]))
    if resolved is not None:
        stmt = stmt.where(AiExtraction.extracted_json["was_resolved"].as_boolean() == resolved)
    if severity:
        stmt = stmt.where(AiExtraction.extracted_json["severity"].astext == severity)
    issues = list(db.execute(stmt).scalars())
    return [_issue_with_latest_extraction(db, issue) for issue in issues]


@router.get("/{issue_id}", response_model=IssueDetail)
def get_issue(issue_id: UUID, db: DbSession) -> IssueDetail:
    issue = db.execute(
        select(NormalizedIssue)
        .options(selectinload(NormalizedIssue.messages))
        .where(NormalizedIssue.id == issue_id)
    ).scalar_one_or_none()
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    latest = db.execute(
        select(AiExtraction)
        .where(AiExtraction.normalized_issue_id == issue.id)
        .order_by(desc(AiExtraction.created_at))
        .limit(1)
    ).scalar_one_or_none()

    detail = IssueDetail.model_validate(issue)
    if latest:
        detail.latest_extraction = ExtractionResult.model_validate(latest.extracted_json)
    return detail


def _issue_with_latest_extraction(db, issue: NormalizedIssue) -> IssueWithExtraction:
    latest = db.execute(
        select(AiExtraction)
        .where(AiExtraction.normalized_issue_id == issue.id)
        .order_by(desc(AiExtraction.created_at))
        .limit(1)
    ).scalar_one_or_none()
    response = IssueWithExtraction.model_validate(issue)
    if latest:
        response.latest_extraction = ExtractionResult.model_validate(latest.extracted_json)
    return response
