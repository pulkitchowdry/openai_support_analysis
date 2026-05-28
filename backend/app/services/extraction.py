import re

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import AiExtraction, NormalizedIssue
from app.schemas.extraction import ExtractionResult


KEYWORD_SKILLS = {
    "rate limit": "rate limiting",
    "429": "rate limiting",
    "stream": "SSE streaming",
    "sse": "SSE streaming",
    "websocket": "WebSockets",
    "async": "async Python",
    "json schema": "JSON schema validation",
    "timeout": "HTTP troubleshooting",
    "retry": "retries/backoff",
    "auth": "API debugging",
    "api key": "API debugging",
    "tool": "tool integration debugging",
    "function calling": "function calling",
    "fine-tuning": "fine-tuning operations",
    "embedding": "vector search",
}

KEYWORD_TECHNOLOGIES = {
    "api": "OpenAI API",
    "python": "Python",
    "node": "Node.js",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "fastapi": "FastAPI",
    "postgres": "PostgreSQL",
    "pgvector": "pgvector",
    "responses": "Responses API",
    "assistant": "Assistants API",
    "assistants-api": "Assistants API",
    "realtime": "Realtime API",
    "api-realtime": "Realtime API",
    "websocket": "WebSockets",
    "sse": "SSE",
    "function calling": "Function calling",
    "function-calling": "Function calling",
    "fine-tuning": "Fine-tuning",
    "embeddings": "Embeddings API",
    "embedding": "Embeddings API",
    "whisper": "Whisper API",
    "image-generation": "Image generation",
    "gpt-4o": "GPT-4o",
    "gpt-5": "GPT-5",
    "codex": "Codex",
}

TAG_CATEGORIES = {
    "api": ("api_error_handling", "developer_platform"),
    "bug": ("api_error_handling", "reported_bug"),
    "assistants-api": ("assistants_api", "assistant_thread_or_run"),
    "assistants": ("assistants_api", "assistant_thread_or_run"),
    "realtime": ("realtime_api", "websocket_session"),
    "api-realtime": ("realtime_api", "websocket_session"),
    "function-calling": ("tool_calling", "function_schema_or_arguments"),
    "fine-tuning": ("fine_tuning", "training_or_job_configuration"),
    "embeddings": ("embeddings", "vectorization_or_retrieval"),
    "codex": ("codex_tooling", "cli_or_agent_workflow"),
    "prompt": ("prompt_engineering", "instruction_or_output_quality"),
    "account-problem": ("authentication_failure", "account_or_access"),
}


