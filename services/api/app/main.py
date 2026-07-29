from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .analyzer import analyze_policy
from .models import AnalyzeRequest, PolicyAnalysis

app = FastAPI(
    title="PrivacyLens Analysis API",
    version="0.1.0",
    description="공개된 개인정보 관련 문서를 근거 기반으로 구조화합니다.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/analyze", response_model=PolicyAnalysis)
def analyze(request: AnalyzeRequest) -> PolicyAnalysis:
    return analyze_policy(request)
