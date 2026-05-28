from datetime import UTC, datetime

import httpx

from app.adapters.base import RawPayload, SourceAdapter
from app.core.config import Settings


class GitHubIssuesAdapter(SourceAdapter):
    def __init__(self, source: str, repo: str, settings: Settings):
        self.source = source
        self.repo = repo
        self.settings = settings

    async def fetch(self, limit: int = 25, since: datetime | None = None) -> list[RawPayload]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"

        params = {"state": "all", "per_page": limit, "sort": "updated", "direction": "desc"}
        if since:
            params["since"] = since.isoformat().replace("+00:00", "Z")

        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            response = await client.get(
                f"https://api.github.com/repos/{self.repo}/issues",
                params=params,
            )
            response.raise_for_status()
            issues = response.json()

        fetched_at = datetime.now(UTC)
        return [
            RawPayload(
                source=self.source,
                source_item_id=str(issue["id"]),
                source_url=issue.get("html_url"),
                payload_json=issue,
                fetched_at=fetched_at,
            )
            for issue in issues
            if "pull_request" not in issue
            and (since is None or self._parse_datetime(issue.get("created_at")) >= since)
        ]

    def _parse_datetime(self, value: str | None) -> datetime:
        if not value:
            return datetime.min.replace(tzinfo=UTC)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
