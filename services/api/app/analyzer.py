import re
from datetime import UTC, datetime

from .models import AnalyzeRequest, Confidence, Evidence, PolicyAnalysis

DATA_PATTERNS = {
    "이메일": r"이메일|전자우편",
    "휴대전화번호": r"휴대.?전화|전화번호",
    "이름": r"성명|이름",
    "주소": r"주소",
    "생년월일": r"생년월일|생일",
}


def _sentence(text: str, match: re.Match[str]) -> str:
    start = max(text.rfind(".", 0, match.start()) + 1, text.rfind("\n", 0, match.start()) + 1)
    end_candidates = [position for position in (text.find(".", match.end()), text.find("\n", match.end())) if position >= 0]
    end = min(end_candidates) + 1 if end_candidates else min(len(text), match.end() + 200)
    return text[start:end].strip()[:500]


def analyze_policy(request: AnalyzeRequest) -> PolicyAnalysis:
    collected: list[str] = []
    evidence: list[Evidence] = []
    for label, pattern in DATA_PATTERNS.items():
        if match := re.search(pattern, request.document_text, re.IGNORECASE):
            collected.append(label)
            evidence.append(Evidence(quote=_sentence(request.document_text, match), confidence=Confidence.CONFIRMED))

    retention_matches = re.findall(r"(?:보유|이용).{0,20}(?:탈퇴 시까지|\d+년|\d+개월)", request.document_text)
    sharing_match = re.search(r"제3자.{0,30}(?:제공|공유).{0,10}", request.document_text)
    third_party = bool(sharing_match) and not bool(
        sharing_match and re.search(r"(?:제공|공유)하지\s*않", sharing_match.group())
    )
    if not collected:
        evidence.append(Evidence(quote=request.document_text[:300], confidence=Confidence.NEEDS_REVIEW))

    return PolicyAnalysis(
        service_name=request.service_name,
        policy_url=request.policy_url,
        collected_data=collected,
        purposes=[],
        retention_periods=list(dict.fromkeys(retention_matches)),
        third_party_sharing=third_party,
        outsourcing=[],
        user_rights=[],
        evidence=evidence,
        analysis_date=datetime.now(tz=UTC).date(),
    )
