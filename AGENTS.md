# Goal

Build an AI support intelligence platform for analyzing OpenAI ecosystem developer issues.

# Architecture Principles

- Prefer modular services
- Use normalized schemas
- Separate ingestion from extraction
- Keep source adapters isolated
- Store raw payloads before transformation
- Prefer async APIs

# Backend

- FastAPI
- PostgreSQL
- SQLAlchemy
- pgvector
- Database - Neon

# Frontend

- Next.js
- TailwindCSS

# AI Model

- Gemini Flash
- Compatible later with other models

# AI Extraction Rules

- Use structured JSON outputs
- Extraction must be deterministic
- Preserve original issue text
- Store extraction confidence
- Never overwrite raw source payloads

# Data Pipeline

1. Ingest raw data
2. Normalize schema
3. Run AI extraction
4. Generate embeddings
5. Store analytics metadata

# Code Standards

- Avoid monolithic files
- Keep routes thin
- Business logic belongs in services
- Use typed schemas
- Prefer dependency injection
- Secure code

# MVP Constraints

Do not build:
- autonomous agents
- browser automation
- copilots
- enterprise auth systems
- billing systems