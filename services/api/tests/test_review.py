import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.llm import OpenAIProvider
from app.main import _analysis_cache_key
from app.models import ConsentTextAnalysisRequest, ExtractedConsent, PersonalDataItem
from app.settings import Settings


def test_terra_receives_source_and_draft_and_returns_corrected_result():
    provider = OpenAIProvider(Settings(openai_api_key="test"))
    draft = ExtractedConsent(purposes=["초안"], collected_items=[PersonalDataItem(
        original_name="건강정보", normalized_name="건강정보", sensitive=True,
        reason="검토", evidence_text="건강정보",
    )])
    corrected = ExtractedConsent(purposes=["수정"])
    parse = AsyncMock(side_effect=[
        SimpleNamespace(output_parsed=draft), SimpleNamespace(output_parsed=corrected),
    ])
    provider.client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    result = asyncio.run(provider.extract("원문 개인정보 동의", "회원가입", "참고 법령"))
    assert result is corrected
    assert parse.call_args_list[0].kwargs["model"] == "gpt-5.6-luna"
    review = parse.call_args_list[1].kwargs
    assert review["model"] == "gpt-5.6-terra"
    assert all(text in review["input"] for text in ["원문 개인정보 동의", "초안", "참고 법령"])


def test_empty_review_is_not_silently_replaced_by_luna():
    provider = OpenAIProvider(Settings(openai_api_key="test"))
    provider.client = SimpleNamespace(responses=SimpleNamespace(parse=AsyncMock(side_effect=[
        SimpleNamespace(output_parsed=ExtractedConsent(third_party_provision_present=True)), SimpleNamespace(output_parsed=None),
    ])))
    with pytest.raises(ValueError, match="Terra"):
        asyncio.run(provider.extract("원문", None))


def test_low_risk_draft_skips_terra_for_lower_latency():
    provider = OpenAIProvider(Settings(openai_api_key="test"))
    parse = AsyncMock(return_value=SimpleNamespace(output_parsed=ExtractedConsent(purposes=["회원가입"])))
    provider.client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    result = asyncio.run(provider.extract("원문", "회원가입"))
    assert result.purposes == ["회원가입"]
    assert parse.await_count == 1


def test_explicit_unique_identifier_requests_terra_review():
    extracted = ExtractedConsent(collected_items=[PersonalDataItem(
        original_name="주민등록번호", normalized_name="주민등록번호",
        reason="고유식별정보", evidence_text="주민등록번호",
    )])
    assert OpenAIProvider._needs_terra_review(extracted)


def test_review_configuration_invalidates_cache():
    request = ConsentTextAnalysisRequest(service_name="테스트", document_text="회원가입을 위한 원문 개인정보 동의서 테스트입니다.")
    single = Settings(openai_api_key="test", openai_review_model="")
    dual = Settings(openai_api_key="test", openai_review_model="gpt-5.6-terra")
    assert _analysis_cache_key(request, single) != _analysis_cache_key(request, dual)
