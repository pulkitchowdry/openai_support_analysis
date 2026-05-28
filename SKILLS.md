# SKILLS.md

## Important Note

This document contains an INITIAL SEED TAXONOMY of skills, issue categories, and troubleshooting patterns.

It is NOT a fixed or exhaustive classification system.

The system is designed to:
- evolve based on real ingested data
- discover new issue types automatically
- refine categories using clustering and AI analysis
- update skill mappings over time

# Core Support Engineering Skills

- API debugging
- HTTP troubleshooting
- retries/backoff
- rate limiting
- SSE streaming
- WebSockets
- async Python
- JSON schema validation

# Common OpenAI Issue Categories

- authentication failures
- quota issues
- streaming interruptions
- malformed tool calls
- SDK migration problems
- timeout errors
- concurrency issues

# Troubleshooting Workflow

1. Verify SDK/version
2. Analyze logs/errors
3. Identify reproducibility
4. Isolate root cause
5. Test possible solutions
6. Recommend mitigation steps

# Common Resolution Patterns

- exponential backoff
- retry jitter
- request batching
- queueing
- timeout tuning
- schema validation

# Technologies

- FastAPI
- Node.js
- Python asyncio
- SSE
- PostgreSQL
- vector search
- embeddings
- REST APIs

# Analytics Goals

- identify recurring failures
- map issues to skills
- cluster similar incidents
- detect unresolved issue patterns