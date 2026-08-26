import { describe, expect, it } from "vitest";
import { decodeExtensionResultHash, parseExtensionResult, safeLegalUrl } from "../../dashboard/app/extensionResult";
import { encodeExtensionResult } from "./webResult";

const payload = {
  version: 1, id: "8cd180d0-1ad4-4e89-bf75-85fb9897a38e", domain: "example.com",
  scannedAt: "2026-08-27T00:00:00.000Z", coverage: "연결 문서 1/1개 본문 반영", incomplete: false,
  documentStatuses: [{ url: "https://example.com/policy", state: "success", message: "본문 수집 완료" }],
  analysis: {
    service_name: "예시", extracted: { collected_items: [{ original_name: "이메일", normalized_name: "이메일", reason: "명시", evidence_text: "이메일" }] },
    findings: [{ rule_id: "r1", title: "확인", reason: "근거", recommendation: "검토", legal_bases: [{ law_name: "개인정보 보호법", article: "제15조", title: "수집", rationale: "고지", source_url: "https://www.law.go.kr/법령/개인정보보호법/제15조" }] }],
    risk_summary: { score: 20, level: "MEDIUM", explanation: "확인" },
  },
};

describe("extension result handoff", () => {
  it("accepts a complete result without re-analysis", () => expect(parseExtensionResult(JSON.stringify(payload))).toMatchObject({ domain: "example.com", analysis: { service_name: "예시" } }));
  it("round-trips Korean result data through the local URL fragment", () => {
    const encoded = encodeExtensionResult(payload);
    expect(parseExtensionResult(decodeExtensionResultHash(encoded))).toMatchObject({ domain: "example.com", analysis: { service_name: "예시" } });
  });
  it("rejects malformed results", () => expect(() => parseExtensionResult(JSON.stringify({ ...payload, analysis: { ...payload.analysis, risk_summary: { score: 101, level: "LOW", explanation: "x" } } }))).toThrow());
  it("only links to official law pages", () => {
    expect(safeLegalUrl("https://www.law.go.kr/법령/개인정보보호법/제15조")).toContain("law.go.kr");
    expect(safeLegalUrl("javascript:alert(1)")).toBeUndefined();
    expect(safeLegalUrl("https://evil.example/law.go.kr")).toBeUndefined();
  });
});
