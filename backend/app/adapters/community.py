import re
from datetime import UTC, datetime
from html import unescape

import httpx

from app.adapters.base import RawPayload, SourceAdapter


class CommunityAdapter(SourceAdapter):
    source = "community"
    base_url = "https://community.openai.com"

    async def fetch(self, limit: int = 25, since: datetime | None = None) -> list[RawPayload]:
        fetched_at = datetime.now(UTC)
        payloads: list[RawPayload] = []
        page = 0

        async with httpx.AsyncClient(
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": "openai-support-intelligence/0.1"},
        ) as client:
            while len(payloads) < limit and page < 10:
                response = await client.get(f"{self.base_url}/latest.json", params={"page": page})
                response.raise_for_status()
                topics = response.json().get("topic_list", {}).get("topics", [])
                if not topics:
                    break

                for topic in topics:
                    if len(payloads) >= limit:
                        break
                    created_at = self._parse_datetime(topic.get("created_at"))
                    if since and created_at < since:
                        continue
                    if topic.get("pinned") or topic.get("archetype") != "regular":
                        continue

                    detail = await self._fetch_topic_detail(client, topic["id"])
                    merged = self._merge_topic(topic, detail)
                    payloads.append(
                        RawPayload(
                            source=self.source,
                            source_item_id=str(topic["id"]),
                            source_url=f"{self.base_url}/t/{topic.get('slug')}/{topic['id']}",
                            payload_json=merged,
                            fetched_at=fetched_at,
                        )
                    )
                page += 1

        return payloads

    async def _fetch_topic_detail(self, client: httpx.AsyncClient, topic_id: int) -> dict:
        response = await client.get(f"{self.base_url}/t/{topic_id}.json")
        response.raise_for_status()
        return response.json()

    def _merge_topic(self, topic: dict, detail: dict) -> dict:
        posts = []
        for post in detail.get("post_stream", {}).get("posts", []):
            posts.append(
                {
                    "id": post.get("id"),
                    "username": post.get("username"),
                    "created_at": post.get("created_at"),
                    "body": self._clean_html(post.get("cooked") or ""),
                    "post_number": post.get("post_number"),
                    "reply_to_post_number": post.get("reply_to_post_number"),
                }
            )

        first_post = posts[0] if posts else {}
        replies = posts[1:]
        tags = detail.get("tags") or topic.get("tags") or []
        return {
            **topic,
            "title": detail.get("title") or topic.get("title"),
            "slug": detail.get("slug") or topic.get("slug"),
            "tags": tags,
            "category_id": detail.get("category_id") or topic.get("category_id"),
            "created_at": detail.get("created_at") or topic.get("created_at"),
            "updated_at": detail.get("last_posted_at") or topic.get("last_posted_at"),
            "status": "closed" if detail.get("closed") else "open",
            "username": first_post.get("username") or topic.get("last_poster_username"),
            "body": first_post.get("body") or self._clean_html(topic.get("excerpt") or ""),
            "replies": replies,
            "accepted_answer_post_id": detail.get("accepted_answer_post_id"),
            "has_accepted_answer": detail.get("has_accepted_answer") or topic.get("has_accepted_answer"),
        }

    def _clean_html(self, value: str) -> str:
        without_tags = re.sub(r"<[^>]+>", " ", value)
        return re.sub(r"\s+", " ", unescape(without_tags)).strip()

    def _parse_datetime(self, value: str | None) -> datetime:
        if not value:
            return datetime.min.replace(tzinfo=UTC)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
