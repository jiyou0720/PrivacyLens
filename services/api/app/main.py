from collections import OrderedDict
from hashlib import sha256
from io import BytesIO
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from pypdf import PdfReader

from .analyzer import analyze_policy
from .llm import OpenAIProvider
from .models import AnalyzeRequest, ConsentTextAnalysis, ConsentTextAnalysisRequest, PolicyAnalysis
from .pipeline import analyze_consent_text
from .rag.embeddings import OpenAIEmbeddingProvider
from .rag.retriever import Retriever
from .settings import Settings, get_settings

_analysis_cache: OrderedDict[str, ConsentTextAnalysis] = OrderedDict()
_ANALYSIS_CACHE_SIZE = 256


app = FastAPI(
    title="PrivacyLens Analysis API",
    version="0.3.0",
    description="공개된 개인정보 관련 문서를 근거 기반으로 구조화합니다.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://privacylens.site",
        "https://www.privacylens.site",
    ],
    allow_origin_regex=r"chrome-extension://.*",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_llm_provider(settings: Annotated[Settings, Depends(get_settings)]) -> OpenAIProvider:
    return OpenAIProvider(settings)


def get_retriever(settings: Annotated[Settings, Depends(get_settings)]) -> Retriever:
    return Retriever(OpenAIEmbeddingProvider(settings))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/analyze", response_model=PolicyAnalysis)
def analyze(request: AnalyzeRequest) -> PolicyAnalysis:
    return analyze_policy(request)


def _analysis_cache_key(request: ConsentTextAnalysisRequest, settings: Settings) -> str:
    normalized = "\n".join(
        [
            settings.openai_model,
            settings.openai_review_model,
            settings.prompt_version,
            settings.rule_version,
            request.service_name.strip(),
            (request.service_function or "").strip(),
            " ".join(request.document_text.split()),
        ]
    )
    return sha256(normalized.encode("utf-8")).hexdigest()


async def _run_analysis(
    request: ConsentTextAnalysisRequest,
    settings: Settings,
    provider: OpenAIProvider,
    retriever: Retriever,
) -> ConsentTextAnalysis:
    cache_key = _analysis_cache_key(request, settings)
    cached = _analysis_cache.get(cache_key)
    if cached is not None:
        _analysis_cache.move_to_end(cache_key)
        return cached.model_copy(deep=True)

    try:
        await retriever.initialize()
        result = await analyze_consent_text(
            request=request,
            provider=provider,
            settings=settings,
            retriever=retriever,
        )
        _analysis_cache[cache_key] = result.model_copy(deep=True)
        _analysis_cache.move_to_end(cache_key)
        while len(_analysis_cache) > _ANALYSIS_CACHE_SIZE:
            _analysis_cache.popitem(last=False)
        return result
    except (httpx.HTTPError, ValidationError, KeyError, ValueError, RuntimeError) as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=503,
            detail="AI 분석 결과를 가져오거나 검증하지 못했습니다.",
        ) from exc


@app.post("/api/v1/analyses/text", response_model=ConsentTextAnalysis)
async def analyze_text(
    request: ConsentTextAnalysisRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    provider: Annotated[OpenAIProvider, Depends(get_llm_provider)],
    retriever: Annotated[Retriever, Depends(get_retriever)],
) -> ConsentTextAnalysis:
    return await _run_analysis(request, settings, provider, retriever)


def _extract_document_text(filename: str, content: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix in {"txt", "md"}:
        try:
            return content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return content.decode("cp949")
    if suffix == "pdf":
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise HTTPException(status_code=400, detail="TXT, MD, PDF 파일만 업로드할 수 있습니다.")


@app.post("/api/v1/analyses/file", response_model=ConsentTextAnalysis)
async def analyze_file(
    service_name: Annotated[str, Form(min_length=1, max_length=100)],
    settings: Annotated[Settings, Depends(get_settings)],
    provider: Annotated[OpenAIProvider, Depends(get_llm_provider)],
    retriever: Annotated[Retriever, Depends(get_retriever)],
    file: Annotated[UploadFile, File()],
    service_function: Annotated[str | None, Form(max_length=1000)] = None,
) -> ConsentTextAnalysis:
    content = await file.read(10_000_001)
    if len(content) > 10_000_000:
        raise HTTPException(status_code=413, detail="파일은 10MB 이하만 업로드할 수 있습니다.")
    document_text = _extract_document_text(file.filename or "", content).strip()
    if len(document_text) < 20:
        raise HTTPException(status_code=400, detail="파일에서 분석 가능한 텍스트를 찾지 못했습니다.")
    request = ConsentTextAnalysisRequest(
        service_name=service_name,
        service_function=service_function or None,
        document_text=document_text[:100_000],
    )
    return await _run_analysis(request, settings, provider, retriever)
