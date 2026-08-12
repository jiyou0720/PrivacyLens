# PrivacyLens Extension

회원가입 화면의 DOM에서 개인정보 **유형과 화면 표시 상태만** 수집하는 Chrome Manifest V3 확장 프로그램입니다.

## 수집 흐름

1. 팝업이 `requestPageScan()`을 호출하고 `requestId`를 생성합니다.
2. `PAGE_SCAN_STARTED` 메시지를 공유합니다.
3. `chrome.scripting.executeScript`가 현재 HTTP(S) 페이지에서 `scanPage(requestId)`를 실행합니다.
4. 성공 시 `PAGE_SCAN_COMPLETED`, 실패 시 `PAGE_SCAN_FAILED` 메시지를 반환합니다.
5. 채민님 담당 모듈은 `ExtensionMessage`를 구독하거나 `requestPageScan()` 반환값을 사용하면 됩니다.

공용 계약은 `packages/contracts/src/index.ts`의 `PageScanResult`와 `ExtensionMessage`를 사용합니다.

## 개인정보 보호 불변 조건

- `input.value`, `textarea.value`, 선택된 option의 실제 값을 읽지 않습니다.
- 비밀번호 필드는 존재와 유형만 탐지합니다.
- 전체 HTML이나 `outerHTML`을 수집하지 않습니다.
- 근거는 타입, 이름, ID, autocomplete, placeholder, label, ARIA 속성 및 제한된 주변 텍스트만 포함합니다.
- 화면에서 확정할 수 없는 항목은 `unknown`/`needs_review`로 반환합니다.

## 검증

```bash
pnpm --filter @privacylens/extension test
pnpm --filter @privacylens/extension typecheck
pnpm --filter @privacylens/extension build
```
