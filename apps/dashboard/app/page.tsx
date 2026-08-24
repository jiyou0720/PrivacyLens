import type { ServiceRecord } from "@privacylens/contracts";
import ConsentAnalysisPanel from "./ConsentAnalysisPanel";
import { ExportRecordsButton, RecordDetails } from "./RecordActions";

const records: ServiceRecord[] = [
  {
    id: "demo-shop",
    serviceName: "데모 쇼핑몰",
    domain: "shop.example.com",
    recordedAt: "2026-07-29",
    dataTypes: ["이메일", "휴대전화번호", "생년월일"],
    optionalConsent: "rejected",
    source: "user_confirmed",
  },
  {
    id: "demo-community",
    serviceName: "데모 커뮤니티",
    domain: "community.example.com",
    recordedAt: "2026-07-25",
    dataTypes: ["이메일", "닉네임"],
    optionalConsent: "not_applicable",
    source: "detected",
  },
];

const sourceLabel = {
  detected: "화면에서 탐지",
  user_confirmed: "사용자 확인",
  policy_stated: "처리방침 명시",
};

export default function Home() {
  const dataTypeCount = new Set(records.flatMap((record) => record.dataTypes)).size;

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#">Privacy<span>Lens</span></a>
        <div className="localBadge"><i /> 로컬 우선 저장</div>
      </header>

      <section className="hero">
        <p className="eyebrow">PRIVACY OVERVIEW</p>
        <h1>내 개인정보의 흐름을<br />한눈에 확인하세요.</h1>
        <p className="heroCopy">실제 개인정보 값은 저장하지 않습니다.<br />어떤 <strong>유형</strong>을 어디에 제공했는지만 안전하게 기록합니다.</p>
      </section>

      <section className="stats" aria-label="요약">
        <article><span>기록된 서비스</span><strong>{records.length}</strong><small>개</small></article>
        <article><span>제공 정보 유형</span><strong>{dataTypeCount}</strong><small>개</small></article>
        <article><span>확인 필요 항목</span><strong className="accent">1</strong><small>건</small></article>
      </section>

      <ConsentAnalysisPanel />

      <section className="records">
        <div className="sectionTitle">
          <div><p className="eyebrow">MY RECORDS</p><h2>서비스별 제공 이력</h2></div>
          <ExportRecordsButton records={records} />
        </div>
        <div className="recordGrid">
          {records.map((record) => (
            <article className="record" key={record.id}>
              <div className="recordHead"><div className="logo">{record.serviceName[3]}</div><div><h3>{record.serviceName}</h3><p>{record.domain}</p></div><span>{sourceLabel[record.source]}</span></div>
              <div className="chips">{record.dataTypes.map((type) => <span key={type}>{type}</span>)}</div>
              <RecordDetails record={record} source={sourceLabel[record.source]} />
            </article>
          ))}
        </div>
      </section>

      <aside className="notice"><strong>Privacy by Design</strong><p>PrivacyLens는 입력한 이메일, 전화번호, 이름 등의 실제 값을 읽거나 저장하지 않습니다.</p></aside>
    </main>
  );
}
