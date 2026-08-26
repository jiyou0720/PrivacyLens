from app.models import (
    ExtractedConsent,
    RiskLevel,
    RiskSummary,
    RuleFinding,
    RuleSeverity,
)


def merge_findings(
    findings: list[RuleFinding],
) -> list[RuleFinding]:
    """
    동일한 Rule이 여러 번 발견된 경우 하나로 병합합니다.

    예:
        HIGH_RISK_IDENTIFIER
        HIGH_RISK_IDENTIFIER

    → 하나의 Finding으로 통합
    """

    merged: dict[str, RuleFinding] = {}

    for finding in findings:
        existing = merged.get(finding.rule_id)

        if existing is None:
            merged[finding.rule_id] = finding
            continue

        # 같은 Rule이 여러 개인정보 항목에서 발생할 경우
        # 영향을 받는 항목은 합친다.
        affected_items = list(
            dict.fromkeys(
                [
                    *existing.affected_items,
                    *finding.affected_items,
                ]
            )
        )

        # evidence도 서로 다르면 유지한다.
        evidence_text = existing.evidence_text

        if (
            finding.evidence_text
            and finding.evidence_text != existing.evidence_text
        ):
            evidence_text = (
                f"{existing.evidence_text} / "
                f"{finding.evidence_text}"
            )

        # 더 높은 confidence 사용
        confidence = max(
            existing.confidence,
            finding.confidence,
        )

        merged[finding.rule_id] = existing.model_copy(
            update={
                "affected_items": affected_items,
                "evidence_text": evidence_text,
                "confidence": confidence,
                "score": max(existing.score, finding.score),
                "severity": max(
                    (existing.severity, finding.severity),
                    key=lambda value: {"info": 0, "warning": 1, "high": 2}[value],
                ),
            }
        )

    return list(merged.values())


def calculate_risk_score(
    findings: list[RuleFinding],
) -> int:
    """
    Finding의 점수를 합산하여 0~100 사이의
    제품용 위험 점수를 계산합니다.

    법적 판단 점수가 아닌 제품용 초기 점수입니다.
    """

    high_risk_rule_ids = {
        "SPECIAL_DATA_REVIEW",
        "UNIQUE_IDENTIFIER_REVIEW",
        "THIRD_PARTY_PROVISION_MISSING",
    }
    high_risk_score = sum(
        finding.score for finding in findings
        if finding.rule_id in high_risk_rule_ids
    )
    disclosure_score = sum(
        finding.score for finding in findings
        if finding.rule_id not in high_risk_rule_ids
    )

    # 불완전한 화면 추출 때문에 단순 고지 누락만 누적되어
    # 곧바로 CRITICAL이 되지 않도록 안내성 점수에 상한을 둡니다.
    return min(high_risk_score + min(disclosure_score, 30), 100)


def calculate_risk_level(
    score: int,
) -> RiskLevel:

    if score >= 70:
        return RiskLevel.CRITICAL

    if score >= 40:
        return RiskLevel.HIGH

    if score >= 20:
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


def check_human_review(
    findings: list[RuleFinding],
    extracted: ExtractedConsent,
    unverified_evidence: list[str],
) -> bool:
    """
    위험 점수와 별개로 사람의 검토가 필요한 상황을 판단합니다.
    """

    # LLM이 자체적으로 검토 필요성을 판단한 경우
    if extracted.requires_human_review:
        return True

    # LLM evidence가 원문에서 검증되지 않은 경우
    if unverified_evidence:
        return True

    for finding in findings:

        # 고위험 개인정보 관련 결과
        if finding.rule_id in {
            "HIGH_RISK_IDENTIFIER",
            "SPECIAL_DATA_REVIEW",
            "UNIQUE_IDENTIFIER_REVIEW",
        }:
            return True

        # HIGH severity
        if finding.severity == RuleSeverity.HIGH:
            return True

        # 신뢰도가 낮은 결과
        if finding.confidence < 0.7:
            return True

    return False


def build_risk_summary(
    findings: list[RuleFinding],
    extracted: ExtractedConsent,
    unverified_evidence: list[str],
) -> RiskSummary:

    score = calculate_risk_score(
        findings
    )

    level = calculate_risk_level(
        score
    )

    human_review = check_human_review(
        findings=findings,
        extracted=extracted,
        unverified_evidence=unverified_evidence,
    )

    if human_review:
        explanation = (
            "위험 점수와 별개로 근거 확인 또는 "
            "고위험 개인정보 처리에 대한 사람의 검토가 필요합니다."
        )
    elif level == RiskLevel.CRITICAL:
        explanation = (
            "여러 고위험 요소가 확인되어 "
            "우선적인 검토가 필요합니다."
        )
    elif level == RiskLevel.HIGH:
        explanation = (
            "개인정보 처리와 관련된 주요 위험 요소가 "
            "확인되어 검토가 필요합니다."
        )
    elif level == RiskLevel.MEDIUM:
        explanation = (
            "일부 주의가 필요한 요소가 확인되었습니다."
        )
    else:
        explanation = (
            "현재 규칙에서 높은 위험 요소는 "
            "확인되지 않았습니다."
        )

    return RiskSummary(
        score=score,
        level=level,
        requires_human_review=human_review,
        explanation=explanation,
    )
