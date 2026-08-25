import inspect
import re

from .llm import LLMProvider
from .models import (
    ConsentTextAnalysis,
    ConsentTextAnalysisRequest,
    Necessity,
)
from .rag.retriever import Retriever
from .rag.risk_engine import (
    build_risk_summary,
    merge_findings,
)
from .rules import evaluate_rules
from .settings import Settings


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _evidence_is_supported(evidence: str, source: str) -> bool:
    normalized_evidence = _normalize(evidence)
    if normalized_evidence in source:
        return True

    # Evidence can summarize text whose words are separated by another
    # collected item (for example, "이메일을 수집합니다" in a sentence that
    # also mentions a phone number). Require every meaningful token to occur
    # in the source instead of accepting an arbitrary partial match.
    tokens = re.findall(r"[가-힣A-Za-z0-9]+", evidence)
    particles = ("으로", "에서", "까지", "부터", "을", "를", "은", "는", "이", "가", "과", "와", "에", "로", "도", "만")

    def token_is_supported(token: str) -> bool:
        token = _normalize(token)
        if token in source:
            return True
        return any(
            token.endswith(particle)
            and token[: -len(particle)] in source
            for particle in particles
        )

    return bool(tokens) and all(token_is_supported(token) for token in tokens)


async def analyze_consent_text(
    request: ConsentTextAnalysisRequest,
    provider: LLMProvider,
    settings: Settings,
    retriever: Retriever,
) -> ConsentTextAnalysis:

    # ============================================================
    # 1. RAG
    # ============================================================

    query = f"""
서비스 기능:
{request.service_function or "제공되지 않음"}

분석 대상 동의서:
{request.document_text[:6000]}
"""

    retrieved_documents = await retriever.retrieve(
        query,
        top_k=3,
    )

    rag_content = "\n\n".join(
        [
            f"[참고 문서 {index + 1}]\n{document}"
            for index, document in enumerate(
                retrieved_documents
            )
        ]
    )

    # ============================================================
    # 2. LLM 분석
    # ============================================================

    # Keep compatibility with lightweight providers used by callers/tests
    # that still implement the pre-RAG extract signature.
    extract_kwargs = {
        "document_text": request.document_text,
        "service_function": request.service_function,
    }
    parameters = inspect.signature(provider.extract).parameters
    accepts_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    if "rag_content" in parameters or accepts_kwargs:
        extract_kwargs["rag_content"] = rag_content or None

    extracted = await provider.extract(**extract_kwargs)

    # ============================================================
    # 3. Evidence 검증
    # ============================================================

    source = _normalize(
        request.document_text
    )

    unverified: list[str] = []

    for item in extracted.collected_items:

        if not _evidence_is_supported(item.evidence_text, source):

            unverified.append(
                item.evidence_text
            )

            item.confidence = 0

            item.necessity = (
                Necessity.CONTEXT_REQUIRED
            )

            item.reason = (
                "제시된 근거 문구를 원문에서 확인할 수 없어 "
                "사람의 검토가 필요합니다."
            )

    # ============================================================
    # 4. Rule Engine
    # ============================================================

    rule_findings = evaluate_rules(
        extracted
    )

    # ============================================================
    # 5. 결과 병합
    # ============================================================

    findings = merge_findings(
        rule_findings
    )

    # ============================================================
    # 6. Risk Score + Risk Level + Human Review
    # ============================================================

    risk_summary = build_risk_summary(
        findings=findings,
        extracted=extracted,
        unverified_evidence=unverified,
    )

    # ============================================================
    # 7. 최종 결과
    # ============================================================

    return ConsentTextAnalysis(
        service_name=request.service_name,
        model_name=provider.model_name,
        prompt_version=settings.prompt_version,
        rule_version=settings.rule_version,

        extracted=extracted,

        # 최종 병합 결과
        findings=findings,

        # 현재 Rule Engine 원본 결과
        rule_findings=rule_findings,

        unverified_evidence=unverified,

        risk_summary=risk_summary,

        requires_human_review=(
            risk_summary.requires_human_review
        ),
    )