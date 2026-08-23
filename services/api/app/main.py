from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .analyzer import analyze_policy
from .llm import OllamaProvider
from .models import (
    AnalyzeRequest,
    ConsentTextAnalysis,
    ConsentTextAnalysisRequest,
    PolicyAnalysis,
)
from .pipeline import analyze_consent_text
from .settings import Settings, get_settings
from .rag.embeddings import OllamaEmbeddingProvider
from .rag.retriever import Retriever


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


# ============================================================
# LLM Provider
# ============================================================

def get_llm_provider(
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
) -> OllamaProvider:
    return OllamaProvider(settings)


# ============================================================
# RAG Retriever
# ============================================================

def get_retriever(
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
) -> Retriever:

    embedding_provider = OllamaEmbeddingProvider(
        settings
    )

    return Retriever(
        embedding_provider
    )


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ============================================================
# 기존 Policy Analysis API
# ============================================================

@app.post(
    "/v1/analyze",
    response_model=PolicyAnalysis,
)
def analyze(
    request: AnalyzeRequest,
) -> PolicyAnalysis:
    return analyze_policy(request)


# ============================================================
# Consent Text Analysis
# Rule Engine + Ollama + RAG + Risk Engine
# ============================================================

@app.post(
    "/api/v1/analyses/text",
    response_model=ConsentTextAnalysis,
)
async def analyze_text(
    request: ConsentTextAnalysisRequest,
    settings: Annotated[
        Settings,
        Depends(get_settings),
    ],
    provider: Annotated[
        OllamaProvider,
        Depends(get_llm_provider),
    ],
    retriever: Annotated[
        Retriever,
        Depends(get_retriever),
    ],
) -> ConsentTextAnalysis:

    try:

        # RAG Retriever 초기화
        await retriever.initialize()

        # 전체 분석 Pipeline 실행
        return await analyze_consent_text(
            request=request,
            provider=provider,
            settings=settings,
            retriever=retriever,
        )

    except (
        httpx.HTTPError,
        ValidationError,
        KeyError,
        ValueError,
    ) as exc:

        print(f"[ERROR] {type(exc).__name__}: {exc}")

        raise HTTPException(
            status_code=503,
            detail="AI 분석 결과를 가져오거나 검증하지 못했습니다.",
        ) from exc