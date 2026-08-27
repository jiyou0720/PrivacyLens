"use client";

import { FormEvent, useEffect, useState } from "react";
import { safeLegalUrl, type ExtensionResult } from "./extensionResult";

export type Analysis = {
  service_name: string;
  extracted: { collected_items: Array<{ original_name: string; normalized_name: string; necessity: string; reason: string; evidence_text: string }> };
  findings: Array<{ rule_id: string; title: string; reason: string; recommendation: string; legal_bases: Array<{ law_name: string; article: string; title: string; rationale: string; source_url: string }> }>;
  risk_summary: { score: number; level: string; explanation: string };
};

type Props = { onAnalyzed: (analysis: Analysis) => void; selected?: ExtensionResult | null };
const riskLabel = (level: string) => level === "LOW" ? "확인된 위험 낮음" : level;

export default function ConsentAnalysisPanel({ onAnalyzed, selected }: Props) {
  const [serviceName, setServiceName] = useState("");
  const [serviceFunction, setServiceFunction] = useState("");
  const [documentText, setDocumentText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [source, setSource] = useState<ExtensionResult | null>(null);
  useEffect(() => {
    if (selected) { setAnalysis(selected.analysis); setSource(selected); setError(null); }
  }, [selected]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null); setAnalysis(null); setSource(null); setLoading(true);
    try {
      let response: Response;
      if (file) {
        if (file.size > 10_000_000) throw new Error("파일은 10MB 이하만 업로드할 수 있습니다.");
        const body = new FormData();
        body.append("service_name", serviceName.trim());
        body.append("service_function", serviceFunction.trim());
        body.append("file", file);
        response = await fetch("/api/v1/analyses/file", { method: "POST", body });
      } else {
        response = await fetch("/api/v1/analyses/text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            service_name: serviceName.trim(),
            service_function: serviceFunction.trim() || null,
            document_text: documentText.trim(),
          }),
        });
      }
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        if (response.status === 413) throw new Error("파일 용량이 서버 업로드 한도를 초과했습니다. 10MB 이하 파일을 사용해 주세요.");
        throw new Error(payload?.detail ?? `분석 요청을 처리하지 못했습니다. (HTTP ${response.status})`);
      }
      const result = payload as Analysis;
      setAnalysis(result);
      onAnalyzed(result);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  const riskTone = source?.incomplete ? "mediumResult" : analysis ? analysis.risk_summary.level === "LOW" ? "lowResult" : analysis.risk_summary.level === "MEDIUM" ? "mediumResult" : "criticalResult" : "";

  return (
    <section className="records">
      <div className="sectionTitle"><div><p className="eyebrow">CONSENT ANALYSIS</p><h2>개인정보 동의문 분석</h2></div></div>
      <form className="record analysisForm" onSubmit={submit}>
        <label>서비스 이름<input required maxLength={100} value={serviceName} onChange={(event) => setServiceName(event.target.value)} /></label>
        <label>서비스 기능<input maxLength={1000} value={serviceFunction} onChange={(event) => setServiceFunction(event.target.value)} /></label>
        <label>동의문 파일 (TXT, MD, PDF · 최대 10MB)<input type="file" accept=".txt,.md,.pdf,text/plain,application/pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
        <label>개인정보 동의문<textarea required={!file} minLength={file ? undefined : 20} maxLength={100000} disabled={Boolean(file)} value={documentText} onChange={(event) => setDocumentText(event.target.value)} placeholder={file ? "선택한 파일의 내용을 분석합니다." : undefined} /></label>
        <button type="submit" disabled={loading}>{loading ? "분석 중..." : "분석하기"}</button>
      </form>
      {error && <aside className="notice" role="alert"><strong>분석 실패</strong><p>{error}</p></aside>}
      {analysis && <article className={`record analysisResult ${riskTone}`}>
        <div className="recordHead"><div className="logo">{source?.incomplete ? "—" : analysis.risk_summary.score}</div><div><h3>{analysis.service_name}</h3><p className={`${riskTone}Level`}>{source?.incomplete ? "분석 불충분" : riskLabel(analysis.risk_summary.level)}</p></div></div>
        <p>{source?.incomplete ? "수집하지 못한 내용이 있어 위험 점수와 등급을 표시하지 않습니다." : analysis.risk_summary.explanation}</p>
        {source && <div className="resultItem"><strong>{source.domain} · 확장 분석 결과</strong><p>{source.coverage} · 재분석 없이 불러옴</p>{source.documentStatuses.map((document, index) => <p key={`${document.url}-${index}`}>{document.message} · {document.url}</p>)}</div>}
        <div className="chips">{analysis.extracted.collected_items.map((item) => <span key={item.original_name}>{item.normalized_name}</span>)}</div>
        {analysis.extracted.collected_items.map((item) => <div className="resultItem" key={`${item.original_name}-${item.evidence_text}`}><strong>{item.original_name}</strong><p>{item.reason}</p><small>근거: {item.evidence_text}</small></div>)}
        {analysis.findings.map((finding) => <div className="resultItem" key={finding.rule_id}><strong>{finding.title}</strong><p>{finding.reason}</p><small>권장: {finding.recommendation}</small>{finding.legal_bases.map((basis) => <p key={`${finding.rule_id}-${basis.law_name}-${basis.article}`}><strong>{basis.law_name} {basis.article} · {basis.title}</strong><br /><small>핵심 요약: {basis.rationale}</small><br /><a href={safeLegalUrl(basis.source_url)} target="_blank" rel="noreferrer">해당 조문 원문 보기 →</a></p>)}</div>)}
      </article>}
    </section>
  );
}
