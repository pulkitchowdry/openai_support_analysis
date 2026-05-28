import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import IssueEmbedding, NormalizedIssue
from app.services.hashing import text_hash


class EmbeddingService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def process_pending(self, limit: int = 25) -> int:
        issues = self.db.execute(select(NormalizedIssue).limit(limit)).scalars()
        processed = 0
        for issue in issues:
            input_text = self.build_embedding_input(issue)
            input_hash = text_hash(input_text)
            existing = self.db.execute(
                select(IssueEmbedding.id).where(
                    IssueEmbedding.normalized_issue_id == issue.id,
                    IssueEmbedding.embedding_model == self.settings.embedding_model,
                    IssueEmbedding.embedding_input_hash == input_hash,
                )
            ).scalar_one_or_none()
            if existing:
                continue
            self.db.add(
                IssueEmbedding(
                    issue=issue,
                    embedding_model=self.settings.embedding_model,
                    embedding_input_hash=input_hash,
                    embedding=self._deterministic_embedding(input_text),
                )
            )
            processed += 1
        self.db.commit()
        return processed

    def build_embedding_input(self, issue: NormalizedIssue) -> str:
        return f"{issue.title}\n\n{issue.normalized_text}".strip()

    def _deterministic_embedding(self, text: str) -> list[float]:
        buckets = [0.0] * 768
        for index, byte in enumerate(text.encode("utf-8")):
            buckets[index % 768] += float(byte)
        norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
        return [value / norm for value in buckets]
