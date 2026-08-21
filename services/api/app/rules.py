from .models import ExtractedConsent, RuleFinding, RuleSeverity

AMBIGUOUS_RETENTION = ("필요시", "목적 달성 시", "관계 법령에 따름", "별도 고지")
RULE_VERSION = "consent-rules-v1"


def evaluate_rules(data: ExtractedConsent) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    def missing(rule_id: str, value: object, title: str, reason: str) -> None:
        if value is None or value is False or value == [] or value == "":
            findings.append(RuleFinding(
                rule_id=rule_id, severity=RuleSeverity.WARNING, title=title, reason=reason
            ))

    missing("PURPOSE_MISSING", data.purposes, "수집·이용 목적 누락", "동의문에서 개인정보 처리 목적을 확인하지 못했습니다.")
    missing("ITEMS_MISSING", data.collected_items, "수집 항목 누락", "수집하는 개인정보 항목을 확인하지 못했습니다.")
    missing("RETENTION_MISSING", data.retention_period, "보유기간 누락", "보유·이용 기간을 확인하지 못했습니다.")
    missing("REFUSAL_RIGHT_MISSING", data.refusal_right_present, "동의 거부권 안내 누락", "동의를 거부할 권리에 대한 안내를 확인하지 못했습니다.")
    missing("REFUSAL_CONSEQUENCE_MISSING", data.refusal_consequence_present, "거부 시 불이익 안내 누락", "동의 거부 시 불이익 여부를 확인하지 못했습니다.")

    retention = (data.retention_period or "").replace(" ", "")
    if retention and any(token.replace(" ", "") in retention for token in AMBIGUOUS_RETENTION):
        findings.append(RuleFinding(
            rule_id="RETENTION_AMBIGUOUS", severity=RuleSeverity.WARNING,
            title="보유기간이 모호함", reason="종료 시점을 구체적으로 확인하기 어려워 검토가 필요합니다.",
            evidence_text=data.retention_period,
        ))

    for item in data.collected_items:
        if item.sensitive or item.unique_identifier:
            kind = "민감정보" if item.sensitive else "고유식별정보"
            findings.append(RuleFinding(
                rule_id="SPECIAL_DATA_REVIEW", severity=RuleSeverity.HIGH,
                title=f"{kind} 수집 검토 필요",
                reason=f"{item.original_name} 수집의 별도 동의 및 필요성을 사람이 검토해야 합니다.",
                evidence_text=item.evidence_text,
            ))
    return findings
