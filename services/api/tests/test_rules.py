from app.models import (
    ExtractedConsent,
    Necessity,
    PersonalDataItem,
)
from app.rules import evaluate_rules


def test_rules_report_missing_required_notices() -> None:
    ids = {
        finding.rule_id
        for finding in evaluate_rules(ExtractedConsent())
    }

    assert {
        "PURPOSE_MISSING",
        "ITEMS_MISSING",
        "RETENTION_MISSING",
    } <= ids

    assert {
        "REFUSAL_RIGHT_MISSING",
        "REFUSAL_CONSEQUENCE_MISSING",
    } <= ids


def test_sensitive_item_requires_high_review() -> None:
    data = ExtractedConsent(
        purposes=["본인 확인"],
        retention_period="회원 탈퇴 시까지",
        refusal_right_present=True,
        refusal_consequence_present=True,
        collected_items=[
            PersonalDataItem(
                original_name="건강정보",
                normalized_name="건강정보",
                purpose="맞춤 서비스",
                sensitive=True,
                necessity=Necessity.CONTEXT_REQUIRED,
                reason="서비스 맥락 확인 필요",
                evidence_text="건강정보를 수집합니다.",
            )
        ],
    )

    findings = evaluate_rules(data)

    finding = next(
        finding
        for finding in findings
        if finding.rule_id == "SPECIAL_DATA_REVIEW"
    )

    assert finding.severity == "high"