import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "개인정보처리방침 | PrivacyLens",
  description: "PrivacyLens 웹서비스 및 Chrome 확장 프로그램 개인정보처리방침",
};

export default function PrivacyPolicy() {
  return (
    <main>
      <header className="topbar">
        <a className="brand" href="/">Privacy<span>Lens</span></a>
        <a className="policyHome" href="/">서비스로 돌아가기</a>
      </header>
      <article className="policyPage">
        <p className="eyebrow">PRIVACY POLICY</p>
        <h1>개인정보처리방침</h1>
        <p className="policyUpdated">시행일: 2026년 8월 27일</p>

        <p>PrivacyLens(이하 “서비스”)는 사용자가 회원가입 및 개인정보 동의 화면을 확인할 수 있도록 돕는 웹서비스와 Chrome 확장 프로그램을 제공합니다. 서비스는 사용자의 실제 입력값을 읽거나 저장하지 않습니다.</p>

        <h2>1. 처리하는 정보</h2>
        <p>사용자가 직접 ‘현재 페이지 분석’을 실행한 경우 다음 정보를 처리합니다.</p>
        <ul>
          <li>현재 페이지의 URL, 도메인 및 제목</li>
          <li>페이지에 표시된 입력 필드의 종류와 동의 항목</li>
          <li>공개된 이용약관 및 개인정보 처리방침의 텍스트와 링크</li>
          <li>분석 결과, 위험 점수, 관련 법령 근거 및 요청 식별자</li>
        </ul>
        <p>사용자가 입력한 이름, 이메일 주소, 전화번호, 비밀번호, 결제정보 등의 실제 값은 읽거나 수집하지 않습니다. 방문 기록 전체, 클릭 기록, 키 입력 내용도 수집하지 않습니다.</p>

        <h2>2. 처리 목적</h2>
        <ul>
          <li>개인정보 입력 필드와 동의 항목 탐지</li>
          <li>공개된 동의문과 약관의 위험 요소 분석</li>
          <li>관련 개인정보 보호법 조항 및 확인 필요 사항 제공</li>
          <li>분석 진행 상태 복원 및 결과 표시</li>
        </ul>

        <h2>3. 정보의 전송 및 제3자 처리</h2>
        <p>분석을 위해 공개된 동의문 및 약관 텍스트와 페이지 제목이 PrivacyLens 서버로 전송됩니다. 해당 내용은 분석 결과 생성을 위해 OpenAI API에서 처리될 수 있습니다. 서비스는 사용자 데이터를 판매하지 않으며, 광고나 신용도 평가 또는 대출 목적으로 사용하지 않습니다.</p>

        <h2>4. 보관 및 삭제</h2>
        <p>확장 프로그램은 진행 중인 분석 상태와 마지막 분석 결과를 Chrome 로컬 저장소에 임시로 보관합니다. 사용자는 확장 프로그램을 삭제하거나 브라우저의 확장 프로그램 데이터를 삭제하여 이를 제거할 수 있습니다. PrivacyLens 서버는 분석 요청을 처리하는 데 필요한 범위에서 정보를 사용하며 별도의 사용자 계정별 분석 이력을 구축하지 않습니다.</p>

        <h2>5. 권한 사용</h2>
        <ul>
          <li><strong>activeTab 및 scripting:</strong> 사용자가 요청한 현재 페이지를 분석합니다.</li>
          <li><strong>storage:</strong> 팝업이 닫힌 후에도 진행 상태와 마지막 결과를 복원합니다.</li>
          <li><strong>호스트 권한:</strong> PrivacyLens 분석 API에 연결하고, 사용자가 허용한 경우 연결된 공개 약관 문서를 불러옵니다.</li>
        </ul>
        <p>모든 실행 코드는 확장 프로그램 패키지에 포함되어 있으며 원격 코드를 내려받아 실행하지 않습니다.</p>

        <h2>6. 이용자의 선택</h2>
        <p>분석은 사용자가 버튼을 눌렀을 때만 시작됩니다. 연결 문서 접근 권한은 Chrome의 권한 화면에서 거부하거나 추후 철회할 수 있습니다.</p>

        <h2>7. 방침의 변경</h2>
        <p>서비스 기능이나 관련 법령이 변경되면 이 방침을 수정할 수 있으며, 중요한 변경 사항은 서비스 또는 확장 프로그램을 통해 안내합니다.</p>

        <h2>8. 문의</h2>
        <p>개인정보 관련 문의: <a href="mailto:jiyou060720@gmail.com">jiyou060720@gmail.com</a></p>
      </article>
    </main>
  );
}
