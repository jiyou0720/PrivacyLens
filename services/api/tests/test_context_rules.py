from app.models import ExtractedConsent, PersonalDataItem
from app.rag.risk_engine import merge_findings
from app.rules import evaluate_rules


def item(**updates):
    return PersonalDataItem(
        original_name="장애 여부", normalized_name="장애 여부", sensitive=True,
        reason="이력서 작성 항목", evidence_text="이력서 작성 시 장애 여부를 수집합니다.",
        **updates,
    )


def special(data):
    return [f for f in evaluate_rules(data) if f.rule_id == "SPECIAL_DATA_REVIEW"]


def test_sensitive_mention_does_not_add_risk():
    findings = special(ExtractedConsent(collected_items=[item()]))
    assert findings and findings[0].score == 0


def test_current_sensitive_data_without_confirmed_separate_consent_adds_risk():
    findings = special(ExtractedConsent(collected_items=[item(
        applies_to_current_function=True,
        scope_evidence="현재 회원가입에서 장애 여부를 수집합니다.",
    )]))
    assert findings[0].score == 20


def test_resume_only_data_is_not_signup_risk():
    assert not special(ExtractedConsent(collected_items=[item(
        collection_context="이력서", applies_to_current_function=False,
        scope_evidence="이력서 작성 시 장애 여부를 수집합니다.",
    )]))


def test_separate_consent_does_not_add_risk():
    findings = special(ExtractedConsent(collected_items=[item(
        applies_to_current_function=True, scope_evidence="현재 기능",
        separate_consent_present=True, consent_evidence="별도 동의를 받습니다.",
    )]))
    assert findings[0].score == 0


def test_explicit_concern_is_not_lost_when_merging():
    data = ExtractedConsent(collected_items=[item(), item(
        applies_to_current_function=True, scope_evidence="현재 기능",
        separate_consent_present=False, consent_evidence="별도 동의 없이 수집합니다.",
    )])
    assert merge_findings(special(data))[0].score == 35


def test_no_third_party_provision_is_not_a_missing_notice():
    findings = evaluate_rules(ExtractedConsent(third_party_provision_present=False))
    assert not any(f.rule_id == "THIRD_PARTY_PROVISION_MISSING" for f in findings)


def test_item_level_retention_is_recognized():
    findings = evaluate_rules(ExtractedConsent(collected_items=[item(
        retention_period="회원 탈퇴 시까지",
    )]))
    assert not any(f.rule_id == "RETENTION_MISSING" for f in findings)
