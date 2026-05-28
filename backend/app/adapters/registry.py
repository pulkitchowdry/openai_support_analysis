from app.adapters.base import SourceAdapter
from app.adapters.community import CommunityAdapter
from app.adapters.github import GitHubIssuesAdapter
from app.core.config import Settings


def build_adapter(source: str, settings: Settings) -> SourceAdapter:
    adapters: dict[str, SourceAdapter] = {
        "github_codex": GitHubIssuesAdapter("github_codex", "openai/codex", settings),
        "github_openai_python": GitHubIssuesAdapter(
            "github_openai_python", "openai/openai-python", settings
        ),
        "github_openai_node": GitHubIssuesAdapter("github_openai_node", "openai/openai-node", settings),
        "community": CommunityAdapter(),
    }
    try:
        return adapters[source]
    except KeyError as exc:
        raise ValueError(f"Unknown source: {source}") from exc
