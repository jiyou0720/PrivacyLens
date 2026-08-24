"use client";

import { FormEvent, useState } from "react";

type Analysis = {
  service_name: string;
  extracted: { collected_items: Array<{ original_name: string; normalized_name: string; necessity: string; reason: string; evidence_text: string }> };
  findings: Array<{ rule_id: string; title: string; reason: string; recommendation: string }>;
  risk_summary: { score: number; level: string; explanation: string };
};

export default function ConsentAnalysisPanel() {
  const [serviceName, setServiceName] = useState("");
  const [serviceFunction, setServiceFunction] = useState("");
  const [documentText, setDocumentText] = useState("");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setAnalysis(null);
    setLoading(true);
    try {
      const response = await fetch("/api/v1/analyses/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          service_name: serviceName.trim(),
          service_function: serviceFunction.trim() || null,
          document_text: documentText.trim(),
        }),
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error(payload?.detail ?? "분석 요청을 처리하지 못했습니다.");
      setAnalysis(payload as Analysis);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="records">
      <div className="sectionTitle"><div><p className="eyebrow">CONSENT ANALYSIS</p><h2>개인정보 동의문 분석</h2></div></div>
      <form className="record analysisForm" onSubmit={submit}>
        <label>서비스 이름<input required maxLength={100} value={serviceName} onChange={(event) => setServiceName(event.target.value)} /></label>
        <label>서비스 기능<input maxLength={1000} value={serviceFunction} onChange={(event) => setServiceFunction(event.target.value)} /></label>
        <label>개인정보 동의문<textarea required minLength={20} maxLength={100000} value={documentText} onChange={(event) => setDocumentText(event.target.value)} /></label>
        <button type="submit" disabled={loading}>{loading ? "분석 중..." : "분석하기"}</button>
      </form>
      {error && <aside className="notice" role="alert"><strong>분석 실패</strong><p>{error}</p></aside>}
      {analysis && <article className="record analysisResult">
        <div className="recordHead"><div className="logo">{analysis.risk_summary.score}</div><div><h3>{analysis.service_name}</h3><p>{analysis.risk_summary.level}</p></div></div>
        <p>{analysis.risk_summary.explanation}</p>
        <div className="chips">{analysis.extracted.collected_items.map((item) => <span key={item.original_name}>{item.normalized_name}</span>)}</div>
        {analysis.extracted.collected_items.map((item) => <div className="resultItem" key={item.evidence_text}><strong>{item.original_name}</strong><p>{item.reason}</p><small>근거: {item.evidence_text}</small></div>)}
        {analysis.findings.map((finding) => <div className="resultItem" key={finding.rule_id}><strong>{finding.title}</strong><p>{finding.reason}</p><small>권장: {finding.recommendation}</small></div>)}
      </article>}
    </section>
  );
}
