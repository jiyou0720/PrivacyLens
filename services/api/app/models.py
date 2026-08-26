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
    collection_context: str = Field(default="확인 필요", max_length=200)
    applies_to_current_function: bool | None = None
    scope_evidence: str | None = Field(default=None, max_length=1000)
    separate_consent_present: bool | None = None
    consent_evidence: str | None = Field(default=None, max_length=1000)
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


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LegalBasis(BaseModel):
    law_name: str
    article: str
    title: str
    rationale: str
    source_url: str


class RuleFinding(BaseModel):
    rule_id: str

    legal_bases: list[LegalBasis] = Field(default_factory=list)

    # 기존 Rule Engine의 심각도
    severity: RuleSeverity

    # 사용자에게 보여줄 분류
    category: str

    title: str

    # 위험 발생 이유
    reason: str

    # 반드시 원문에서 가져온 근거
    evidence_text: str | None = None

    # 영향을 받는 개인정보 항목
    affected_items: list[str] = Field(default_factory=list)

    # 개선 방법
    recommendation: str

    # 제품용 위험 점수
    score: int = Field(default=0, ge=0, le=100)

    # 해당 Finding에 대한 신뢰도
    confidence: float = Field(default=1.0, ge=0, le=1)


class RiskSummary(BaseModel):
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    requires_human_review: bool
    explanation: str


class ConsentTextAnalysisRequest(BaseModel):
    service_name: str = Field(min_length=1, max_length=100)
    service_function: str | None = Field(default=None, max_length=1000)
    document_text: str = Field(min_length=20, max_length=100_000)


class ConsentTextAnalysis(BaseModel):
    service_name: str
    model_name: str
    review_model_name: str | None = None
    prompt_version: str
    rule_version: str

    extracted: ExtractedConsent

    # 최종적으로 병합된 Finding
    findings: list[RuleFinding]

    # 기존 필드도 당장은 유지
    rule_findings: list[RuleFinding]

    unverified_evidence: list[str]

    risk_summary: RiskSummary

    requires_human_review: bool
