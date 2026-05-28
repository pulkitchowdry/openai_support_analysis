import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
    inspect,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SourceType(str, enum.Enum):
    github = "github"
    community = "community"


class SourceConfig(Base):
    __tablename__ = "source_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    adapter_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer)
    last_checkpoint: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RawItem(Base):
    __tablename__ = "raw_items"
    __table_args__ = (
        UniqueConstraint("source", "source_item_id", name="uq_raw_items_source_item"),
        Index("ix_raw_items_payload_hash", "payload_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_item_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    normalized_issue: Mapped["NormalizedIssue | None"] = relationship(back_populates="raw_item")


class NormalizedIssue(Base):
    __tablename__ = "normalized_issues"
    __table_args__ = (
        Index("ix_normalized_issues_source_created", "source", "source_created_at"),
        Index("ix_normalized_issues_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_items.id"), unique=True)
    source: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    author_handle: Mapped[str | None] = mapped_column(String(255))
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(String(80))
    canonical_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    raw_item: Mapped[RawItem] = relationship(back_populates="normalized_issue")
    messages: Mapped[list["IssueMessage"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan"
    )
    extractions: Mapped[list["AiExtraction"]] = relationship(back_populates="issue")
    embeddings: Mapped[list["IssueEmbedding"]] = relationship(back_populates="issue")


class IssueMessage(Base):
    __tablename__ = "issue_messages"
    __table_args__ = (Index("ix_issue_messages_issue_position", "normalized_issue_id", "position"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_issue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("normalized_issues.id"))
    source_message_id: Mapped[str | None] = mapped_column(String(255))
    author_handle: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    issue: Mapped[NormalizedIssue] = relationship(back_populates="messages")


class AiExtraction(Base):
    __tablename__ = "ai_extractions"
    __table_args__ = (Index("ix_ai_extractions_extracted_json", "extracted_json", postgresql_using="gin"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_issue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("normalized_issues.id"))
    model_provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(40), nullable=False)
    extracted_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issue: Mapped[NormalizedIssue] = relationship(back_populates="extractions")


class IssueEmbedding(Base):
    __tablename__ = "issue_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "normalized_issue_id",
            "embedding_model",
            "embedding_input_hash",
            name="uq_issue_embedding_input",
        ),
        Index("ix_issue_embeddings_input_hash", "embedding_input_hash"),
        Index(
            "ix_issue_embeddings_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_ops={"embedding": "vector_l2_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_issue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("normalized_issues.id"))
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding_input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issue: Mapped[NormalizedIssue] = relationship(back_populates="embeddings")


class TaxonomyTerm(Base):
    __tablename__ = "taxonomy_terms"
    __table_args__ = (UniqueConstraint("term_type", "name", name="uq_taxonomy_term_type_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term_type: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IssueTaxonomyLink(Base):
    __tablename__ = "issue_taxonomy_links"
    __table_args__ = (
        UniqueConstraint("normalized_issue_id", "taxonomy_term_id", name="uq_issue_taxonomy_link"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    normalized_issue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("normalized_issues.id"))
    taxonomy_term_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("taxonomy_terms.id"))
    confidence: Mapped[float | None] = mapped_column(Float)


@event.listens_for(RawItem, "before_update")
def prevent_raw_payload_updates(mapper, connection, target: RawItem) -> None:
    state = inspect(target)
    changed_columns = [
        attr.key for attr in mapper.column_attrs if state.attrs[attr.key].history.has_changes()
    ]
    if changed_columns:
        raise ValueError("raw_items are immutable after insert")
