from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RawPayload:
    source: str
    source_item_id: str
    source_url: str | None
    payload_json: dict[str, Any]
    fetched_at: datetime


class SourceAdapter(ABC):
    source: str

    @abstractmethod
    async def fetch(self, limit: int = 25, since: datetime | None = None) -> list[RawPayload]:
        """Fetch raw source payloads without transforming them."""
