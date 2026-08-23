from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class Confidence(StrEnum):
    CONFIRMED = "confirmed"
    INFERRED = "inferred"
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


class Necessity(StrEnum):
    NECESSARY = "necessary"
    CONTEXT_REQUIRED = "context_required"
    POSSIBLY_EXCESSIVE = "possibly_excessive"
    HIGH_RISK = "high_risk"


class PersonalDataItem(BaseModel):
    original_name: str = Field(min_length=1, max_length=200)
    normalized_name: str = Field(min_length=1, max_length=100)
    purpose: str | None = Field(default=None, max_length=500)
    mandatory: bool | None = None
    sensitive: bool = False
    unique_identifier: bool = False
    retention_period: str | None = Field(default=None, max_length=500)
    necessity: Necessity = Necessity.CONTEXT_REQUIRED
    reason: str = Field(min_length=1, max_length=1000)
    evidence_text: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(default=1.0, ge=0, le=1)


class ExtractedConsent(BaseModel):
    model_config = {"extra": "forbid"}

    controller: str | None = Field(default=None, max_length=300)
    purposes: list[str] = Field(default_factory=list)
    collected_items: list[PersonalDataItem] = Field(default_factory=list)
    retention_period: str | None = Field(default=None, max_length=500)
    refusal_right_present: bool | None = None
    refusal_consequence_present: bool | None = None
    third_party_provision_present: bool | None = None
    overseas_transfer_present: bool | None = None
    requires_human_review: bool = False


class RuleSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"


class RuleFinding(BaseModel):
    rule_id: str
    severity: RuleSeverity
    title: str
    reason: str
    evidence_text: str | None = None


class ConsentTextAnalysisRequest(BaseModel):
    service_name: str = Field(min_length=1, max_length=100)
    service_function: str | None = Field(default=None, max_length=1000)
    document_text: str = Field(min_length=20, max_length=100_000)


class ConsentTextAnalysis(BaseModel):
    service_name: str
    model_name: str
    prompt_version: str
    rule_version: str
    extracted: ExtractedConsent
    rule_findings: list[RuleFinding]
    unverified_evidence: list[str]
    requires_human_review: bool
