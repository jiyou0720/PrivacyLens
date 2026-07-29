from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_analysis_returns_evidence_without_personal_values() -> None:
    response = client.post(
        "/v1/analyze",
        json={
            "service_name": "데모 쇼핑몰",
            "policy_url": "https://example.com/privacy",
            "document_text": "회원가입을 위해 이메일과 휴대전화번호를 수집합니다. 보유 기간은 회원 탈퇴 시까지입니다. 제3자에게 제공하지 않습니다.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["collected_data"] == ["이메일", "휴대전화번호"]
    assert body["third_party_sharing"] is False
    assert len(body["evidence"]) == 2
