# PrivacyLens

개인정보 처리방침과 회원가입 화면을 근거 기반으로 분석하고, 실제 개인정보 값 없이 제공 이력을 관리하는 오픈소스 프로젝트입니다.

## 구성

- `apps/extension`: Chrome Manifest V3 확장 프로그램 (React + TypeScript)
- `apps/dashboard`: 개인정보 제공 이력 웹 대시보드 (Next.js)
- `services/api`: 처리방침 구조화 분석 API (FastAPI + Pydantic)
- `packages/contracts`: 프론트엔드 공용 TypeScript 타입
- `packages/rules`: 다크패턴 탐지 규칙

## 빠른 시작

### 프론트엔드

Node.js 20 이상과 pnpm 9 이상이 필요합니다.

```bash
pnpm install
pnpm dev
```

- 대시보드: http://localhost:3000
- 확장 프로그램: `pnpm --filter @privacylens/extension build` 후 `apps/extension/dist`를 Chrome의 압축해제된 확장 프로그램으로 로드

### 분석 API

Python 3.12 이상이 필요합니다.

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

API 문서: http://localhost:8000/docs

## 개인정보 보호 원칙

- 이메일 주소, 전화번호, 이름 등 실제 입력값은 수집하거나 저장하지 않습니다.
- 도메인, 분석 일자, 개인정보 **유형**, 사용자의 확인 상태만 다룹니다.
- 분석 결과에는 근거 원문과 `confirmed`/`needs_review` 상태를 함께 제공합니다.
- 법률 위반 여부나 기업의 실제 개인정보 보유 상태를 단정하지 않습니다.

## 개발 명령

```bash
pnpm lint
pnpm typecheck
pnpm build
cd services/api && pytest
```

## 현재 범위

이 저장소는 MVP 개발을 위한 기본 골격과 데모 UI/API를 제공합니다. 실제 AI 제공자 연동, 인증, PostgreSQL 동기화, 사이트별 어댑터는 후속 단계에서 추가합니다.

## License

Apache-2.0
