import type { Analysis } from "./ConsentAnalysisPanel";

export type ExtensionResult = {
  version: 1; id: string; analysis: Analysis; domain: string; scannedAt: string;
  coverage: string; incomplete: boolean;
  documentStatuses: Array<{ url: string; state: string; message: string }>;
};

export function parseExtensionResult(raw: string): ExtensionResult {
  if (raw.length > 2_000_000) throw new Error("분석 결과가 너무 큽니다.");
  const value = JSON.parse(raw);
  const text = (v: unknown) => typeof v === "string";
  const array = (v: unknown) => Array.isArray(v) && v.length <= 2000;
  const a = value?.analysis;
  if (value?.version !== 1 || !text(value.id) || !text(value.domain) || !text(value.scannedAt)
    || !text(value.coverage) || typeof value.incomplete !== "boolean"
    || !a || !text(a.service_name) || !array(a.extracted?.collected_items)
    || !a.extracted.collected_items.every((i: Record<string, unknown>) => i && [i.original_name, i.normalized_name, i.reason, i.evidence_text].every(text))
    || !array(a.findings) || !a.findings.every((f: Record<string, any>) => f && [f.rule_id, f.title, f.reason, f.recommendation].every(text)
      && array(f.legal_bases) && f.legal_bases.every((b: Record<string, unknown>) => b && [b.law_name, b.article, b.title, b.rationale, b.source_url].every(text)))
    || !Number.isFinite(a.risk_summary?.score) || a.risk_summary.score < 0 || a.risk_summary.score > 100
    || !["LOW", "MEDIUM", "HIGH", "CRITICAL"].includes(a.risk_summary.level) || !text(a.risk_summary.explanation)
    || !array(value.documentStatuses) || !value.documentStatuses.every((d: Record<string, unknown>) => d && [d.url, d.state, d.message].every(text))) {
    throw new Error("확장 프로그램의 분석 결과 형식을 확인하지 못했습니다.");
  }
  return value as ExtensionResult;
}

export function safeLegalUrl(url: string): string | undefined {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" && ["www.law.go.kr", "law.go.kr"].includes(parsed.hostname) ? parsed.href : undefined;
  } catch { return undefined; }
}
