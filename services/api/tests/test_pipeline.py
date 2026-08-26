import asyncio

from app.models import (
    ConsentTextAnalysisRequest,
    ExtractedConsent,
    Necessity,
    PersonalDataItem,
)
from app.pipeline import analyze_consent_text
from app.settings import Settings


class FakeProvider:
    model_name = "fake-model"

    def __init__(self, evidence: str):
        self.evidence = evidence

    async def extract(
        self,
        document_text: str,
        service_function: str | None,
    ) -> ExtractedConsent:
        return ExtractedConsent(
            purposes=["회원 가입"],
            retention_period="회원 탈퇴 시까지",
            refusal_right_present=True,
            refusal_consequence_present=True,
            collected_items=[
                PersonalDataItem(
                    original_name="이메일",
                    normalized_name="email",
                    purpose="회원 가입",
                    mandatory=True,
                    necessity=Necessity.NECESSARY,
                    reason="계정 식별",
                    evidence_text=self.evidence,
                )
            ],
        )


class FakeRetriever:
    """
    CI에서는 실제 Ollama embedding을 호출하지 않는다.
    """

    async def initialize(self) -> None:
        pass

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[str]:
        return [
            "회원가입을 위해 이메일을 수집합니다."
        ]


def analyze(evidence: str):
    request = ConsentTextAnalysisRequest(
        service_name="데모",
        document_text=(
            "회원 가입을 위해 이메일을 수집하며 "
            "회원 탈퇴 시까지 보유합니다."
        ),
    )

    return asyncio.run(
        analyze_consent_text(
            request,
            FakeProvider(evidence),
            Settings(),
            FakeRetriever(),
        )
    )


def test_pipeline_verifies_evidence_against_source() -> None:
    result = analyze("이메일을 수집")

    assert result.unverified_evidence == []
    assert result.extracted.collected_items[0].confidence == 1


def test_pipeline_marks_hallucinated_evidence_for_review() -> None:
    result = analyze("주민등록번호를 수집")

    assert result.requires_human_review is True
    assert result.extracted.collected_items[0].confidence == 0
    assert (
        result.extracted.collected_items[0].necessity
        == Necessity.CONTEXT_REQUIRED
    )
    assert result.risk_summary.score == 0
    assert "명백한 위험 요소는 확인되지 않았습니다" in result.risk_summary.explanation

def test_rag_query_is_bounded_for_long_documents() -> None:
    class RecordingRetriever(FakeRetriever):
        query_length = 0

        async def retrieve(self, query: str, top_k: int = 3) -> list[str]:
            self.query_length = len(query)
            return await super().retrieve(query, top_k)

    document = "회원 가입을 위해 이메일을 수집합니다. " * 3000
    retriever = RecordingRetriever()
    request = ConsentTextAnalysisRequest(
        service_name="긴 약관",
        document_text=document,
    )
    asyncio.run(analyze_consent_text(
        request,
        FakeProvider("이메일을 수집"),
        Settings(),
        retriever,
    ))

    assert retriever.query_length < 7000


def test_unsupported_scope_and_consent_are_not_used_for_scoring() -> None:
    class UnsupportedProvider(FakeProvider):
        async def extract(self, document_text, service_function):
            data = await super().extract(document_text, service_function)
            item = data.collected_items[0]
            item.sensitive = True
            item.applies_to_current_function = True
            item.scope_evidence = "원문에 없는 기능 범위"
            item.separate_consent_present = False
            item.consent_evidence = "동의 없이 수집한다는 존재하지 않는 문장"
            return data

    result = asyncio.run(analyze_consent_text(
        ConsentTextAnalysisRequest(service_name="검증", document_text="회원 가입을 위해 이메일을 수집하며 회원 탈퇴 시까지 보유합니다."),
        UnsupportedProvider("이메일을 수집"), Settings(), FakeRetriever(),
    ))
    item = result.extracted.collected_items[0]
    assert item.applies_to_current_function is None
    assert item.separate_consent_present is None
    assert result.requires_human_review
    assert all(f.score == 0 for f in result.findings if f.rule_id == "SPECIAL_DATA_REVIEW")
