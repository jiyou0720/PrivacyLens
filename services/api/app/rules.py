from .models import ExtractedConsent, LegalBasis, RuleFinding, RuleSeverity

AMBIGUOUS_RETENTION = (
    "필요시",
    "목적 달성 시",
    "관계 법령에 따름",
    "별도 고지",
)

UNIQUE_IDENTIFIER_KEYWORDS = (
    "주민등록번호",
    "여권번호",
    "운전면허번호",
    "외국인등록번호",
)

RULE_VERSION = "consent-rules-v4"

PIPA_URL = "https://www.law.go.kr/법령/개인정보보호법"
PIPA_DECREE_URL = "https://www.law.go.kr/법령/개인정보보호법시행령"


def article_url(base_url: str, article: str) -> str:
    """Link to the exact article, not merely the law's opening page."""
    return f"{base_url}/{article.split()[0]}"


def legal_basis(article: str, title: str, rationale: str) -> LegalBasis:
    return LegalBasis(
        law_name="개인정보 보호법",
        article=article,
        title=title,
        rationale=rationale,
        source_url=article_url(PIPA_URL, article),
    )


CONSENT_METHOD = LegalBasis(
    law_name="개인정보 보호법 시행령",
    article="제17조",
    title="동의를 받는 방법",
    rationale="정보주체가 동의 내용을 확인할 수 있는 방법으로 동의를 받아야 합니다.",
    source_url=article_url(PIPA_DECREE_URL, "제17조"),
)

LEGAL_BASES: dict[str, list[LegalBasis]] = {
    "PURPOSE_MISSING": [legal_basis("제15조 제2항", "개인정보의 수집·이용", "수집·이용 목적을 알려야 합니다."), CONSENT_METHOD],
    "ITEMS_MISSING": [legal_basis("제15조 제2항", "개인정보의 수집·이용", "수집할 개인정보 항목을 알려야 합니다."), CONSENT_METHOD],
    "RETENTION_MISSING": [legal_basis("제15조 제2항", "개인정보의 수집·이용", "보유·이용 기간을 알려야 합니다.")],
    "REFUSAL_RIGHT_MISSING": [legal_basis("제15조 제2항", "개인정보의 수집·이용", "동의 거부권을 알려야 합니다."), CONSENT_METHOD],
    "REFUSAL_CONSEQUENCE_MISSING": [legal_basis("제15조 제2항", "개인정보의 수집·이용", "거부 시 불이익이 있다면 그 내용을 알려야 합니다."), CONSENT_METHOD],
    "RETENTION_AMBIGUOUS": [legal_basis("제15조 제2항", "개인정보의 수집·이용", "보유·이용 기간을 구체적으로 알려야 합니다."), legal_basis("제21조", "개인정보의 파기", "불필요해진 개인정보는 지체 없이 파기해야 합니다.")],
    "SPECIAL_DATA_REVIEW": [legal_basis("제23조", "민감정보의 처리 제한", "법령 근거가 없다면 민감정보에 대해 별도 동의가 필요합니다.")],
    "UNIQUE_IDENTIFIER_REVIEW": [legal_basis("제24조", "고유식별정보의 처리 제한", "법령 근거가 없다면 고유식별정보에 대해 별도 동의가 필요합니다.")],
    "THIRD_PARTY_PROVISION_MISSING": [legal_basis("제17조 제2항", "개인정보의 제공", "제3자 제공 관련 필수 사항을 알려야 합니다.")],
}


