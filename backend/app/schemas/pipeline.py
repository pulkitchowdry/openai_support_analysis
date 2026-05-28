from pydantic import BaseModel, Field


class IngestionRunRequest(BaseModel):
    source: str
    limit: int = Field(default=25, ge=1, le=100)


class FetchLatestRequest(BaseModel):
    sources: list[str] = Field(
        default_factory=lambda: [
            "github_codex",
            "github_openai_python",
            "github_openai_node",
            "community",
        ]
    )
    ingest_limit: int = Field(default=100, ge=1, le=100)
    normalize_limit: int = Field(default=100, ge=1, le=500)
    extract_limit: int = Field(default=100, ge=1, le=500)
    embed_limit: int = Field(default=100, ge=1, le=500)
    use_checkpoint: bool = True


class PipelineProcessRequest(BaseModel):
    normalize_limit: int = Field(default=50, ge=1, le=500)
    extract_limit: int = Field(default=25, ge=1, le=100)
    embed_limit: int = Field(default=25, ge=1, le=100)


class OperationSummary(BaseModel):
    status: str
    counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
