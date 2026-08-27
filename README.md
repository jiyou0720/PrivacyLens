# PrivacyLens

개인정보 처리방침과 회원가입 화면을 근거 기반으로 분석하고, 실제 개인정보 값 없이 제공 이력을 관리하는 오픈소스 프로젝트입니다.

## 서비스 링크

- 웹서비스: [https://privacylens.site](https://privacylens.site)
- 개인정보처리방침: [https://privacylens.site/privacy](https://privacylens.site/privacy)
- GitHub 저장소: [https://github.com/jiyou0720/PrivacyLens](https://github.com/jiyou0720/PrivacyLens)
- 문의: [jiyou.0720.cs@gmail.com](mailto:jiyou.0720.cs@gmail.com)
- Chrome 웹 스토어: 심사 승인 후 링크 추가 예정

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

### Chrome 확장 프로그램 설치

개발 버전은 다음 순서로 설치할 수 있습니다.

1. `pnpm --filter @privacylens/extension build` 실행
2. Chrome에서 `chrome://extensions` 열기
3. 우측 상단의 `개발자 모드` 활성화
4. `압축해제된 확장 프로그램을 로드합니다` 선택
5. `apps/extension/dist` 폴더 선택

Chrome 웹 스토어 업로드용 ZIP은 빌드된 `apps/extension/dist` 폴더의 **내용물**을 압축하여 만듭니다. ZIP을 열었을 때 최상위에 `manifest.json`, `index.html`, `assets/`가 있어야 합니다.

Windows PowerShell 예시:

```powershell
pnpm --filter @privacylens/extension build
Compress-Archive -Path apps/extension/dist/* -DestinationPath PrivacyLens-extension.zip -Force
```

### Chrome 웹 스토어 등록 자료

- [한국어 등록 문구](store-assets/store-listing-ko.md)
- [스토어 아이콘 128×128](store-assets/privacylens-icon-128.png)
- [캡처 화면 1280×800](store-assets/privacylens-screenshot-1280x800.png)
- [작은 프로모션 타일 440×280](store-assets/privacylens-promo-small-440x280.png)
- [마키 프로모션 타일 1400×560](store-assets/privacylens-promo-marquee-1400x560.png)

스토어 등록 시 개인정보처리방침 URL에는 `https://privacylens.site/privacy`를 입력합니다.

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

## 배포

`main` 병합 후 EC2 서버에서 다음 명령으로 웹서비스를 갱신합니다.

```bash
cd ~/PrivacyLens
git switch main
git pull --ff-only origin main
pnpm install --frozen-lockfile
pnpm --filter @privacylens/dashboard build
sudo systemctl restart privacylens-dashboard
```

배포 확인:

```bash
curl -I https://privacylens.site/
curl -I https://privacylens.site/privacy
```

## 현재 범위

현재 버전은 Chrome 확장 프로그램의 회원가입·동의 화면 탐지, 연결 약관 수집, AI 기반 분석, 관련 법령 근거 표시, 웹 대시보드 결과 전달 및 파일·텍스트 분석을 지원합니다. 분석 결과는 법률 판단이 아닌 확인 보조 정보입니다.

## License

Apache-2.0
