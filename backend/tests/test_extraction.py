from types import SimpleNamespace

from app.schemas.extraction import ExtractionResult
from app.services.extraction import ExtractionService


def test_extraction_detects_rate_limits_without_network() -> None:
    issue = SimpleNamespace(
        normalized_text="Python SDK gets 429 rate limit errors and needs retry handling",
        status="open",
    )
    service = ExtractionService(db=None, settings=SimpleNamespace(gemini_model="gemini-flash-test"))

    result = service.extract(issue)

    assert isinstance(result, ExtractionResult)
    assert result.problem_type == "rate_limiting"
    assert "rate limiting" in result.skills_required
    assert result.resolution_steps