def evaluate_rules(data: ExtractedConsent) -> list[RuleFinding]:
    findings: list[RuleFinding] = []

    def with_subject(value: str) -> str:
        """Attach the Korean subject particle that matches the final syllable."""
        if not value:
            return value
        last = value[-1]
        if "가" <= last <= "힣":
            has_batchim = (ord(last) - ord("가")) % 28 != 0
            return f"{value}{'은' if has_batchim else '는'}"
        return f"{value}은"

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
        legal_bases: list[LegalBasis] | None = None,
    ) -> None:
        findings.append(
            RuleFinding(
                rule_id=rule_id,
                legal_bases=legal_bases or LEGAL_BASES.get(rule_id, []),
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

    relevant_items = [
        item for item in data.collected_items
        if item.applies_to_current_function is not False
    ]
    item_retention_complete = bool(relevant_items) and all(
        item.retention_period for item in relevant_items
    )
    if not data.retention_period and not item_retention_complete:
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

    retention_text = data.retention_period or " / ".join(
        item.retention_period for item in relevant_items if item.retention_period
    )
    retention = retention_text.replace(" ", "")

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
            evidence_text=retention_text,
        )

    # ============================================================
    # 3. 민감정보 / 고유식별정보
    # ============================================================

    for item in data.collected_items:
        if item.applies_to_current_function is False or item.confidence == 0:
            continue
        normalized = item.original_name.replace(" ", "")

        substantiated_concern = (
            item.applies_to_current_function is True
            and bool(item.scope_evidence)
            and item.separate_consent_present is False
            and bool(item.consent_evidence)
        )
        unresolved_separate_consent = (
            item.applies_to_current_function is True
            and bool(item.scope_evidence)
            and item.separate_consent_present is not True
        )

        if item.sensitive:
            add_finding(
                rule_id="SPECIAL_DATA_REVIEW",
                severity=RuleSeverity.HIGH if substantiated_concern else RuleSeverity.WARNING,
                category="민감정보",
                title="민감정보 수집 검토 필요",
                reason=(
                    f"{with_subject(item.original_name)} 민감정보로 분류되어 "
                    "별도 동의 및 수집 필요성에 대한 검토가 필요합니다."
                ),
                recommendation=(
                    "민감정보 수집이 필요한지 확인하고, "
                    "필요한 경우 별도의 동의 및 고지 여부를 검토하세요."
                ),
                score=35 if substantiated_concern else 20 if unresolved_separate_consent else 0,
                evidence_text=item.evidence_text,
                affected_items=[item.original_name],
                confidence=item.confidence,
            )

        # 서비스 계정 ID·내부 식별값은 개인정보일 수 있지만 법령상
        # 고유식별정보는 아닙니다. 모델의 boolean 추정만으로 제24조를
        # 적용하지 않고 법정 식별번호가 원문 항목명에 명시된 경우만 봅니다.
        is_unique_identifier = any(
            keyword in normalized
            for keyword in UNIQUE_IDENTIFIER_KEYWORDS
        )

        if is_unique_identifier:
            add_finding(
                rule_id="UNIQUE_IDENTIFIER_REVIEW",
                severity=RuleSeverity.HIGH if substantiated_concern else RuleSeverity.WARNING,
                category="고유식별정보",
                title="고유식별정보 수집 검토 필요",
                reason=(
                    f"{with_subject(item.original_name)} 고유식별정보에 해당할 가능성이 있어 "
                    "수집 근거와 별도 처리 여부를 검토해야 합니다."
                ),
                recommendation=(
                    "해당 식별정보의 수집 필요성과 처리 근거를 확인하고 "
                    "불필요한 경우 수집하지 않도록 검토하세요."
                ),
                score=40 if substantiated_concern else 25 if unresolved_separate_consent else 0,
                evidence_text=item.evidence_text,
                affected_items=[item.original_name],
                confidence=item.confidence,
            )

    # ============================================================
    # 4. 제3자 제공
    # ============================================================

    # Presence alone does not establish defective disclosure. Until the
    # recipient/purpose/items/period/consent evidence is modeled, review only.
    if data.third_party_provision_present is True:
        add_finding(
            rule_id="THIRD_PARTY_PROVISION_MISSING",
            severity=RuleSeverity.WARNING,
            category="제3자 제공",
            title="제3자 제공 내용 확인 필요",
            reason="제3자 제공이 언급되어 관련 고지와 처리 근거의 확인이 필요합니다.",
            recommendation="제3자 제공이 있는 경우 제공받는 자, 목적, 항목 등을 명확하게 고지하세요.",
            score=0,
            confidence=0.5,
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
