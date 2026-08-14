import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import type { PageScanResult } from "@privacylens/contracts";
import { requestPageScan } from "./messaging";
import "./styles.css";

const categoryLabel: Record<string, string> = {
  name: "이름", email: "이메일", phone: "휴대전화번호", address: "주소",
  birth_date: "생년월일", gender: "성별", nickname: "닉네임", location: "위치정보",
  payment: "결제정보", identifier: "고유식별정보", password: "비밀번호 필드", unknown: "확인 필요",
};

function App() {
  const [result, setResult] = useState<PageScanResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function analyze() {
    setError(""); setLoading(true);
    const response = await requestPageScan();
    setLoading(false);
    if (response.type === "PAGE_SCAN_COMPLETED") setResult(response.payload);
    if (response.type === "PAGE_SCAN_FAILED") setError(response.error.message);
  }

  return <main>
    <header><strong>Privacy<span>Lens</span></strong><small>실제 입력값은 읽지 않아요</small></header>
    <section><p className="eyebrow">PAGE CHECK</p><h1>제공하기 전에<br />한번 더 확인하세요.</h1><button onClick={analyze} disabled={loading}>{loading ? "분석 중…" : "현재 페이지 분석"}</button></section>
    {error && <p className="error" role="alert">{error}</p>}
    {result && <div className="result"><h2>{result.page.domain}</h2><label>탐지된 개인정보 필드</label><div className="chips">{result.fields.length ? result.fields.map((field) => <span key={field.id}>{categoryLabel[field.category]} · {field.requirement}</span>) : <em>탐지된 항목 없음</em>}</div><label>동의 항목</label><p>{result.consents.length}개 탐지 · 기본 선택 경고 {result.warnings.length}건</p><footer>요청 ID {result.requestId.slice(0, 12)}…</footer></div>}
    <aside>분석 결과는 법률 판단이 아닌 확인 보조 정보입니다.</aside>
  </main>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
