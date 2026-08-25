import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import type { PageScanResult } from "@privacylens/contracts";
import { requestPageScan } from "./messaging";
import "./styles.css";

const WEB_SERVICE_URL = "https://privacylens.site";

type Analysis = {
  service_name: string;
  extracted: { collected_items: Array<{ normalized_name: string }> };
  risk_summary: { score: number; level: string; explanation: string };
};

const categoryLabel: Record<string, string> = {
  name: "이름", email: "이메일", phone: "휴대전화번호", address: "주소",
  birth_date: "생년월일", gender: "성별", nickname: "닉네임", location: "위치정보",
  payment: "결제정보", identifier: "고유식별정보", password: "비밀번호 필드", unknown: "확인 필요",
};

function App() {
  const [result, setResult] = useState<PageScanResult | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function analyze() {
    setError(""); setLoading(true); setAnalysis(null);
    const response = await requestPageScan();
    if (response.type === "PAGE_SCAN_FAILED") {
      setError(response.error.message); setLoading(false); return;
    }
    if (response.type !== "PAGE_SCAN_COMPLETED") {
      setError("페이지 분석 응답을 확인하지 못했습니다."); setLoading(false); return;
    }

    const scan = response.payload;
    setResult(scan);
    if (scan.analysisText.trim().length < 20) {
      setError("분석할 개인정보 동의문이나 입력 항목을 찾지 못했습니다.");
      setLoading(false); return;
    }

    try {
      const apiResponse = await fetch(`${WEB_SERVICE_URL}/api/v1/analyses/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          service_name: scan.page.title || scan.page.domain,
          service_function: "현재 페이지의 개인정보 입력 및 동의",
          document_text: scan.analysisText,
        }),
      });
      const payload = await apiResponse.json().catch(() => null);
      if (!apiResponse.ok) throw new Error(payload?.detail ?? "AI 분석 요청을 처리하지 못했습니다.");
      setAnalysis(payload as Analysis);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "AI 분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  const critical = result?.warnings.length || (analysis && ["HIGH", "CRITICAL"].includes(analysis.risk_summary.level));

  return <main>
    <header><strong>Privacy<span>Lens</span></strong><small>실제 입력값은 읽지 않아요</small></header>
    <section><p className="eyebrow">PAGE CHECK</p><h1>제공하기 전에<br />한번 더 확인하세요.</h1><button onClick={analyze} disabled={loading}>{loading ? "분석 중…" : "현재 페이지 분석"}</button></section>
    {error && <p className="error" role="alert">{error}</p>}
    {result && <div className={`result ${critical ? "riskCritical" : ""}`}>
      <h2>{result.page.domain}</h2>
      {analysis && <div className="risk"><strong>{analysis.risk_summary.level}</strong><span>위험 점수 {analysis.risk_summary.score}</span><p>{analysis.risk_summary.explanation}</p></div>}
      <label>탐지된 개인정보 필드</label><div className="chips">{result.fields.length ? result.fields.map((field) => <span key={field.id}>{categoryLabel[field.category]} · {field.requirement}</span>) : <em>탐지된 항목 없음</em>}</div>
      <label>동의 항목</label><p>{result.consents.length}개 탐지 · 기본 선택 경고 {result.warnings.length}건</p>
      <a className="webLink" href={WEB_SERVICE_URL} target="_blank" rel="noreferrer">웹서비스에서 자세히 보기</a>
      <footer>요청 ID {result.requestId.slice(0, 12)}…</footer>
    </div>}
    <aside>분석 결과는 법률 판단이 아닌 확인 보조 정보입니다.</aside>
  </main>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
