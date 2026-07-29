from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class Confidence(StrEnum):
    CONFIRMED = "confirmed"
    NEEDS_REVIEW = "needs_review"


class Evidence(BaseModel):
    quote: str = Field(min_length=1, max_length=500)
    location: str | None = None
    confidence: Confidence


class AnalyzeRequest(BaseModel):
    service_name: str = Field(min_length=1, max_length=100)
    policy_url: HttpUrl
    document_text: str = Field(min_length=20, max_length=100_000)


class PolicyAnalysis(BaseModel):
    service_name: str
    policy_url: HttpUrl
    collected_data: list[str]
    purposes: list[str]
    retention_periods: list[str]
    third_party_sharing: bool | None
    outsourcing: list[str]
    user_rights: list[str]
    evidence: list[Evidence]
    analysis_date: date
