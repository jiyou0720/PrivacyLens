"use client";

import { useEffect, useState } from "react";
import { decodeExtensionResultHash, parseExtensionResult, type ExtensionResult } from "./extensionResult";
import type { ServiceRecord } from "@privacylens/contracts";
import ConsentAnalysisPanel, { type Analysis } from "./ConsentAnalysisPanel";
import { ExportRecordsButton, RecordDetails } from "./RecordActions";

const sourceLabel = { detected: "화면에서 탐지", user_confirmed: "사용자 확인", policy_stated: "처리방침 명시" };
type AnalysisRecord = ServiceRecord & { riskLevel: string; requiresReview: boolean; result: ExtensionResult };
const riskLabel = (level: string) => level === "LOW" ? "확인된 위험 낮음" : level;

export default function Home() {
  const [records, setRecords] = useState<AnalysisRecord[]>([]);
  const [selected, setSelected] = useState<ExtensionResult | null>(null);
  const [importError, setImportError] = useState("");
  useEffect(() => {
    function receive() {
      const match = /^#result=([A-Za-z0-9_-]+)$/.exec(location.hash);
      if (!match) return;
      try {
        const raw = decodeExtensionResultHash(match[1]);
        const result = parseExtensionResult(raw);
        setSelected(result); addRecord(result.analysis, result); setImportError("");
      } catch (error) {
        setImportError(error instanceof Error ? error.message : "결과를 불러오지 못했습니다.");
      } finally {
        history.replaceState(null, "", location.pathname + location.search);
      }
    }
    receive();
    window.addEventListener("hashchange", receive);
    return () => window.removeEventListener("hashchange", receive);
  }, []);
  const dataTypeCount = new Set(records.flatMap((record) => record.dataTypes)).size;
  const reviewCount = records.filter((record) => record.requiresReview).length;

  function addRecord(analysis: Analysis, imported?: ExtensionResult) {
    const result: ExtensionResult = imported ?? {
      version: 1, id: crypto.randomUUID(), analysis, domain: "직접 분석한 동의문",
      scannedAt: new Date().toISOString(), coverage: "직접 입력·업로드 분석",
      incomplete: false, documentStatuses: [],
    };
    const record: AnalysisRecord = {
      id: result.id,
      serviceName: analysis.service_name,
      domain: result.domain,
      recordedAt: result.scannedAt,
      dataTypes: Array.from(new Set(analysis.extracted.collected_items.map((item) => item.normalized_name))),
      optionalConsent: "not_applicable",
      source: "policy_stated",
      riskLevel: result.incomplete ? "분석 불충분" : analysis.risk_summary.level,
      requiresReview: result.incomplete || ["HIGH", "CRITICAL"].includes(analysis.risk_summary.level),
      result,
    };
    setRecords((current) => [record, ...current.filter((item) => item.id !== record.id)]);
  }

  return (
    <main>
      <header className="topbar"><a className="brand" href="#">Privacy<span>Lens</span></a><div className="localBadge"><i /> 로컬 우선 저장</div></header>
      <section className="hero"><p className="eyebrow">PRIVACY OVERVIEW</p><h1>내 개인정보의 흐름을<br />한눈에 확인하세요.</h1><p className="heroCopy">실제 개인정보 값은 저장하지 않습니다.<br />어떤 <strong>유형</strong>을 어디에 제공했는지만 안전하게 기록합니다.</p></section>
      <section className="stats" aria-label="요약">
        <article><span>기록된 서비스</span><strong>{records.length}</strong><small>개</small></article>
        <article><span>제공 정보 유형</span><strong>{dataTypeCount}</strong><small>개</small></article>
        <article><span>확인 필요 항목</span><strong className="accent">{reviewCount}</strong><small>건</small></article>
      </section>
      {importError && <aside className="notice" role="alert">{importError}</aside>}
      <ConsentAnalysisPanel onAnalyzed={addRecord} selected={selected} />
      <section className="records">
        <div className="sectionTitle"><div><p className="eyebrow">MY RECORDS</p><h2>서비스별 제공 이력</h2></div><ExportRecordsButton records={records} /></div>
        {records.length === 0 ? <article className="record"><p>현재 세션에서 분석한 서비스가 없습니다.</p></article> : <div className="recordGrid">
          {records.map((record) => <article className="record" key={record.id}>
            <div className="recordHead"><div className="logo">{record.serviceName[0]}</div><div><h3>{record.serviceName}</h3><p>{record.domain}</p></div><span className={record.riskLevel === "LOW" ? "lowBadge" : ["MEDIUM", "분석 불충분"].includes(record.riskLevel) ? "mediumBadge" : "criticalBadge"}>{riskLabel(record.riskLevel)}</span></div>
            <div className="chips">{record.dataTypes.map((type) => <span key={type}>{type}</span>)}</div>
            <RecordDetails record={record} source={sourceLabel[record.source]} />
            <button type="button" onClick={() => setSelected({ ...record.result })}>분석 결과 다시 보기</button>
          </article>)}
        </div>}
      </section>
      <aside className="notice"><strong>Privacy by Design</strong><p>PrivacyLens는 입력한 이메일, 전화번호, 이름 등의 실제 값을 읽거나 저장하지 않습니다.</p></aside>
    </main>
  );
}
