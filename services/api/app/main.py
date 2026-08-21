from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .analyzer import analyze_policy
from .llm import OllamaProvider
from .models import AnalyzeRequest, ConsentTextAnalysis, ConsentTextAnalysisRequest, PolicyAnalysis
from .pipeline import analyze_consent_text
from .settings import Settings, get_settings

app = FastAPI(
    title="PrivacyLens Analysis API",
    version="0.2.0",
    description="공개된 개인정보 관련 문서를 근거 기반으로 구조화합니다.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_llm_provider(settings: Annotated[Settings, Depends(get_settings)]) -> OllamaProvider:
    return OllamaProvider(settings)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/analyze", response_model=PolicyAnalysis)
def analyze(request: AnalyzeRequest) -> PolicyAnalysis:
    return analyze_policy(request)


@app.post("/api/v1/analyses/text", response_model=ConsentTextAnalysis)
async def analyze_text(
    request: ConsentTextAnalysisRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    provider: Annotated[OllamaProvider, Depends(get_llm_provider)],
) -> ConsentTextAnalysis:
    try:
        return await analyze_consent_text(request, provider, settings)
    except (httpx.HTTPError, ValidationError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Ollama 분석 결과를 가져오거나 검증하지 못했습니다.",
        ) from exc
