from .models import ExtractedConsent, RuleFinding, RuleSeverity


AMBIGUOUS_RETENTION = (
    "필요시",
    "목적 달성 시",
    "관계 법령에 따름",
    "별도 고지",
)

RULE_VERSION = "consent-rules-v2"


def evaluate_rules(data: ExtractedConsent) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    def add_finding(
        *,
        rule_id: str,
        severity: RuleSeverity,
        category: str,
        title: str,
        reason: str,
        recommendation: str,
        score: int,
        evidence_text: str | None = None,
        affected_items: list[str] | None = None,
        confidence: float = 1.0,
    ) -> None:
        findings.append(
            RuleFinding(
                rule_id=rule_id,
                severity=severity,
                category=category,
                title=title,
                reason=reason,
                evidence_text=evidence_text,
                affected_items=affected_items or [],
                recommendation=recommendation,
                score=score,
                confidence=confidence,
            )
        )

    # ============================================================
    # 1. 문서 구조 적정성
    # ============================================================

    if not data.purposes:
        add_finding(
            rule_id="PURPOSE_MISSING",
            severity=RuleSeverity.WARNING,
            category="문서 구조",
            title="수집·이용 목적 누락",
            reason="동의문에서 개인정보 처리 목적을 확인하지 못했습니다.",
            recommendation="개인정보를 수집·이용하는 구체적인 목적을 명시하세요.",
            score=10,
        )

    if not data.collected_items:
        add_finding(
            rule_id="ITEMS_MISSING",
            severity=RuleSeverity.WARNING,
            category="문서 구조",
            title="수집 항목 누락",
            reason="수집하는 개인정보 항목을 확인하지 못했습니다.",
            recommendation="수집하는 개인정보 항목을 구체적으로 명시하세요.",
            score=0,
        )

    if not data.retention_period:
        add_finding(
            rule_id="RETENTION_MISSING",
            severity=RuleSeverity.WARNING,
            category="보유기간",
            title="보유기간 누락",
            reason="보유·이용 기간을 확인하지 못했습니다.",
            recommendation="개인정보의 보유 및 이용기간을 구체적으로 명시하세요.",
            score=20,
        )

    if data.refusal_right_present is not True:
        add_finding(
            rule_id="REFUSAL_RIGHT_MISSING",
            severity=RuleSeverity.WARNING,
            category="동의권",
            title="동의 거부권 안내 누락",
            reason="동의를 거부할 권리에 대한 안내를 확인하지 못했습니다.",
            recommendation="동의 거부 권리와 관련된 안내를 명확하게 제공하세요.",
            score=15,
        )

    if data.refusal_consequence_present is not True:
        add_finding(
            rule_id="REFUSAL_CONSEQUENCE_MISSING",
            severity=RuleSeverity.WARNING,
            category="동의권",
            title="거부 시 불이익 안내 누락",
            reason="동의 거부 시 발생하는 불이익에 대한 안내를 확인하지 못했습니다.",
            recommendation="동의 거부 시 서비스 이용에 미치는 영향을 명확하게 안내하세요.",
            score=15,
        )

    # ============================================================
    # 2. 보유기간
    # ============================================================

    retention = (data.retention_period or "").replace(" ", "")

    if retention and any(
        token.replace(" ", "") in retention
        for token in AMBIGUOUS_RETENTION
    ):
        add_finding(
            rule_id="RETENTION_AMBIGUOUS",
            severity=RuleSeverity.WARNING,
            category="보유기간",
            title="보유기간이 모호함",
            reason="개인정보의 보유 종료 시점을 구체적으로 확인하기 어렵습니다.",
            recommendation="개인정보의 보유기간 또는 파기 시점을 구체적으로 명시하세요.",
            score=20,
            evidence_text=data.retention_period,
        )

    # ============================================================
    # 3. 민감정보 / 고유식별정보
    # ============================================================

    for item in data.collected_items:

        if item.sensitive:
            add_finding(
                rule_id="SENSITIVE_DATA_NO_SEPARATE_CONSENT",
                severity=RuleSeverity.HIGH,
                category="민감정보",
                title="민감정보 수집 검토 필요",
                reason=(
                    f"{item.original_name}이 민감정보로 분류되어 "
                    "별도 동의 및 수집 필요성에 대한 검토가 필요합니다."
                ),
                recommendation=(
                    "민감정보 수집이 필요한지 확인하고, "
                    "필요한 경우 별도의 동의 및 고지 여부를 검토하세요."
                ),
                score=35,
                evidence_text=item.evidence_text,
                affected_items=[item.original_name],
                confidence=item.confidence,
            )

        if item.unique_identifier:
            add_finding(
                rule_id="HIGH_RISK_IDENTIFIER",
                severity=RuleSeverity.HIGH,
                category="고유식별정보",
                title="고위험 식별정보 수집 검토 필요",
                reason=(
                    f"{item.original_name}이 고유식별정보로 분류되어 "
                    "수집의 필요성과 적절한 처리 근거에 대한 검토가 필요합니다."
                ),
                recommendation=(
                    "해당 식별정보의 수집 필요성과 처리 근거를 확인하고 "
                    "불필요한 경우 수집하지 않도록 검토하세요."
                ),
                score=40,
                evidence_text=item.evidence_text,
                affected_items=[item.original_name],
                confidence=item.confidence,
            )

    # ============================================================
    # 4. 제3자 제공
    # ============================================================

    if data.third_party_provision_present is False:
        add_finding(
            rule_id="THIRD_PARTY_PROVISION_MISSING",
            severity=RuleSeverity.WARNING,
            category="제3자 제공",
            title="제3자 제공 내용 확인 필요",
            reason="제3자 제공 여부 또는 관련 고지를 확인하지 못했습니다.",
            recommendation="제3자 제공이 있는 경우 제공받는 자, 목적, 항목 등을 명확하게 고지하세요.",
            score=25,
        )

    # ============================================================
    # 5. 국외 이전
    # ============================================================

    if data.overseas_transfer_present is False:
        # 여기서는 단순히 '국외 이전이 없다'를 위험으로 확정하지 않는다.
        # 실제 국외 이전 여부가 확인되지 않은 경우에만 별도 Rule을
        # 추가하는 것이 더 안전하다.
        pass

    return findings
