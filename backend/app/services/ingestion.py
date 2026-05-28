from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base import RawPayload
from app.adapters.registry import build_adapter
from app.core.config import Settings
from app.models import RawItem, SourceConfig, SourceType
from app.services.hashing import stable_json_hash


class IngestionService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    async def run(self, source: str, limit: int, use_checkpoint: bool = True) -> tuple[int, list[str]]:
        adapter = build_adapter(source, self.settings)
        config = self._get_or_create_source_config(source)
        since = self._fetch_since(config, use_checkpoint)
        payloads = await adapter.fetch(limit=limit, since=since)
        inserted = self.store_raw_payloads(payloads)
        self._update_checkpoint(config, payloads)
        warnings: list[str] = []
        limitation = getattr(adapter, "limitation", None)
        if limitation:
            warnings.append(limitation)
        return inserted, warnings

    def store_raw_payloads(self, payloads: list[RawPayload]) -> int:
        inserted = 0
        for payload in payloads:
            existing = self.db.execute(
                select(RawItem.id).where(
                    RawItem.source == payload.source,
                    RawItem.source_item_id == payload.source_item_id,
                )
            ).scalar_one_or_none()
            if existing:
                continue

            raw_item = RawItem(
                source=payload.source,
                source_item_id=payload.source_item_id,
                source_url=payload.source_url,
                payload_json=payload.payload_json,
                payload_hash=stable_json_hash(payload.payload_json),
                fetched_at=payload.fetched_at,
            )
            self.db.add(raw_item)
            inserted += 1
        self.db.commit()
        return inserted

    def _get_or_create_source_config(self, source: str) -> SourceConfig:
        config = self.db.execute(
            select(SourceConfig).where(SourceConfig.source == source)
        ).scalar_one_or_none()
        if config:
            return config

        config = SourceConfig(
            source=source,
            adapter_type=SourceType.community if source == "community" else SourceType.github,
            enabled=True,
            last_checkpoint=None,
        )
        self.db.add(config)
        self.db.flush()
        return config

    def _checkpoint_datetime(self, config: SourceConfig) -> datetime | None:
        checkpoint = config.last_checkpoint or {}
        updated_at = checkpoint.get("last_source_updated_at")
        if not updated_at:
            return None
        return datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))

    def _fetch_since(self, config: SourceConfig, use_checkpoint: bool) -> datetime:
        year_start = datetime(datetime.now(UTC).year, 1, 1, tzinfo=UTC)
        checkpoint = self._checkpoint_datetime(config) if use_checkpoint else None
        if checkpoint is None:
            return year_start
        return max(checkpoint, year_start)

    def _update_checkpoint(self, config: SourceConfig, payloads: list[RawPayload]) -> None:
        latest = self._latest_source_update(payloads)
        if latest is None:
            self.db.commit()
            return

        config.last_checkpoint = {"last_source_updated_at": latest.isoformat()}
        self.db.add(config)
        self.db.commit()

    def _latest_source_update(self, payloads: list[RawPayload]) -> datetime | None:
        values: list[datetime] = []
        for payload in payloads:
            updated_at = payload.payload_json.get("updated_at") or payload.payload_json.get("created_at")
            if updated_at:
                values.append(datetime.fromisoformat(str(updated_at).replace("Z", "+00:00")))
        return max(values) if values else None
