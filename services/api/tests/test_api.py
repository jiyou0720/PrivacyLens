from fastapi.testclient import TestClient

from app.main import app, get_llm_provider
from app.models import ExtractedConsent, Necessity, PersonalDataItem


client = TestClient(app)


class FakeProvider:
    model_name = "fake-model"

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
                    evidence_text="이메일과 휴대전화번호를 수집",
                )
            ],
        )


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analysis_returns_evidence_without_personal_values() -> None:
    response = client.post(
        "/v1/analyze",
        json={
            "service_name": "데모 쇼핑몰",
            "policy_url": "https://example.com/privacy",
            "document_text": (
                "회원가입을 위해 이메일과 휴대전화번호를 수집합니다. "
                "보유 기간은 회원 탈퇴 시까지입니다. "
                "제3자에게 제공하지 않습니다."
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["collected_data"] == [
        "이메일",
        "휴대전화번호",
    ]

    assert body["third_party_sharing"] is False
    assert len(body["evidence"]) == 2


def test_structured_analysis_endpoint() -> None:
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()

    try:
        response = client.post(
            "/api/v1/analyses/text",
            json={
                "service_name": "데모 쇼핑몰",
                "service_function": "회원 가입",
                "document_text": (
                    "회원가입을 위해 이메일과 휴대전화번호를 수집합니다. "
                    "보유 기간은 회원 탈퇴 시까지입니다."
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["model_name"] == "fake-model"
    assert body["unverified_evidence"] == []
    assert "risk_score" not in body