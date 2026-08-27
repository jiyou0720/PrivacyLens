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


def test_sensitive_item_requires_review_without_automatic_high_risk() -> None:
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

    assert finding.severity == "warning"
    assert finding.score == 20

def test_findings_include_legal_bases() -> None:
    findings = evaluate_rules(ExtractedConsent())
    purpose = next(finding for finding in findings if finding.rule_id == "PURPOSE_MISSING")

    assert any(
        basis.law_name == "개인정보 보호법"
        and basis.article == "제15조 제2항"
        for basis in purpose.legal_bases
    )
    assert any(
        basis.law_name == "개인정보 보호법 시행령"
        and basis.article == "제17조"
        for basis in purpose.legal_bases
    )
    assert any(basis.source_url.endswith('/제15조') for basis in purpose.legal_bases)
    assert any(basis.source_url.endswith('/제17조') for basis in purpose.legal_bases)


def test_disclosure_only_score_is_capped() -> None:
    from app.rag.risk_engine import build_risk_summary

    extracted = ExtractedConsent()
    findings = evaluate_rules(extracted)
    summary = build_risk_summary(findings, extracted, [])

    assert summary.score == 30
    assert summary.level == "MEDIUM"

def test_service_account_id_is_not_unique_identifier() -> None:
    data = ExtractedConsent(
        purposes=["회원 관리"], retention_period="회원 탈퇴 시까지",
        refusal_right_present=True, refusal_consequence_present=True,
        collected_items=[PersonalDataItem(
            original_name="네이버 아이디(아이디 식별값 포함)",
            normalized_name="서비스 아이디", unique_identifier=True,
            necessity=Necessity.NECESSARY, reason="회원 식별",
            evidence_text="네이버 아이디를 수집합니다.",
        )],
    )
    ids = {finding.rule_id for finding in evaluate_rules(data)}
    assert "UNIQUE_IDENTIFIER_REVIEW" not in ids


def test_statutory_identifier_is_unique_identifier() -> None:
    data = ExtractedConsent(
        purposes=["본인 확인"], retention_period="확인 완료 시까지",
        refusal_right_present=True, refusal_consequence_present=True,
        collected_items=[PersonalDataItem(
            original_name="여권번호", normalized_name="여권번호",
            necessity=Necessity.CONTEXT_REQUIRED, reason="본인 확인",
            evidence_text="여권번호를 수집합니다.",
        )],
    )
    ids = {finding.rule_id for finding in evaluate_rules(data)}
    assert "UNIQUE_IDENTIFIER_REVIEW" in ids
