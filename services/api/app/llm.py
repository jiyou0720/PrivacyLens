from __future__ import annotations

from typing import Protocol

from openai import AsyncOpenAI

from .models import ExtractedConsent
from .settings import Settings


class LLMProvider(Protocol):
    """LLM Provider 공통 인터페이스"""

    model_name: str

    async def extract(
        self,
        document_text: str,
        service_function: str | None,
        rag_content: str | None = None,
    ) -> ExtractedConsent:
        ...


SYSTEM_PROMPT = """
당신은 개인정보 동의서 구조화 분석기입니다.

사용자가 제공한 개인정보 처리 동의서에서 다음 정보를 추출합니다.

- 수집 목적
- 수집하는 개인정보 항목
- 보유 및 이용 기간
- 동의 거부권
- 동의 거부 시 불이익
- 각 개인정보 항목의 필요성
- 민감정보 여부

반드시 JSON 형식으로만 응답하세요.

추측하지 마세요.
문서에 명확하게 존재하지 않는 정보는 만들지 마세요.
각 개인정보 항목의 evidence_text는 반드시 원문에서 그대로 가져오세요.
"""


class OpenAIProvider:
    """OpenAI GPT 기반 개인정보 동의서 분석 Provider"""

    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )

        self.model_name = settings.openai_model

    async def extract(
        self,
        document_text: str,
        service_function: str | None,
        rag_content: str | None = None,
    ) -> ExtractedConsent:

        user_prompt = f"""
서비스 기능:
{service_function or "알 수 없음"}

개인정보 동의서 원문:
{document_text}

관련 법령 참고자료:
{rag_content or "제공되지 않음"}

법령 참고자료는 해석의 보조자료로만 사용하고, 개인정보 항목의 evidence_text에는 반드시 동의서 원문만 인용하세요.

위 문서를 분석하여 개인정보 동의 정보를 JSON으로 추출하세요.
"""

        response = await self.client.responses.parse(
            model=self.model_name,
            instructions=SYSTEM_PROMPT,
            input=user_prompt,
            text_format=ExtractedConsent,
        )

        if response.output_parsed is None:
            raise ValueError("OpenAI에서 구조화된 분석 결과를 받지 못했습니다.")

        return response.output_parsed