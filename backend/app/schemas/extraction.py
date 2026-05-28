from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    problem_type: str = Field(default="unknown")
    problem_subtype: str = Field(default="general")
    root_cause: str | None = None
    resolution_steps: list[str] = Field(default_factory=list)
    skills_required: list[str] = Field(default_factory=list)
    technologies_involved: list[str] = Field(default_factory=list)
    severity: str = Field(default="unknown")
    was_resolved: bool = False
    resolution_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    issue_category: str = Field(default="uncategorized")
    issue_subcategory: str = Field(default="general")
    support_workflow_stage: str = Field(default="triage")
