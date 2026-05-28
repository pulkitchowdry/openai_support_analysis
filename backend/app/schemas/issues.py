from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.extraction import ExtractionResult


class IssueMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_message_id: str | None
    author_handle: str | None
    body: str
    position: int
    source_created_at: datetime | None


class IssueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    title: str
    original_text: str
    normalized_text: str
    author_handle: str | None
    source_created_at: datetime | None
    source_updated_at: datetime | None
    status: str | None
    canonical_url: str | None


class IssueWithExtraction(IssueRead):
    latest_extraction: ExtractionResult | None = None


class IssueDetail(IssueRead):
    messages: list[IssueMessageRead] = []
    latest_extraction: ExtractionResult | None = None
    similar_issue_ids: list[UUID] = []
