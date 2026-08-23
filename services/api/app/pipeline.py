import re

from .llm import LLMProvider
from .models import (
    ConsentTextAnalysis,
    ConsentTextAnalysisRequest,
    Necessity,
    RuleSeverity,
)
from .rules import evaluate_rules
from .settings import Settings
from .rag.retriever import Retriever


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value)


async def analyze_consent_text(
    request: ConsentTextAnalysisRequest,
    provider: LLMProvider,
    settings: Settings,
    retriever: Retriever,
) -> ConsentTextAnalysis:
    """
    동의서 텍스트를 분석합니다.

    1. RAG를 통해 관련 법률/가이드 문서를 검색
    2. 검색된 문서를 LLM 분석 컨텍스트로 전달
    3. LLM이 개인정보 수집 항목 및 분석 결과 추출
    4. LLM이 제시한 근거가 실제 원문에 존재하는지 검증
    5. Rule 기반 위험 요소 평가
    """

    # 1. 분석 대상 문서와 서비스 기능을 기반으로
    # 관련 법률/가이드/정책 문서 검색
    query = f"""
서비스명: {request.service_name}

서비스 기능:
{request.service_function}

분석할 개인정보 동의서:
{request.document_text}
"""

    retrieved_documents = await retriever.retrieve(
        query,
        top_k=3,
    )

    # 2. 검색된 문서를 LLM에 전달하기 위한 Context 생성
    rag_context = "\n\n".join(
        [
            f"[참고 문서 {index + 1}]\n{document}"
            for index, document in enumerate(retrieved_documents)
        ]
    )

    # 검색 결과가 없을 경우
    if not rag_context:
        rag_context = (
            "관련 참고 문서를 찾지 못했습니다. "
            "분석 대상 원문에 명시된 내용만 근거로 판단하세요."
        )

    # 3. RAG Context와 함께 LLM 분석
    extracted = await provider.extract(
        document_text=request.document_text,
        service_function=request.service_function,
        rag_context=rag_context,
    )

    # 4. LLM이 제시한 evidence_text가
    # 실제 사용자가 제공한 원문에 존재하는지 검증
    source = _normalize(request.document_text)

    unverified: list[str] = []

    for item in extracted.collected_items:
        if _normalize(item.evidence_text) not in source:
            unverified.append(item.evidence_text)

            item.confidence = 0
            item.necessity = Necessity.CONTEXT_REQUIRED
            item.reason = (
                "제시된 근거 문구를 원문에서 확인할 수 없어 "
                "사람의 검토가 필요합니다."
            )

    # 5. 기존 Rule 기반 분석
    findings = evaluate_rules(extracted)

    # 6. 사람이 검토해야 하는지 판단
    needs_review = (
        extracted.requires_human_review
        or bool(unverified)
        or any(
            finding.severity == RuleSeverity.HIGH
            for finding in findings
        )
    )

    # 7. 최종 결과 반환
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