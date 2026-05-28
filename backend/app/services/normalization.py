from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import IssueMessage, NormalizedIssue, RawItem


class NormalizationService:
    def __init__(self, db: Session):
        self.db = db

    def process_pending(self, limit: int = 50) -> int:
        raw_items = self.db.execute(
            select(RawItem)
            .outerjoin(NormalizedIssue)
            .where(NormalizedIssue.id.is_(None))
            .limit(limit)
        ).scalars()

        processed = 0
        for raw_item in raw_items:
            normalized = self._normalize(raw_item)
            if normalized is None:
                continue
            self.db.add(normalized)
            processed += 1
        self.db.commit()
        return processed

    def _normalize(self, raw_item: RawItem) -> NormalizedIssue | None:
        if raw_item.source.startswith("github_"):
            return self._normalize_github(raw_item)
        if raw_item.source == "community":
            return self._normalize_community(raw_item)
        return None

    def _normalize_github(self, raw_item: RawItem) -> NormalizedIssue:
        payload = raw_item.payload_json
        title = payload.get("title") or "Untitled GitHub issue"
        body = payload.get("body") or ""
        labels = [label.get("name") for label in payload.get("labels", []) if label.get("name")]
        normalized_text = "\n\n".join(
            part for part in [title, body, f"Labels: {', '.join(labels)}" if labels else ""] if part
        )
        return NormalizedIssue(
            raw_item=raw_item,
            source=raw_item.source,
            title=title,
            original_text=body,
            normalized_text=normalized_text,
            author_handle=(payload.get("user") or {}).get("login"),
            source_created_at=self._parse_datetime(payload.get("created_at")),
            source_updated_at=self._parse_datetime(payload.get("updated_at")),
            status=payload.get("state"),
            canonical_url=payload.get("html_url") or raw_item.source_url,
        )

    def _normalize_community(self, raw_item: RawItem) -> NormalizedIssue:
        payload = raw_item.payload_json
        title = payload.get("title") or "Untitled Community topic"
        body = payload.get("body") or payload.get("raw") or ""
        tags = [tag for tag in payload.get("tags", []) if tag]
        replies = payload.get("replies", [])
        reply_text = "\n\n".join(
            reply.get("body") or reply.get("raw") or "" for reply in replies if reply.get("body") or reply.get("raw")
        )
        metadata = []
        if tags:
            metadata.append(f"Tags: {', '.join(tags)}")
        if payload.get("has_accepted_answer"):
            metadata.append("Accepted answer: true")
        issue = NormalizedIssue(
            raw_item=raw_item,
            source=raw_item.source,
            title=title,
            original_text=body,
            normalized_text="\n\n".join(
                part for part in [title, body, reply_text, *metadata] if part
            ).strip(),
            author_handle=payload.get("username") or payload.get("author"),
            source_created_at=self._parse_datetime(payload.get("created_at")),
            source_updated_at=self._parse_datetime(payload.get("updated_at")),
            status=payload.get("status") or "open",
            canonical_url=raw_item.source_url,
        )
        for index, reply in enumerate(replies, start=1):
            issue.messages.append(
                IssueMessage(
                    source_message_id=str(reply.get("id") or index),
                    author_handle=reply.get("username") or reply.get("author"),
                    body=reply.get("body") or reply.get("raw") or "",
                    position=index,
                    source_created_at=self._parse_datetime(reply.get("created_at")),
                )
            )
        return issue

    def _parse_datetime(self, value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
