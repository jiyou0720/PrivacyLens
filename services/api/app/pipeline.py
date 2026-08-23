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
{request.document_text}
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

    extracted = await provider.extract(
        document_text=request.document_text,
        service_function=request.service_function,
        rag_content=rag_content or None,
    )

    # ============================================================
    # 3. Evidence 검증
    # ============================================================

    source = _normalize(
        request.document_text
    )

    unverified: list[str] = []

    for item in extracted.collected_items:

        evidence = _normalize(
            item.evidence_text
        )

        if evidence not in source:

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