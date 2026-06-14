import json

import httpx
import respx

from youbuyfirst_pipeline.realestate_evidence import build_real_estate_evidence_logs
from youbuyfirst_pipeline.realestate_llm_evaluation import (
    GmsOpenAIChatEvaluationClient,
    apply_real_estate_llm_evaluation,
)


@respx.mock
def test_gms_openai_chat_evaluation_client_calls_gms_chat_completions():
    route = respx.post("https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "tone": "mixed",
                                    "summary": "기대와 우려가 함께 나타나는 구간입니다.",
                                    "subtitle": "언급 증가와 전세 쟁점이 함께 확인됩니다.",
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            },
        )
    )
    client = GmsOpenAIChatEvaluationClient(api_key="test-gms-key", model_name="gpt-5-mini")

    evaluation = client.evaluate(_rule_log())

    assert evaluation == {
        "tone": "mixed",
        "summary": "기대와 우려가 함께 나타나는 구간입니다.",
        "subtitle": "언급 증가와 전세 쟁점이 함께 확인됩니다.",
    }
    request = route.calls[0].request
    assert request.headers["authorization"] == "Bearer test-gms-key"
    payload = json.loads(request.content)
    assert payload["model"] == "gpt-5-mini"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["messages"][0]["role"] == "developer"
    assert "매수" in payload["messages"][0]["content"]
    assert payload["messages"][1]["role"] == "user"


def test_apply_real_estate_llm_evaluation_updates_safe_summary_without_changing_evidence_items():
    log = _rule_log()
    updated = apply_real_estate_llm_evaluation(
        log,
        {
            "tone": "watch",
            "summary": "관심이 빠르게 증가했지만 시장 사실 확인이 함께 필요합니다.",
            "subtitle": "전세와 교통 쟁점이 반복적으로 언급됩니다.",
        },
        model_name="gpt-5-mini",
        prompt_version="gms-evidence-v1",
    )

    assert updated["tone"] == "watch"
    assert updated["summary"] == "관심이 빠르게 증가했지만 시장 사실 확인이 함께 필요합니다."
    assert updated["subtitle"] == "전세와 교통 쟁점이 반복적으로 언급됩니다."
    assert updated["modelName"] == "gpt-5-mini"
    assert updated["promptVersion"] == "gms-evidence-v1"
    assert updated["skipReason"] is None
    assert updated["evidenceItems"] == log["evidenceItems"]


def test_apply_real_estate_llm_evaluation_blocks_forbidden_copy_and_keeps_rule_summary():
    log = _rule_log()
    updated = apply_real_estate_llm_evaluation(
        log,
        {
            "tone": "watch",
            "summary": "지금 들어가라, 확정 호재입니다.",
            "subtitle": "수익 보장처럼 보이는 문구입니다.",
        },
        model_name="gpt-5-mini",
        prompt_version="gms-evidence-v1",
    )

    assert updated["summary"] == log["summary"]
    assert updated["subtitle"] == log["subtitle"]
    assert updated["skipReason"] == "forbidden_copy_detected"
    assert "forbidden_copy_detected" in updated["caveats"]
    assert updated["modelName"] == "gpt-5-mini"
    assert updated["promptVersion"] == "gms-evidence-v1"


def _rule_log():
    return build_real_estate_evidence_logs(
        [
            {
                "targetType": "region",
                "targetId": "region-seoul-mapo",
                "windowStart": "2026-06-14T00:00:00Z",
                "windowEnd": "2026-06-14T01:00:00Z",
                "asOf": "2026-06-14T01:02:00Z",
                "mentionCount": 12,
                "previousMentionCount": 6,
                "expectationScore": 48.0,
                "concernScore": 42.0,
                "neutralScore": 10.0,
                "heatScore": 74,
                "confidence": 0.71,
                "sourceCount": 4,
                "sourceSkew": 0.4,
                "coverageStatus": "partial",
                "stale": False,
                "issues": [
                    {"issueKey": "jeonse", "label": "전세", "share": 0.4, "direction": "concern"},
                    {"issueKey": "transport", "label": "교통", "share": 0.3, "direction": "expectation"},
                ],
            }
        ],
        target_id="region-seoul-mapo",
        window_start="2026-06-14T00:00:00Z",
        evaluated_at="2026-06-14T02:00:00Z",
    )[0]
