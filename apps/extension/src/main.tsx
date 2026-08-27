import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import type { PageScanResult } from "@privacylens/contracts";
import { requestPageScan } from "./messaging";
import { budgetDocuments } from "./documentBudget";
import { fieldLabels } from "./fieldLabels";
import { openWebResult } from "./webResult";
import "./styles.css";

const WEB_SERVICE_URL = "https://privacylens.site";
const riskLabel = (level: string) => level === "LOW" ? "확인된 위험 낮음" : level;

type Analysis = {
  service_name: string;
  extracted: { collected_items: Array<{ original_name: string; normalized_name: string; collection_context?: string; applies_to_current_function?: boolean | null }> };
  findings: Array<{ rule_id: string; legal_bases: Array<{ law_name: string; article: string; title: string; rationale: string; source_url: string }> }>;
  risk_summary: { score: number; level: string; explanation: string; requires_human_review?: boolean };
};

type DocumentStatus = { url: string; state: "success" | "partial" | "permission" | "http" | "format" | "empty" | "failed"; message: string };
type SavedView = { result: PageScanResult; analysis: Analysis | null; error: string; coverage: string; incomplete: boolean; documentStatuses: DocumentStatus[] };
let restoreStarted = false;

async function readLinkedDocuments(urls: string[], pageUrl: string): Promise<{ texts: Array<{ url: string; text: string }>; attempted: number; statuses: DocumentStatus[] }> {
  const pageOrigin = new URL(pageUrl).origin;
  const candidates = urls.slice(0, 8);
  const requestedOrigins = Array.from(new Set(candidates
    .map((url) => {
      try { return `${new URL(url).origin}/*`; } catch { return null; }
    })
    .filter((origin): origin is string => origin !== null)
    .filter((origin) => !origin.startsWith(`${pageOrigin}/`))));
  let allowedOrigins = new Set<string>();
  if (requestedOrigins.length) {
    const granted = await chrome.permissions.request({ origins: requestedOrigins }).catch(() => false);
    if (granted) allowedOrigins = new Set(requestedOrigins.map((origin) => origin.slice(0, -2)));
  }
  const statuses: DocumentStatus[] = [];
  const texts: Array<{ url: string; text: string }> = [];
  for (const url of candidates) {
    let permitted = false;
    try {
      const origin = new URL(url).origin;
      permitted = origin === pageOrigin || allowedOrigins.has(origin);
    } catch { /* invalid URL */ }
    if (!permitted) {
      statuses.push({ url, state: "permission", message: "접근 권한이 없어 반영하지 못함" });
      continue;
    }
    try {
      const response = await fetch(url, { credentials: "include", signal: AbortSignal.timeout(8000) });
      if (!response.ok) {
        statuses.push({ url, state: "http", message: `응답 오류 HTTP ${response.status}` });
        continue;
      }
      if (!response.headers.get("content-type")?.includes("text/html")) {
        statuses.push({ url, state: "format", message: "HTML 문서가 아님" });
        continue;
      }
      let html = await response.text();
      let document = new DOMParser().parseFromString(html, "text/html");
      document.querySelectorAll("script, style, noscript, svg, nav, footer").forEach((node) => node.remove());
      let text = (document.body?.innerText || document.body?.textContent || "").replace(/\s+/g, " ").trim();

      // 네이버 모바일 약관은 빈 컨테이너를 먼저 반환하고 type 번호에
      // 해당하는 termN.html을 JavaScript로 다시 불러옵니다.
      const parsedUrl = new URL(url);
      if (text.length < 100 && parsedUrl.hostname === "policy.naver.com" && parsedUrl.pathname === "/policy-mobile/term.html") {
        const type = parsedUrl.searchParams.get("type");
        if (type && /^\d+$/.test(type)) {
          const contentUrl = new URL(`/policy-mobile/term${type}.html`, parsedUrl);
          const contentResponse = await fetch(contentUrl.href, { credentials: "include", signal: AbortSignal.timeout(8000) });
          if (contentResponse.ok) {
            html = await contentResponse.text();
            document = new DOMParser().parseFromString(html, "text/html");
            document.querySelectorAll("script, style, noscript, svg, nav, footer").forEach((node) => node.remove());
            text = (document.body?.innerText || document.body?.textContent || "").replace(/\s+/g, " ").trim();
          }
        }
      }
      if (text.length < 100) {
        statuses.push({ url, state: "empty", message: "분석할 본문이 없음" });
        continue;
      }
      texts.push({ url, text });
      statuses.push({ url, state: "success", message: "본문 수집 완료" });
    } catch {
      statuses.push({ url, state: "failed", message: "요청 실패 또는 시간 초과" });
    }
  }
  for (const url of urls.slice(8)) {
    statuses.push({ url, state: "partial", message: "문서 수 제한으로 미반영" });
  }
  return { texts, attempted: urls.length, statuses };
}

