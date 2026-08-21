import re

from .llm import LLMProvider
from .models import ConsentTextAnalysis, ConsentTextAnalysisRequest, Necessity, RuleSeverity
from .rules import evaluate_rules
from .settings import Settings


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value)


async def analyze_consent_text(
    request: ConsentTextAnalysisRequest,
    provider: LLMProvider,
    settings: Settings,
) -> ConsentTextAnalysis:
    extracted = await provider.extract(request.document_text, request.service_function)
    source = _normalize(request.document_text)
    unverified: list[str] = []

    for item in extracted.collected_items:
        if _normalize(item.evidence_text) not in source:
            unverified.append(item.evidence_text)
            item.confidence = 0
            item.necessity = Necessity.CONTEXT_REQUIRED
            item.reason = "제시된 근거 문구를 원문에서 확인할 수 없어 사람의 검토가 필요합니다."

    findings = evaluate_rules(extracted)
    needs_review = (
        extracted.requires_human_review
        or bool(unverified)
        or any(finding.severity == RuleSeverity.HIGH for finding in findings)
    )
    return ConsentTextAnalysis(
        service_name=request.service_name,
        model_name=provider.model_name,
        prompt_version=settings.prompt_version,
        rule_version=settings.rule_version,
        extracted=extracted,
        rule_findings=findings,
        unverified_evidence=unverified,
        requires_human_review=needs_review,
    )