class ExtractionService:
    prompt_version = "support-extraction-v3"
    schema_version = "issue-extraction-v1"

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def process_pending(self, limit: int = 25) -> int:
        issues = self.db.execute(
            select(NormalizedIssue)
            .where(
                ~exists().where(
                    AiExtraction.normalized_issue_id == NormalizedIssue.id,
                    AiExtraction.prompt_version == self.prompt_version,
                    AiExtraction.schema_version == self.schema_version,
                )
            )
            .limit(limit)
        ).scalars()
        processed = 0
        for issue in issues:
            result = self.extract(issue)
            self.db.add(
                AiExtraction(
                    issue=issue,
                    model_provider="gemini",
                    model_name=self.settings.gemini_model,
                    prompt_version=self.prompt_version,
                    schema_version=self.schema_version,
                    extracted_json=result.model_dump(),
                    confidence=result.resolution_confidence,
                )
            )
            processed += 1
        self.db.commit()
        return processed

    def extract(self, issue: NormalizedIssue) -> ExtractionResult:
        text = issue.normalized_text.lower()
        tags = self._extract_tags(text)
        skills = sorted({skill for keyword, skill in KEYWORD_SKILLS.items() if keyword in text})
        technologies = sorted(
            {tech for keyword, tech in KEYWORD_TECHNOLOGIES.items() if keyword in text or keyword in tags}
        )
        was_resolved = bool(issue.status and issue.status.lower() in {"closed", "resolved", "solved"})
        problem_type, problem_subtype = self._problem_classification(text, tags)
        resolution_steps = self._resolution_steps(issue.normalized_text, problem_type, technologies)
        technologies = sorted(set(technologies) | self._technologies_from_steps(resolution_steps))
        confidence = 0.65 if resolution_steps or was_resolved else 0.35

        return ExtractionResult(
            problem_type=problem_type,
            problem_subtype=problem_subtype,
            root_cause=f"Likely {problem_type}",
            resolution_steps=resolution_steps,
            skills_required=skills,
            technologies_involved=technologies,
            severity="low" if problem_type == "triage_needed" else "medium",
            was_resolved=was_resolved,
            resolution_confidence=confidence,
            issue_category=problem_type,
            issue_subcategory=problem_subtype,
            support_workflow_stage="resolution" if was_resolved else "triage",
        )

    def _problem_classification(self, text: str, tags: set[str]) -> tuple[str, str]:
        for tag in sorted(tags, key=len, reverse=True):
            if tag in TAG_CATEGORIES:
                return TAG_CATEGORIES[tag]
        if "429" in text or "rate limit" in text:
            return "rate_limiting", "quota_or_throttling"
        if "stream" in text or "sse" in text:
            if "json" in text or "parse" in text:
                return "streaming_interruption", "stream_parsing"
            return "streaming_interruption", "connection_or_event_flow"
        if "websocket" in text or "realtime" in text:
            return "realtime_api", "websocket_session"
        if "timeout" in text:
            return "timeout_error", "network_or_client_timeout"
        if "auth" in text or "api key" in text:
            return "authentication_failure", "api_key_or_permission"
        if "json schema" in text or "schema" in text:
            return "schema_validation", "structured_output_validation"
        if "migration" in text:
            return "sdk_migration", "version_or_api_change"
        if "install" in text or "dependency" in text or "package" in text:
            return "environment_setup", "dependency_or_installation"
        if "sandbox" in text or "permission" in text:
            return "runtime_permissions", "sandbox_or_filesystem"
        if "memory" in text or "context" in text:
            return "context_management", "memory_or_context_window"
        if "model" in text or "response" in text or "output" in text:
            return "model_response_quality", "unexpected_or_incomplete_output"
        if "error" in text or "exception" in text or "failed" in text or "failure" in text:
            return "api_error_handling", "generic_runtime_error"
        return "triage_needed", "insufficient_signal"

    def _resolution_steps(
        self, original_text: str, problem_type: str, technologies: list[str]
    ) -> list[str]:
        text = original_text.lower()
        steps = self._extract_candidate_steps(original_text)

        if "retry" in text or problem_type == "rate_limiting":
            steps.extend(["Apply exponential backoff with jitter", "Reduce request concurrency"])
        if problem_type == "timeout_error":
            steps.extend(["Increase client timeout", "Log request latency and retry transient failures"])
        if problem_type == "schema_validation":
            steps.append("Validate JSON schema locally before sending requests")
        if problem_type == "streaming_interruption":
            steps.append("Validate streaming event parsing and handle partial or null response payloads")
        if problem_type == "authentication_failure":
            steps.append("Verify API key, organization, project, and resource permissions")
        if problem_type == "realtime_api":
            steps.append("Inspect Realtime API WebSocket session lifecycle and event ordering")
        if problem_type == "assistants_api":
            steps.append("Inspect assistant thread, run, and tool-call state transitions")
        if problem_type == "tool_calling":
            steps.append("Validate tool/function schemas and argument serialization")
        if problem_type == "fine_tuning":
            steps.append("Validate fine-tuning dataset format and job configuration")
        if problem_type == "embeddings":
            steps.append("Validate embedding model, vector dimensions, and retrieval query construction")
        if problem_type == "codex_tooling":
            steps.append("Inspect Codex CLI configuration, sandbox permissions, and MCP server setup")
        if problem_type == "prompt_engineering":
            steps.append("Tighten prompt instructions and add output validation for expected format")
        if not steps and technologies:
            steps.append(f"Investigate configuration and runtime behavior for {', '.join(technologies[:3])}")

        return self._dedupe_steps(steps)

    def _extract_tags(self, text: str) -> set[str]:
        match = re.search(r"tags:\s*([^\n]+)", text)
        if not match:
            return set()
        return {tag.strip().lower() for tag in match.group(1).split(",") if tag.strip()}

    def _extract_candidate_steps(self, text: str) -> list[str]:
        candidates: list[str] = []
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            cleaned = re.sub(r"\s+", " ", sentence).strip(" -`")
            if not 20 <= len(cleaned) <= 180:
                continue
            lowered = cleaned.lower()
            if any(
                marker in lowered
                for marker in [
                    "you can ",
                    "you should ",
                    "try ",
                    "use ",
                    "set ",
                    "add ",
                    "remove ",
                    "upgrade ",
                    "pin ",
                    "workaround",
                    "fixed by",
                    "resolved by",
                    "solution",
                ]
            ):
                candidates.append(cleaned[0].upper() + cleaned[1:])
        return candidates[:5]

    def _technologies_from_steps(self, steps: list[str]) -> set[str]:
        joined = " ".join(steps).lower()
        return {tech for keyword, tech in KEYWORD_TECHNOLOGIES.items() if keyword in joined}

    def _dedupe_steps(self, steps: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for step in steps:
            normalized = step.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(step)
        return deduped[:8]