function App() {
  const [result, setResult] = useState<PageScanResult | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [openingWeb, setOpeningWeb] = useState(false);
  const [coverage, setCoverage] = useState("");
  const [incomplete, setIncomplete] = useState(false);
  const [documentStatuses, setDocumentStatuses] = useState<DocumentStatus[]>([]);

  async function persistView(view: SavedView) {
    await chrome.storage.local.set({ lastView: view });
  }

  async function processScan(scan: PageScanResult) {
    setResult(scan);
    if (scan.analysisText.trim().length < 20) {
      const message = "분석할 개인정보 동의문이나 입력 항목을 찾지 못했습니다.";
      setError(message); setLoading(false);
      await persistView({ result: scan, analysis: null, error: message, coverage: "", incomplete: true, documentStatuses: [] });
      return;
    }

    try {
      await chrome.storage.local.set({ pendingScan: scan });
      const linked = await readLinkedDocuments(scan.documentUrls ?? [], scan.page.url);
      const budget = budgetDocuments(scan.analysisText, linked.texts);
      for (const status of linked.statuses) {
        if (budget.clippedUrls.includes(status.url)) {
          status.state = "partial";
          status.message = "길이 제한으로 일부 또는 전체 미반영";
        }
      }
      const completeCount = linked.statuses.filter((status) => status.state === "success").length;
      const nextCoverage = linked.attempted ? `연결 문서 ${completeCount}/${linked.attempted}개 본문 반영` : "현재 화면 기준 분석";
      const nextIncomplete = linked.attempted > completeCount || budget.truncated || Boolean(scan.analysisTruncated);
      setCoverage(nextCoverage); setIncomplete(nextIncomplete); setDocumentStatuses(linked.statuses);
      const documentText = budget.text;
      if (linked.attempted > 0 && linked.texts.length === 0) {
        const message = "연결된 약관 원문을 읽지 못해 정확한 위험 점수를 계산할 수 없습니다. 분석 불충분 상태입니다.";
        setError(message);
        await persistView({ result: scan, analysis: null, error: message, coverage: nextCoverage, incomplete: true, documentStatuses: linked.statuses });
        await chrome.storage.local.remove("pendingScan");
        return;
      }
      const apiResponse = await fetch(`${WEB_SERVICE_URL}/api/v1/analyses/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ service_name: scan.page.title || scan.page.domain, service_function: `현재 페이지: ${scan.page.title}. 현재 화면의 개인정보 입력 및 동의만 평가하고, 연결 문서의 다른 기능은 구분하세요.`.slice(0, 1000), document_text: documentText }),
      });
      const payload = await apiResponse.json().catch(() => null);
      if (!apiResponse.ok) throw new Error(payload?.detail ?? `AI 분석 요청이 실패했습니다. (${apiResponse.status})`);
      const nextAnalysis = payload as Analysis;
      setAnalysis(nextAnalysis);
      await persistView({ result: scan, analysis: nextAnalysis, error: "", coverage: nextCoverage, incomplete: nextIncomplete, documentStatuses: linked.statuses });
      await chrome.storage.local.remove("pendingScan");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "AI 분석 중 오류가 발생했습니다.";
      setError(message);
      await chrome.storage.local.remove("pendingScan");
    } finally {
      setLoading(false);
    }
  }

  async function analyze() {
    setError(""); setLoading(true); setAnalysis(null); setCoverage(""); setDocumentStatuses([]);
    await chrome.storage.local.remove(["lastView", "pendingScan"]);
    const response = await requestPageScan();
    if (response.type === "PAGE_SCAN_FAILED") {
      setError(response.error.message); setLoading(false); return;
    }
    if (response.type !== "PAGE_SCAN_COMPLETED") {
      setError("페이지 분석 응답을 확인하지 못했습니다."); setLoading(false); return;
    }
    await processScan(response.payload);
  }

  useEffect(() => {
    if (restoreStarted) return;
    restoreStarted = true;
    void chrome.storage.local.get(["pendingScan", "lastView"]).then(async ({ pendingScan, lastView }) => {
      if (pendingScan) {
        setError(""); setLoading(true); setAnalysis(null);
        await processScan(pendingScan as PageScanResult);
        return;
      }
      if (!lastView) return;
      const saved = lastView as SavedView;
      setResult(saved.result); setAnalysis(saved.analysis); setError(saved.error);
      setCoverage(saved.coverage); setIncomplete(saved.incomplete); setDocumentStatuses(saved.documentStatuses ?? []);
    });
  }, []);

  const riskTone = incomplete || !analysis ? "" : analysis.risk_summary.level === "LOW" ? "riskLow" : analysis.risk_summary.level === "MEDIUM" ? "riskMedium" : "riskHigh";
  const detectedFields = fieldLabels(analysis?.extracted.collected_items ?? [], result?.fields ?? []);

  async function showWebResult(event: React.MouseEvent<HTMLAnchorElement>) {
    if (!analysis || !result) return;
    event.preventDefault();
    if (openingWeb) return;
    setOpeningWeb(true);
    try {
      await openWebResult({
        version: 1, id: result.requestId, analysis,
        domain: result.page.domain, scannedAt: result.scannedAt,
        coverage, incomplete, documentStatuses,
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "결과 전달에 실패했습니다.");
    } finally { setOpeningWeb(false); }
  }

  return <main>
    <header><strong>Privacy<span>Lens</span></strong><small>실제 입력값은 읽지 않아요</small></header>
    <section><p className="eyebrow">PAGE CHECK</p><h1>제공하기 전에<br />한번 더 확인하세요.</h1><button onClick={analyze} disabled={loading}>{loading ? "분석 중…" : "현재 페이지 분석"}</button></section>
    {error && <p className="error" role="alert">{error}</p>}
    {result && <div className={`result ${riskTone}`}>
      <h2>{result.page.domain}</h2>
      {coverage && <p className="coverage">{coverage}</p>}
      {documentStatuses.length > 0 && <div className="documentStatuses">{documentStatuses.map((document) => <div key={document.url} className={document.state === "success" ? "documentOk" : "documentFail"}><strong>{document.message}</strong><span title={document.url}>{new URL(document.url).hostname}</span></div>)}</div>}
      {analysis && incomplete ? <div className="risk insufficient"><strong>분석 불충분</strong><p>원문 수집 실패 또는 길이·문서 수 제한으로 일부 내용이 빠져 위험 점수와 등급을 표시하지 않습니다.</p></div> : analysis && <div className="risk"><strong>{analysis.risk_summary.requires_human_review && analysis.risk_summary.score === 0 ? "검토 필요" : riskLabel(analysis.risk_summary.level)}</strong><span>규칙 기반 위험 점수 {analysis.risk_summary.score}</span><p>{analysis.risk_summary.explanation}</p></div>}
      <label>탐지된 개인정보 필드</label><div className="chips">{detectedFields.size ? Array.from(detectedFields.entries()).map(([key, text]) => <span key={key}>{text}</span>) : <em>탐지된 항목 없음</em>}</div>
      <label>동의 항목</label><p>{result.consents.length}개 탐지 · 기본 선택 경고 {result.warnings.length}건</p>
      {analysis && !incomplete && analysis.findings.some((finding) => finding.legal_bases.length) && <><label>관련 법령 근거</label><div className="legalBases">{analysis.findings.flatMap((finding) => finding.legal_bases.map((basis) => <a key={`${finding.rule_id}-${basis.law_name}-${basis.article}`} href={basis.source_url} target="_blank" rel="noreferrer"><strong>{basis.law_name} {basis.article}</strong><span>{basis.title}</span><p><b>핵심 요약</b> {basis.rationale}</p><em>해당 조문 원문 보기 →</em></a>))}</div></>}
      <a className="webLink" href={WEB_SERVICE_URL} target="_blank" rel="noreferrer" onClick={showWebResult} aria-disabled={openingWeb}>{openingWeb ? "결과 전달 중…" : "웹서비스에서 자세히 보기"}</a>
      <footer>요청 ID {result.requestId.slice(0, 12)}…</footer>
    </div>}
    <aside>분석 결과는 법률 판단이 아닌 확인 보조 정보입니다.</aside>
  </main>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
