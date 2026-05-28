from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import AiExtraction, NormalizedIssue, RawItem


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def overview(self) -> dict:
        year_start = datetime(datetime.now(UTC).year, 1, 1, tzinfo=UTC)
        source_rows = self.db.execute(
            select(NormalizedIssue.source, func.count(NormalizedIssue.id))
            .where(NormalizedIssue.source_created_at >= year_start)
            .group_by(NormalizedIssue.source)
        ).all()
        extraction_rows = self._latest_extractions()
        source_range = self.db.execute(
            select(
                func.min(NormalizedIssue.source_created_at),
                func.max(NormalizedIssue.source_created_at),
            )
            .where(NormalizedIssue.source_created_at >= year_start)
        ).one()
        fetched_range = self.db.execute(
            select(func.min(RawItem.fetched_at), func.max(RawItem.fetched_at), func.count(RawItem.id))
            .join(NormalizedIssue, NormalizedIssue.raw_item_id == RawItem.id)
            .where(NormalizedIssue.source_created_at >= year_start)
        ).one()

        categories: dict[str, int] = {}
        subcategories: dict[str, int] = {}
        skills: dict[str, int] = {}
        technologies: dict[str, int] = {}
        unresolved = 0
        for extracted in extraction_rows:
            categories[extracted.get("issue_category", "uncategorized")] = (
                categories.get(extracted.get("issue_category", "uncategorized"), 0) + 1
            )
            subcategory = extracted.get("issue_subcategory") or extracted.get("problem_subtype")
            if subcategory:
                subcategories[subcategory] = subcategories.get(subcategory, 0) + 1
            for skill in extracted.get("skills_required", []):
                skills[skill] = skills.get(skill, 0) + 1
            for technology in extracted.get("technologies_involved", []):
                technologies[technology] = technologies.get(technology, 0) + 1
            if not extracted.get("was_resolved", False):
                unresolved += 1

        return {
            "sources": dict(source_rows),
            "top_issue_categories": self._top(categories),
            "top_issue_subcategories": self._top(subcategories),
            "top_skills": self._top(skills),
            "top_technologies": self._top(technologies),
            "unresolved_rate": unresolved / len(extraction_rows) if extraction_rows else 0.0,
            "raw_items_count": fetched_range[2],
            "normalized_issues_count": sum(count for _, count in source_rows),
            "source_date_range": {
                "start": source_range[0].isoformat() if source_range[0] else None,
                "end": source_range[1].isoformat() if source_range[1] else None,
            },
            "fetched_date_range": {
                "start": fetched_range[0].isoformat() if fetched_range[0] else None,
                "end": fetched_range[1].isoformat() if fetched_range[1] else None,
            },
        }

    def resolutions(self) -> dict:
        rows = self._latest_extractions()
        patterns: dict[str, int] = {}
        for extracted in rows:
            for step in extracted.get("resolution_steps", []):
                patterns[step] = patterns.get(step, 0) + 1
        return {"resolution_patterns": self._top(patterns)}

    def _latest_extractions(self) -> list[dict]:
        year_start = datetime(datetime.now(UTC).year, 1, 1, tzinfo=UTC)
        rows = self.db.execute(
            select(AiExtraction)
            .join(NormalizedIssue, NormalizedIssue.id == AiExtraction.normalized_issue_id)
            .where(NormalizedIssue.source_created_at >= year_start)
            .order_by(AiExtraction.normalized_issue_id, desc(AiExtraction.created_at))
        ).scalars()
        latest_by_issue = {}
        for row in rows:
            latest_by_issue.setdefault(row.normalized_issue_id, row.extracted_json)
        return list(latest_by_issue.values())

    def _top(self, values: dict[str, int], limit: int = 10) -> list[dict[str, int | str]]:
        return [
            {"name": name, "count": count}
            for name, count in sorted(values.items(), key=lambda item: item[1], reverse=True)[:limit]
        ]
