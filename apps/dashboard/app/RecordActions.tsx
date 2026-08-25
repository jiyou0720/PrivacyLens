"use client";

import { useState } from "react";
import type { ServiceRecord } from "@privacylens/contracts";

export function ExportRecordsButton({ records }: { records: ServiceRecord[] }) {
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(records, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "privacylens-records.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }
  return <button type="button" onClick={download}>데이터 내보내기</button>;
}

export function RecordDetails({ record, source }: { record: ServiceRecord; source: string }) {
  const [expanded, setExpanded] = useState(false);
  return <>
    {expanded && <div className="recordDetail"><p>선택 동의: {record.optionalConsent === "accepted" ? "동의" : record.optionalConsent === "rejected" ? "거부" : "해당 없음"}</p><p>기록 출처: {source}</p></div>}
    <div className="recordFoot"><time>{record.recordedAt} 기록</time><button type="button" onClick={() => setExpanded(!expanded)}>{expanded ? "접기 ↑" : "자세히 보기 →"}</button></div>
  </>;
}
