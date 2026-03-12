from pydantic import BaseModel
from typing import Dict, List

class ProposalRequest(BaseModel):
    project_title: str
    industry: str
    duration_months: int
    expected_users: int
    tech_stack: List[str]

class ProposalResponse(BaseModel):
    executive_summary: str
    technical_approach: str
    timeline: str
    estimated_cost: Dict[str, float]
    risk_assessment: str