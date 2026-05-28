# MVP Architecture

## Summary

The platform is a modular AI support intelligence system for OpenAI API ecosystem issues. It ingests raw discussions from GitHub, Reddit, and accessible OpenAI Community sources, preserves immutable raw payloads, normalizes them into a unified issue model, runs deterministic Gemini-compatible extraction, creates pgvector embeddings, and exposes analytics for recurring issues, resolutions, skills, technologies, and unresolved patterns.

The MVP favors traceability over automation breadth. Stack Overflow, advanced clustering, human review, and scheduled jobs are deferred to later phases.

## System Shape

- Backend: FastAPI, SQLAlchemy, PostgreSQL/Neon, pgvector.
- Frontend: Next.js and TailwindCSS dashboard.
- AI: Gemini Flash-compatible extraction interface with versioned prompts and schemas.
- Pipeline: raw ingestion -> normalization -> AI extraction -> embeddings -> analytics.

Adapters are isolated by source. Routes are thin and call services. Services own business logic. Raw payloads are never overwritten by normalization, extraction, or embedding stages.

## Ingestion

MVP sources:

- GitHub: `openai/codex`, `openai/openai-python`, `openai/openai-node`.
- Reddit: `r/OpenAIDev`, `r/OpenAI`.
- OpenAI Community: adapter stubbed as limited until a stable non-browser public access path is configured.

Each adapter returns raw payload objects with source, source item ID, canonical URL, payload JSON, and fetch time. The ingestion service stores them in `raw_items` and deduplicates by `source` plus `source_item_id`.

## Normalization

The normalization service converts raw source shapes into:

- `normalized_issues`
- `issue_messages`

The normalized issue preserves original source text separately from normalized text. Reddit normalization applies basic developer-topic filtering and excludes obvious consumer support, billing, refund, and account-management posts.

## AI Extraction

The extraction service stores every extraction run in `ai_extractions` with:

- model provider and model name
- prompt version
- schema version
- structured JSON output
- confidence

The MVP implementation is deterministic and schema-compatible. It can be replaced with Gemini Flash API calls behind the same service boundary without changing downstream tables or routes.

Extraction fields:

- `problem_type`
- `root_cause`
- `resolution_steps`
- `skills_required`
- `technologies_involved`
- `severity`
- `was_resolved`
- `resolution_confidence`
- `issue_category`
- `support_workflow_stage`

## Embeddings

Embeddings are stored in `issue_embeddings` with provider/model metadata and an input hash. The MVP uses a deterministic local vector placeholder to keep the pipeline testable without network access. Production should replace that implementation with the selected embedding model while preserving the same table contract.

The embedding input is normalized title plus normalized issue text. Unchanged input hashes are skipped to avoid duplicate embeddings.

## Database Schema

Core tables:

- `source_configs`: source metadata, adapter type, enabled flag, rate limits, checkpoint.
- `raw_items`: immutable source payloads, source IDs, payload hashes, fetch/ingestion times.
- `normalized_issues`: unified issue records with original and normalized text.
- `issue_messages`: normalized comments, replies, and thread messages.
- `ai_extractions`: versioned structured extraction results.
- `issue_embeddings`: pgvector vectors with embedding model and input hash.
- `taxonomy_terms`: categories, skills, technologies, and resolution patterns.
- `issue_taxonomy_links`: issue-to-taxonomy associations.

Important indexes:

- Unique raw item key on `source` and `source_item_id`.
- Issue filters on source, created time, and status.
- GIN index for extraction JSON.
- pgvector index for embedding search.
- Hash indexes for idempotency.

## API Surface

- `POST /api/ingestion/runs`: trigger ingestion for one source.
- `POST /api/pipeline/process`: normalize, extract, and embed pending records.
- `GET /api/issues`: list/filter normalized issues.
- `GET /api/issues/{id}`: issue detail, messages, latest extraction, and similar issue placeholder.
- `GET /api/analytics/overview`: source counts, issue categories, skills, technologies, unresolved rate.
- `GET /api/analytics/resolutions`: common resolution steps.
- `GET /api/search/semantic`: MVP lexical fallback for the future semantic-search route.

## Frontend

The Next.js app provides a dashboard-first MVP:

- overview metrics
- top issue categories
- top skills
- top technologies
- issue explorer entry point
- similar issue search entry point

The frontend reads `NEXT_PUBLIC_API_BASE_URL` and degrades to empty dashboard states when the backend has no data yet.

## Risks and Missing Components

- OpenAI Community may not expose a stable public API path; browser automation remains out of scope.
- Reddit can be noisy and needs stronger developer-topic filtering as data accumulates.
- Gemini extraction should be evaluated against fixture sets before being trusted for analytics.
- Raw payload growth needs retention and archival policy.
- API rate limits require backoff, checkpoints, and retry persistence in v1.
- The MVP semantic endpoint is currently lexical fallback; pgvector distance ranking should replace it after real embeddings are configured.
- No production auth is included. Deployment should be private/admin-only until access control is designed.

## Phased Implementation

### MVP

- Create FastAPI backend, SQLAlchemy schema, and service boundaries.
- Implement GitHub and Reddit raw ingestion.
- Keep Community adapter limited without browser automation.
- Normalize source payloads into unified issues.
- Store deterministic structured extraction outputs.
- Generate versioned embeddings and analytics summaries.
- Provide dashboard shell and API endpoints.

### v1

- Add Stack Overflow ingestion for `[openai]` and `[openai-api]`.
- Replace local extraction and embedding placeholders with production Gemini and embedding calls.
- Add scheduled ingestion, retries, checkpoint updates, and backoff.
- Improve taxonomy management and extraction evaluation.
- Add pgvector distance search and unresolved issue clustering.

### v2

- Add trend detection and recurring incident reporting.
- Add human review for low-confidence extractions.
- Add support-engineering training workflows.
- Add export/report generation.
- Add multi-provider model compatibility.

## Test Strategy

- Unit-test adapter payload handling with fixtures.
- Unit-test normalization per source.
- Validate extraction output against the typed schema.
- Test ingestion idempotency.
- Test that raw payloads are not overwritten.
- Test embedding input hashes skip unchanged records.
- Test analytics output from seeded records.
- Run an end-to-end pipeline fixture: raw item -> normalized issue -> extraction -> embedding -> analytics.
