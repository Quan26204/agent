
from typing import Any, List, Dict
from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    request: str = Field(min_length=3, max_length=5000)
    conversation_id: int | None = None


class ProposedJob(BaseModel):
    job_key: str = Field(min_length=1, max_length=80)
    job_type: str
    target_agent: str
    description: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    schedule: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)


class PlanProposal(BaseModel):
    title: str
    summary: str
    needs_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)
    jobs: List[ProposedJob] = Field(default_factory=list, max_length=20)
