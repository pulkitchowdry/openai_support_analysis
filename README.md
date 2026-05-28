# OpenAI AI Support Intelligence Platform

## Goal

Build an AI support intelligence platform focused on analyzing issues related to the OpenAI API ecosystem.

The platform should:

* identify the most frequently reported issues
* analyze troubleshooting workflows
* extract successful resolution patterns
* identify recurring operational problems
* map issues to required technical skills
* help train and prepare for AI Support Engineering roles

The initial focus is on OpenAI API developer support workflows.

---

# Primary Objectives

The application should help answer questions such as:

1. What issues occur most frequently?

   * Example: streaming failures, retries, async handling, rate limits

2. What troubleshooting steps resolve issues successfully?

   * Example: exponential backoff, request batching, retry jitter

3. What technical knowledge is repeatedly required?

   * Example: HTTP debugging, SSE streaming, async Python, JSON schema validation

4. Which issues are unresolved or repeatedly re-opened?

5. Which technologies or SDKs generate the most operational complexity?

---

# Initial MVP Scope

The MVP should focus ONLY on:

* OpenAI API ecosystem issues
* Developer troubleshooting workflows
* Issue classification and extraction

The MVP should NOT initially focus on:

* ChatGPT consumer support
* billing workflows
* enterprise account management
* autonomous agents
* full copilots

---

# Data Sources

Create adapters for the below list of sources and extract required details,

## 1. OpenAI Developer Community

https://community.openai.com

Focus areas:

* API
* Responses API
* Assistants / Agents
* Fine-tuning
* SDKs
* Realtime API

Useful for:

* production developer pain points
* troubleshooting discussions
* undocumented edge cases

---

## 2. OpenAI Codex GitHub Issues

https://github.com/openai/codex/issues

Useful for:

* agent workflows
* sandboxing
* context handling
* CLI/tooling failures
* debugging patterns

---

## 3. OpenAI Python SDK Issues

https://github.com/openai/openai-python/issues

Useful for:

* async failures
* retries
* authentication issues
* streaming bugs
* SDK migration issues

---

## 4. OpenAI Node SDK Issues

https://github.com/openai/openai-node/issues

Useful for:

* streaming
* edge runtime issues
* fetch/network behavior
* timeout handling

---

## 5. Stack Overflow

Tags:

* [openai]
* [openai-api]

Useful for:

* structured Q&A
* accepted solutions
* reproducible debugging workflows

---

# Core Issue Categories

Identify the core issue categories and group them for better analytics and identification of things to learn to excel in the support engineering role.

---

# Extracted Data Format

Unified schema for all the sources so that data can be extracted properly.

Store the raw source payload data:

```json
{
    "raw_source_payload": {}
}
```

Then normalize and extract the data in below format:

```json
{
  "source": "",
  "issue_title": "",
  "problem_type": "",
  "root_cause": "",
  "resolution_steps": [],
  "skills_required": [],
  "technologies_involved": [],
  "severity": "",
  "was_resolved": true,
  "resolution_confidence": 0.0
}
```

---

# Suggested Tech Stack

## Backend

* FastAPI
* PostgreSQL
* pgvector
* SQLAlchemy
* Database - Neon or another PostgreSQL cloud database system

## Frontend

* Next.js
* TailwindCSS

## AI Extraction

* AI Model - Gemini Flash
* structured outputs
* embeddings

---

# Architecture Goals

The system should eventually support:

* issue ingestion pipelines
* issue normalization
* semantic search
* issue clustering
* troubleshooting intelligence
* skill extraction
* analytics dashboards
* support engineering training workflows

---

# MVP Implementation

This repository now contains an MVP scaffold for the architecture in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

The app runs as a support intelligence dashboard:

* the backend stores immutable raw source payloads first
* source adapters fetch GitHub issue data from OpenAI ecosystem repositories
* normalization converts raw payloads into a unified issue schema
* deterministic extraction classifies issues, skills, technologies, severity,
  and resolution status
* deterministic embeddings support the semantic-search endpoint without
  requiring external credentials during local development
* the frontend displays overview metrics, expandable intelligence groups,
  issue explorer filters, search, and manual fetch controls

Data is not pulled automatically on every page load. Use **Fetch Latest Data**
in the dashboard to ingest and process new records. Each source stores a
checkpoint in `source_configs.last_checkpoint`; later fetches use that
checkpoint so the app requests only issues updated after the previous run.
Existing raw items are also protected by a unique `(source, source_item_id)`
constraint, so repeated fetches do not duplicate stored payloads.

