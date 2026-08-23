import asyncio

from app.models import ConsentTextAnalysisRequest, ExtractedConsent, Necessity, PersonalDataItem
from app.pipeline import analyze_consent_text
from app.settings import Settings


class FakeProvider:
    model_name = "fake-model"

    def __init__(self, evidence: str):
        self.evidence = evidence

    async def extract(self, document_text: str, service_function: str | None) -> ExtractedConsent:
        return ExtractedConsent(
            purposes=["회원 가입"],
            retention_period="회원 탈퇴 시까지",
            refusal_right_present=True,
            refusal_consequence_present=True,
            collected_items=[PersonalDataItem(
                original_name="이메일", normalized_name="email", purpose="회원 가입",
                mandatory=True, necessity=Necessity.NECESSARY, reason="계정 식별",
                evidence_text=self.evidence,
            )],
        )


def analyze(evidence: str):
    request = ConsentTextAnalysisRequest(
        service_name="데모", document_text="회원 가입을 위해 이메일을 수집하며 회원 탈퇴 시까지 보유합니다."
    )
    return asyncio.run(analyze_consent_text(request, FakeProvider(evidence), Settings()))


def test_pipeline_verifies_evidence_against_source() -> None:
    result = analyze("이메일을 수집")
    assert result.unverified_evidence == []
    assert result.extracted.collected_items[0].confidence == 1


def test_pipeline_marks_hallucinated_evidence_for_review() -> None:
    result = analyze("주민등록번호를 수집")
    assert result.requires_human_review is True
    assert result.extracted.collected_items[0].confidence == 0
    assert result.extracted.collected_items[0].necessity == Necessity.CONTEXT_REQUIRED
