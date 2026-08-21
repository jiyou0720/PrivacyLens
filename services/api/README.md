# PrivacyLens 분석 API

8월 19일 회의에서 정한 지유 담당 범위인 **규칙 검사 + Ollama 의미 분석**의 1차 구현입니다.
채민 담당인 RAG, 위험등급 계산, 결과 웹 화면은 이 모듈에서 다루지 않습니다.

## 실행

Python 3.12 환경에서:

```bash
pip install -e ".[dev]"
ollama pull qwen3:0.6b
uvicorn app.main:app --reload
```

필요하면 `.env.example`을 `.env`로 복사해 모델과 Ollama 주소를 변경합니다.

## API

`POST /api/v1/analyses/text`

```json
{
  "service_name": "데모 서비스",
  "service_function": "회원 가입 및 계정 관리",
  "document_text": "회원가입을 위해 이메일을 수집합니다..."
}
```

응답에는 LLM 구조화 추출 결과, 버전이 명시된 규칙 결과, 원문에서 확인되지 않은 근거,
사람 검토 필요 여부가 포함됩니다. 총점이나 최종 위험등급은 반환하지 않습니다.

기존 익스텐션 연동용 `POST /v1/analyze`도 그대로 유지됩니다.

## 안전장치

- Ollama JSON Schema structured output을 Pydantic으로 재검증합니다.
- 각 개인정보 항목의 근거 문구가 입력 원문에 실제 존재하는지 확인합니다.
- 확인되지 않은 근거, 민감정보 및 고유식별정보는 사람 검토 대상으로 표시합니다.
- 모델은 법적 위반 여부를 확정하지 않고 필요성 검토 의견만 제공합니다.