If an existing database only has the earlier small sample, use **Backfill Recent
History**. That action requests the most recent 100 items per configured source
without applying the checkpoint, while still relying on database deduplication
to avoid duplicate raw payloads.

Ingestion and dashboard views are scoped to issues created in the current
calendar year. Older raw payloads are not overwritten or deleted, but analytics,
issue explorer, and search default to current-year issue records.

## Backend

Location: `backend/`

Core components:

* FastAPI app in `backend/app/main.py`
* SQLAlchemy models in `backend/app/models/domain.py`
* source adapters in `backend/app/adapters/`
* pipeline services in `backend/app/services/`
* API routes in `backend/app/api/`

Main endpoints:

* `POST /api/ingestion/runs`
* `POST /api/ingestion/fetch-latest`
* `POST /api/pipeline/process`
* `GET /api/issues`
* `GET /api/issues/{id}`
* `GET /api/analytics/overview`
* `GET /api/analytics/resolutions`
* `GET /api/search/semantic`

## Frontend

Location: `frontend/`

The Next.js dashboard reads analytics from the backend and renders:

* normalized issue count
* raw source payload count
* unresolved rate
* active sources
* source issue date range
* source payload fetch date range
* expandable groups for issue categories, skills, technologies, and sources
* issue rows with links back to GitHub/community source pages
* issue details including original text, status, extraction metadata,
  confidence, and detected resolution steps
* an issue explorer with source/status filters
* a search UI backed by `GET /api/search/semantic`

The **Fetch Latest Data** button calls `POST /api/ingestion/fetch-latest`,
which ingests configured GitHub sources and then runs normalization,
extraction, and embedding generation.

The **Backfill Recent History** button calls the same endpoint with
`use_checkpoint=false` and `ingest_limit=100`.

Resolution steps are not limited to a fixed seed list. The extractor scans issue
and reply text for actionable recommendations, stores new steps directly in the
extraction JSON, and adds category-specific remediation steps when a topic has
enough signal. These steps are also used as technology-learning signals.

## Docker local run

The Docker setup runs Postgres, FastAPI, and Next.js as separate services. The
application image does not initialize or embed Postgres.

```bash
cp docker/secrets/postgres_password.example docker/secrets/postgres_password.txt
docker compose -f docker/docker-compose.yml up --build
```

Use a locally generated password in `docker/secrets/postgres_password.txt`.
That file is ignored by git.

The frontend is available at `http://localhost:3000`, the backend at
`http://localhost:8000`, and Postgres at `localhost:5432`.

After the containers are running, open `http://localhost:3000` and click
**Fetch Latest Data**. The first run pulls the latest GitHub issues from:

* `openai/codex`
* `openai/openai-python`
* `openai/openai-node`
* OpenAI Developer Community latest topics

Subsequent runs use the stored per-source checkpoint and skip records that are
already present. If unauthenticated GitHub API limits are too low, set
`GITHUB_TOKEN` on the backend service.

By default the app fetches up to 100 current-year items per source. The GitHub
adapter filters out pull requests because GitHub returns issues and pull
requests from the same endpoint. The Community adapter reads Discourse JSON
endpoints, stores topic tags/replies, and uses relevant tags as category and
technology signals. Full historical ingestion beyond the first 100 current-year
items per source should be added as a paginated backfill job if deeper history
is required.

The Next.js server reads `API_BASE_URL` at runtime and displays overview
metrics, top issue categories, skills, technologies, and entry points for issue
exploration and search. It is intentionally not a `NEXT_PUBLIC_*` variable
because the current dashboard fetches data server-side.

The browser-side fetch button reads `NEXT_PUBLIC_API_BASE_URL`, which is set to
`http://localhost:8000` in Docker Compose so the browser can call the mapped
backend port.

## Local Database

A local pgvector-enabled PostgreSQL service is defined in
`docker/docker-compose.yml`.

Use the `postgres` service from `docker/docker-compose.yml` when only the local
database is needed.

## Environment

Copy the example files before running locally:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Do not put secrets in the Dockerfile as `ARG` or `ENV` values. For containers,
provide secrets through Docker secrets or runtime environment variables. The
backend also supports `POSTGRES_PASSWORD_FILE` for file-mounted secrets.

The MVP keeps Gemini and embedding interfaces versioned, but uses deterministic
local extraction/embedding behavior so the pipeline can be tested without
network credentials. Production Gemini and embedding calls should be added
behind the existing service boundaries.
