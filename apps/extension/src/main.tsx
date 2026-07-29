import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import type { ScanResult } from "./scanner";
import "./styles.css";

function App() {
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState("");

  async function analyze() {
    setError("");
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab.id) throw new Error("현재 탭을 찾을 수 없습니다.");
      const [{ result: scan }] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const patterns: Array<[RegExp, string]> = [[/email|이메일/i,"이메일"],[/tel|phone|mobile|전화번호/i,"휴대전화번호"],[/birth|생년월일/i,"생년월일"],[/address|주소/i,"주소"],[/name|이름|성명/i,"이름"]];
          const fields = [...document.querySelectorAll<HTMLInputElement>("input, select, textarea")];
          const types = new Set<string>();
          fields.forEach((field) => { const hint=[field.type,field.name,field.id,field.placeholder,field.labels?.[0]?.textContent].join(" "); patterns.forEach(([p,t])=>p.test(hint)&&types.add(t)); });
          const policyLinks=[...document.querySelectorAll<HTMLAnchorElement>("a[href]")].filter((a)=>/개인정보|privacy|수집.?이용|제3자.?제공/i.test(a.textContent??"")).map((a)=>a.href);
          const preselectedConsents=fields.filter((f)=>f.type==="checkbox"&&f.checked).map((f)=>f.labels?.[0]?.textContent?.trim()??f.name).filter((t)=>/선택|마케팅|광고|수신/i.test(t));
          return {domain:location.hostname,dataTypes:[...types],policyLinks,preselectedConsents};
        },
      });
      setResult(scan as ScanResult);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "분석에 실패했습니다."); }
  }

  return <main><header><strong>Privacy<span>Lens</span></strong><small>실제 입력값은 읽지 않아요</small></header><section><p className="eyebrow">PAGE CHECK</p><h1>제공하기 전에<br/>한번 더 확인하세요.</h1><button onClick={analyze}>현재 페이지 분석</button></section>{error&&<p className="error">{error}</p>}{result&&<div className="result"><h2>{result.domain}</h2><label>탐지된 개인정보 유형</label><div className="chips">{result.dataTypes.length?result.dataTypes.map((x)=><span key={x}>{x}</span>):<em>탐지된 항목 없음</em>}</div><label>주의 신호</label><p>{result.preselectedConsents.length?`기본 선택된 선택 동의 ${result.preselectedConsents.length}개가 있습니다.`:"기본 선택된 선택 동의를 찾지 못했습니다."}</p><footer>처리방침 링크 {result.policyLinks.length}개 탐지</footer></div>}<aside>분석 결과는 법률 판단이 아닌 확인 보조 정보입니다.</aside></main>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
