import json
from datetime import datetime, timezone

import pytest

from youbuyfirst_pipeline.realestate_daily_briefing import (
    GmsAnthropicMessagesDailyBriefingClient,
    apply_daily_briefing_llm_generation,
    build_daily_briefing_input_pack,
    build_rule_based_daily_briefing,
)
from youbuyfirst_pipeline.realestate_daily_scheduler import RealEstateDailyBriefingRefreshJob


def _now() -> datetime:
    return datetime(2026, 6, 24, 0, 30, tzinfo=timezone.utc)


def test_build_daily_briefing_input_pack_uses_internal_lenses_without_time_window_labels():
    pack = build_daily_briefing_input_pack(
        generated_at=_now(),
        market_facts=[
            {
                "targetId": "region-seoul",
                "factType": "jeonse_pressure",
                "observedAt": "2026-06-23",
                "valueJson": {"label": "수도권 전세 압력"},
                "provider": "reb_stat",
            }
        ],
        map_targets=[
            {
                "targetId": "region-gyeonggi-south",
                "displayName": "경기 남부",
                "periods": {
                    "month": {
                        "changePct": 0.82,
                        "sampleCount": 120,
                        "provider": "molit",
                        "dataStatus": "ok",
                    }
                },
            }
        ],
        content_items=[
            {
                "contentId": "news-policy-1",
                "title": "경기 남부 공급 정책 점검",
                "url": "https://example.com/policy",
                "contentType": "news",
                "publishedAt": "2026-06-23T01:00:00Z",
            }
        ],
        curated_items=[
            {
                "sourceItemId": "manual-report-1",
                "sourceType": "report",
                "title": "서울 동남권 거래 회복 리포트",
                "url": "https://example.com/report",
                "lens": "repeated_flow",
                "importance": 0.9,
            }
        ],
    )

    assert pack["briefingDate"] == "2026-06-24"
    assert [lens["id"] for lens in pack["analysisLenses"]] == [
        "new_variables",
        "repeated_flow",
        "accumulated_direction",
        "regional_importance",
    ]
    assert pack["sourceItems"][0]["sourceItemId"] == "manual-report-1"
    assert any(candidate["lens"] == "regional_importance" for candidate in pack["candidates"])
    serialized = json.dumps(pack, ensure_ascii=False)
    for forbidden_label in ("24시간", "7일", "1개월", "3개월"):
        assert forbidden_label not in serialized


def test_build_daily_briefing_input_pack_filters_low_signal_personal_news_candidates():
    pack = build_daily_briefing_input_pack(
        generated_at=_now(),
        content_items=[
            {
                "contentId": "noisy-personal-news",
                "title": "홍석현, 누나 홍라희에 300억 차입…이천·남양주 가족 부동산 73건 담보로 묶였다",
                "url": "https://example.com/noisy",
                "contentType": "news",
            },
            {
                "contentId": "policy-market-news",
                "title": "정부 부동산 세제 개편 시동…임대 매물 잠김 우려",
                "url": "https://example.com/policy",
                "contentType": "news",
            },
        ],
    )

    titles = [candidate["title"] for candidate in pack["candidates"]]
    assert "정부 부동산 세제 개편 시동…임대 매물 잠김 우려" in titles
    assert all("홍석현" not in title for title in titles)


def test_build_daily_briefing_input_pack_prefers_canonical_urls_and_column_rules():
    pack = build_daily_briefing_input_pack(
        generated_at=_now(),
        content_items=[
            {
                "contentId": "column-news-1",
                "title": "부동산 세제 개편, 과욕 버리고 단순화하라 [전성인 칼럼] - 한겨레",
                "url": "https://news.google.com/rss/articles/wrapped?oc=5",
                "canonicalUrl": "https://www.hani.co.kr/arti/opinion/column/example.html",
                "domain": "www.hani.co.kr",
                "contentType": "news",
            }
        ],
    )

    candidate = pack["candidates"][0]
    assert candidate["url"] == "https://www.hani.co.kr/arti/opinion/column/example.html"
    assert candidate["domain"] == "www.hani.co.kr"
    assert pack["writingRules"]["tone"] == "건조한 금융권 리서치 브리프"
    assert pack["writingRules"]["minimumBodyCharacters"] >= 650
    assert pack["writingRules"]["targetBodyCharacters"] >= 900
    assert "나열" in pack["writingRules"]["avoid"]


def test_build_daily_briefing_input_pack_prefers_week_or_month_region_changes():
    pack = build_daily_briefing_input_pack(
        generated_at=_now(),
        map_targets=[
            {
                "targetId": "region-seoul",
                "displayName": "서울특별시",
                "periods": {
                    "year": {"changePct": 10.97},
                    "month": {"changePct": 0.82},
                    "week": {"changePct": 0.18},
                },
            },
            {
                "targetId": "region-busan",
                "displayName": "부산광역시",
                "periods": {
                    "year": {"changePct": -6.2},
                    "quarter": {"changePct": -1.8},
                },
            },
        ],
    )

    region_candidates = [
        candidate for candidate in pack["candidates"]
        if candidate["lens"] == "regional_importance"
    ]
    seoul = next(candidate for candidate in region_candidates if candidate["targetId"] == "region-seoul")
    busan = next(candidate for candidate in region_candidates if candidate["targetId"] == "region-busan")
    assert seoul["summary"] == "단기 변화율 +0.18%"
    assert seoul["period"] == "week"
    assert "10.97" not in json.dumps(seoul, ensure_ascii=False)
    assert busan["summary"] == ""


def test_anthropic_daily_briefing_client_uses_gms_messages_endpoint(monkeypatch):
    captured = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "title": "오늘의 부동산 시장 브리핑",
                                "summaryHeadlines": [
                                    "서울 변동 확대",
                                    "세제 개편 파장",
                                    "지역별 온도차",
                                ],
                                "sections": {
                                    "오늘의 핵심 흐름": "서울과 정책 이슈를 함께 봅니다.",
                                    "주목할 지역과 이유": "서울과 경기 흐름을 확인합니다.",
                                    "시장 변수": "세제와 공급 일정이 변수입니다.",
                                    "관련 뉴스·리포트": "뉴스룸 원문을 확인합니다.",
                                },
                                "focusRegions": [],
                                "sourceItems": [],
                            },
                            ensure_ascii=False,
                        ),
                    }
                ]
            }

    class _FakeClient:
        def __init__(self, *, timeout):
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def post(self, url, *, headers, json):
            captured["url"] = url
            captured["headers"] = headers
            captured["payload"] = json
            return _FakeResponse()

    monkeypatch.setattr(
        "youbuyfirst_pipeline.realestate_daily_briefing.httpx.Client",
        _FakeClient,
    )

    client = GmsAnthropicMessagesDailyBriefingClient(
        "secret-key",
        base_url="https://gms.ssafy.io/gmsapi/api.anthropic.com/v1",
        model_name="claude-opus-4-8",
        timeout_seconds=77,
        max_tokens=4096,
    )

    result = client.generate({"briefingDate": "2026-06-24", "candidates": []})

    assert result["summaryHeadlines"][0] == "서울 변동 확대"
    assert captured["url"] == "https://gms.ssafy.io/gmsapi/api.anthropic.com/v1/messages"
    assert captured["headers"]["x-api-key"] == "secret-key"
    assert captured["headers"]["anthropic-version"] == "2023-06-01"
    assert captured["payload"]["model"] == "claude-opus-4-8"
    assert captured["payload"]["max_tokens"] == 4096
    assert captured["payload"]["system"]
    assert captured["payload"]["messages"][0]["role"] == "user"


def test_apply_daily_briefing_generation_builds_shared_dashboard_payload():
    pack = build_daily_briefing_input_pack(
        generated_at=_now(),
        curated_items=[
            {
                "sourceItemId": "manual-report-1",
                "sourceType": "report",
                "title": "서울 동남권 거래 회복 리포트",
                "url": "https://example.com/report",
                "lens": "repeated_flow",
            }
        ],
    )
    generated = {
        "title": "오늘의 부동산 시장 브리핑",
        "summaryHeadlines": [
            "수도권 전세 압력 재부각",
            "서울 동남권 거래 회복 흐름",
            "경기 남부 공급·정책 이슈 집중",
        ],
        "sections": [
            {
                "sectionId": "flow",
                "title": "오늘의 핵심 흐름",
                "body": (
                    "전세 압력과 거래 회복 흐름이 같은 방향으로 움직이는지가 오늘 브리핑의 출발점입니다. "
                    "단기 뉴스만 떼어 보면 세제 논의와 공급 일정이 각각 분리된 사건처럼 보이지만, 실제 시장 체감은 "
                    "전세 가격 부담, 매매 대기 수요, 입주 물량 기대가 한꺼번에 겹치며 형성됩니다. 따라서 이번 흐름은 "
                    "가격 상승 단정이 아니라 수도권 핵심 생활권의 수급 압력이 다시 논의의 중심으로 올라왔다는 신호로 읽어야 합니다."
                ),
            },
            {
                "sectionId": "regions",
                "title": "주목할 지역과 이유",
                "body": (
                    "서울 동남권은 거래 재개 기대와 전세 부담이 함께 언급되는 권역이고, 경기 남부는 공급·교통·산업 이슈가 "
                    "동시에 붙어 시장 해석의 밀도가 높습니다. 두 권역은 같은 수도권 안에서도 수요의 성격이 다르기 때문에 "
                    "단순 등락률보다 거래 회복의 지속성, 전세 수요 이동, 신규 공급 일정의 체감 시차를 함께 봐야 합니다."
                ),
            },
            {
                "sectionId": "variables",
                "title": "시장 변수",
                "body": (
                    "가장 큰 변수는 세제 개편 논의가 매물 출회와 임대시장 기대를 어떻게 바꾸는지입니다. 여기에 착공·준공 "
                    "일정이 늦어질 경우 전세 압력이 더 오래 남을 수 있고, 반대로 입주 물량이 확인되는 지역은 같은 정책 변수 "
                    "아래에서도 체감 강도가 낮아질 수 있습니다. 변수의 핵심은 방향 단정이 아니라 정책과 공급이 수요 심리를 "
                    "어느 시점에 다시 조정하느냐입니다."
                ),
            },
            {
                "sectionId": "sources",
                "title": "관련 뉴스·리포트",
                "body": (
                    "이번 브리핑은 세제 개편 보도, 수도권 전세 관련 기사, 지역별 거래·공급 흐름 자료를 함께 묶어 작성했습니다. "
                    "개별 기사 하나를 결론으로 삼기보다 여러 출처에서 반복되는 논점을 교차 확인하는 방식이 적절합니다. "
                    "아래 근거는 판단의 확정치가 아니라 어떤 재료가 오늘의 시장 해석에 쓰였는지 확인하기 위한 출처 목록입니다."
                ),
            },
        ],
        "focusRegions": [
            {
                "targetId": "region-seoul",
                "label": "서울",
                "reason": "거래 회복 흐름",
            }
        ],
        "sourceItems": [
            {
                "sourceItemId": "manual-report-1",
                "sourceType": "report",
                "title": "서울 동남권 거래 회복 리포트",
                "url": "https://example.com/report",
            }
        ],
    }

    payload = apply_daily_briefing_llm_generation(
        pack,
        generated,
        model_name="claude opus 4 8",
        prompt_version="daily-briefing-v1",
    )

    assert payload["briefingId"] == "daily-briefing-20260624-v1"
    assert payload["summaryHeadlines"] == generated["summaryHeadlines"]
    assert [section["title"] for section in payload["sections"]] == [
        "오늘의 핵심 흐름",
        "주목할 지역과 이유",
        "시장 변수",
        "관련 뉴스·리포트",
    ]
    assert payload["modelName"] == "claude opus 4 8"
    assert payload["promptVersion"] == "daily-briefing-v1"
    assert payload["sourceItems"][0]["displayOrder"] == 1


def test_apply_daily_briefing_generation_accepts_object_sections_and_focus_region_ids():
    pack = build_daily_briefing_input_pack(
        generated_at=_now(),
        map_targets=[
            {
                "targetId": "region-seoul",
                "displayName": "서울특별시",
                "periods": {"month": {"changePct": 10.97}},
            }
        ],
    )
    generated = {
        "title": "오늘의 부동산 시장 브리핑",
        "summaryHeadlines": [
            "서울 지역 흐름",
            "수도권 변수 집중",
            "정책 이슈 점검",
        ],
        "sections": {
            "오늘의 핵심 흐름": (
                "서울 중심의 지역별 온도차는 단기 가격 신호 하나보다 수급 압력과 정책 기대가 함께 반영된 결과로 봐야 합니다. "
                "특히 수도권 핵심 권역에서 전세 부담과 매매 대기 수요가 동시에 거론되면, 시장은 개별 호재보다 위험 회피와 "
                "선호 지역 압축이라는 방향으로 반응할 가능성이 커집니다. 따라서 오늘의 핵심은 상승 단정이 아니라 지역 간 "
                "체감 격차가 다시 커지는 배경을 확인하는 데 있습니다."
            ),
            "주목할 지역과 이유": (
                "서울은 정책과 거래 심리가 가장 먼저 결합되는 시장이고, 경기 남부는 산업·교통·공급 재료가 겹쳐 해석할 요소가 많습니다. "
                "두 지역 모두 단순 순위보다 왜 관심이 붙는지, 그 관심이 실거래·전세·공급 중 어디에서 반복되는지 확인해야 합니다. "
                "이 구분이 있어야 일시적 뉴스 노출과 실제 시장 압력을 나눠 볼 수 있습니다."
            ),
            "시장 변수": (
                "세제와 공급 일정은 같은 방향으로만 작동하지 않습니다. 세제 논의가 매물 대기 심리를 키우는 동안 공급 일정은 "
                "지역별 체감 압력을 낮추거나 높일 수 있습니다. 지금 필요한 판단은 특정 정책의 즉시 효과보다 전세·거래·공급 "
                "자료가 같은 방향으로 누적되는지 확인하는 것입니다."
            ),
            "관련 뉴스·리포트": (
                "뉴스룸과 공식 리포트는 오늘의 해석을 만든 재료로 연결됩니다. 개별 보도의 표현을 그대로 결론화하지 않고, "
                "정책 논의와 지역 지표가 반복해서 만나는 지점을 중심으로 확인해야 합니다. 근거 링크는 추가 검토를 위한 "
                "출처이며 투자 행동을 지시하는 신호가 아닙니다."
            ),
        },
        "focusRegions": [
            {"candidateId": "region-seoul", "title": "서울특별시 지역 흐름", "reason": "변화율 +10.97%"}
        ],
        "sourceItems": [
            {
                "candidateId": "region-seoul",
                "sourceType": "map_layer",
                "title": "서울특별시 지역 흐름",
            }
        ],
    }

    payload = apply_daily_briefing_llm_generation(
        pack,
        generated,
        model_name="gpt-5-mini",
        prompt_version="daily-briefing-v1",
    )

    assert [section["title"] for section in payload["sections"]] == [
        "오늘의 핵심 흐름",
        "주목할 지역과 이유",
        "시장 변수",
        "관련 뉴스·리포트",
    ]
    assert payload["focusRegions"][0]["targetId"] == "region-seoul"
    assert payload["focusRegions"][0]["label"] == "서울특별시 지역 흐름"
    assert payload["focusRegions"][0]["reason"] == "변화율 +10.97%"
    assert payload["sourceItems"][0]["sourceItemId"] == "region-seoul"


def test_apply_daily_briefing_generation_fills_missing_required_sections_from_rule_based_context():
    pack = build_daily_briefing_input_pack(
        generated_at=_now(),
        map_targets=[
            {
                "targetId": "region-seoul",
                "displayName": "서울특별시",
                "periods": {"month": {"changePct": 10.97}},
            }
        ],
    )
    generated = {
        "title": "오늘의 부동산 시장 브리핑",
        "summaryHeadlines": [
            "서울 지역 흐름",
            "수도권 변수 집중",
            "정책 이슈 점검",
        ],
        "sections": {
            "오늘의 핵심 흐름": (
                "서울 중심의 지역별 온도차는 단기 등락보다 수요가 어느 생활권으로 압축되는지를 보여주는 신호입니다. "
                "오늘 들어온 재료를 분리해서 보면 정책, 전세, 거래가 따로 움직이는 것처럼 보이지만 실제 시장에서는 "
                "이 요소들이 한꺼번에 체감 심리를 만들 수 있습니다. 따라서 핵심은 특정 지역의 강세 단정이 아니라 "
                "반복되는 관심과 누적 지표가 같은 방향인지 점검하는 데 있습니다."
            ),
            "주목할 지역과 이유": (
                "서울과 경기 남부는 서로 다른 이유로 주목됩니다. 서울은 거래 회복 기대와 전세 부담이 맞물리는 권역이고, "
                "경기 남부는 공급과 산업 이슈가 함께 붙는 권역입니다. 같은 수도권이라도 해석 기준이 다르므로 순위보다 "
                "관심의 원인이 어디에서 반복되는지 보는 편이 더 유효합니다."
            ),
            "관련 뉴스·리포트": (
                "뉴스룸과 공식 리포트는 브리핑의 근거 후보로 연결됩니다. 한 기사나 한 지표만으로 결론을 내리기보다 "
                "여러 자료에서 반복되는 정책·공급·전세 논점을 함께 확인하는 구조가 필요합니다. 아래 근거는 시장 행동 "
                "권고가 아니라 오늘의 해석에 쓰인 자료의 출처입니다."
            ),
        },
        "focusRegions": [],
        "sourceItems": [],
    }

    payload = apply_daily_briefing_llm_generation(
        pack,
        generated,
        model_name="gpt-5-mini",
        prompt_version="daily-briefing-v1",
    )

    sections_by_title = {section["title"]: section for section in payload["sections"]}
    assert sections_by_title["오늘의 핵심 흐름"]["body"].startswith("서울 중심의 지역별 온도차")
    assert "시장 변수" in sections_by_title
    assert sections_by_title["시장 변수"]["body"]


def test_apply_daily_briefing_generation_rejects_thin_column_copy():
    pack = build_daily_briefing_input_pack(generated_at=_now())

    with pytest.raises(ValueError, match="column-style"):
        apply_daily_briefing_llm_generation(
            pack,
            {
                "title": "오늘의 부동산 시장 브리핑",
                "summaryHeadlines": ["서울 흐름", "정책 변수", "전세 압력"],
                "sections": {
                    "오늘의 핵심 흐름": "서울과 정책을 봅니다.",
                    "주목할 지역과 이유": "서울을 봅니다.",
                    "시장 변수": "정책이 변수입니다.",
                    "관련 뉴스·리포트": "뉴스를 봅니다.",
                },
                "focusRegions": [],
                "sourceItems": [],
            },
            model_name="claude-opus-4-8",
        )


def test_apply_daily_briefing_generation_allows_concise_supporting_sections():
    pack = build_daily_briefing_input_pack(generated_at=_now())
    concise_market_variables = (
        "세제 논의와 공급 일정이 단기 변수다. 가격 방향보다 발표 시점과 지역별 체감 차이를 확인한다."
    )

    payload = apply_daily_briefing_llm_generation(
        pack,
        {
            "title": "서울·수도권 단기 흐름 점검",
            "summaryHeadlines": ["서울 단기 흐름 점검", "경기 남부 변화 확인", "정책·공급 변수 압축"],
            "sections": {
                "오늘의 핵심 흐름": (
                    "이번 브리핑의 핵심은 서울과 수도권 일부 지역에서 단기 변화율, 전세 압력, 정책 논의가 같은 화면에 "
                    "올라왔다는 점이다. 하루치 사건을 나열하기보다 최근 며칠 사이 반복된 신호가 어떤 지역에서 다시 "
                    "확인되는지를 보는 편이 적절하다. 서울 중심권은 거래 회복과 전세 부담이 함께 언급되고, 경기 남부는 "
                    "공급 일정과 생활권 수요가 같은 축에서 확인된다. 다만 단기 변화율 하나를 시장 방향으로 단정하지 않고 "
                    "가격, 전세, 공급, 정책 자료가 같은 방향을 가리키는지 확인하는 방식으로 읽어야 한다. 그래서 오늘 "
                    "브리핑은 특정 지역 순위보다 단기 신호가 반복되는 지역과 변수의 조합을 중심에 둔다. 같은 수도권 안에서도 "
                    "전세 부담이 먼저 드러나는 생활권과 공급 일정이 먼저 반영되는 생활권은 해석 순서가 다르다. 따라서 핵심 "
                    "흐름은 가격 변화율만 보지 않고 전세, 공급, 정책 재료가 동시에 언급되는지를 확인하는 방식으로 정리한다."
                ),
                "주목할 지역과 이유": (
                    "서울 동남권과 경기 남부를 먼저 본다. 두 권역은 최근 단기 변화율과 공급·전세 이슈가 함께 확인돼 "
                    "누적 상승률보다 최근 움직임을 점검할 필요가 있다."
                ),
                "시장 변수": concise_market_variables,
                "관련 뉴스·리포트": (
                    "관련 뉴스와 리포트는 정책, 공급, 전세 흐름을 확인하는 근거다. 원문 링크는 같은 논점이 반복되는지 "
                    "추가로 확인하기 위한 출처로 둔다."
                ),
            },
            "focusRegions": [],
            "sourceItems": [],
        },
        model_name="claude-opus-4-8",
    )

    sections_by_title = {section["title"]: section for section in payload["sections"]}
    assert sections_by_title["시장 변수"]["body"] == concise_market_variables
    assert len(sections_by_title["시장 변수"]["body"]) < 130


def test_apply_daily_briefing_generation_rejects_overheated_news_style_copy():
    pack = build_daily_briefing_input_pack(generated_at=_now())

    with pytest.raises(ValueError, match="overheated"):
        apply_daily_briefing_llm_generation(
            pack,
            {
                "title": "세제 개편을 앞둔 관망 심리",
                "summaryHeadlines": ["세제 개편 논의", "서울 변화율 점검", "공급 변수 확인"],
                "sections": {
                    "오늘의 핵심 흐름": (
                        "오늘 시장의 중심축은 세제 개편을 둘러싼 관망 심리다. 시장은 속으로 부글거리는 모습을 보인다. "
                        "정부 논의와 공급 일정은 같은 화면에서 확인할 필요가 있다. 다만 개별 기사 표현을 그대로 결론으로 "
                        "옮기기보다 가격, 전세, 공급 지표가 함께 움직이는지 확인해야 한다. 단기 이슈를 시장 방향으로 "
                        "바로 연결하지 않고 공식 지표와 지역별 단기 변화율을 함께 확인하는 방식이 필요하다."
                    ),
                    "주목할 지역과 이유": (
                        "서울과 경기 남부를 확인한다. 두 지역은 단기 변화율과 공급 이슈가 함께 언급된다. "
                        "지역 순위보다 어떤 지표가 반복되는지가 중요하다. 단기 지표에서 변화가 확인되는 지역을 먼저 보고, "
                        "장기 누적 변화율은 보조 맥락으로만 둔다."
                    ),
                    "시장 변수": (
                        "세제와 공급 일정이 변수다. 정책 논의가 매물 판단에 영향을 줄 수 있고 공급 일정은 지역별 체감 차이를 만든다. "
                        "변수는 방향 단정보다 확인 대상에 가깝다. 전세와 공급 일정이 같은 방향으로 움직이는지 확인하는 "
                        "것이 단기 브리핑의 우선순위다."
                    ),
                    "관련 뉴스·리포트": (
                        "관련 뉴스와 리포트는 근거 확인용이다. 같은 논점이 여러 자료에서 반복되는지 확인한다. "
                        "원문 링크는 추가 검토를 위한 출처다. 기사 문장을 그대로 가져오지 않고 지표와 연결되는 내용만 "
                        "브리핑 본문에 반영한다."
                    ),
                },
                "focusRegions": [],
                "sourceItems": [],
            },
            model_name="claude-opus-4-8",
        )


def test_apply_daily_briefing_generation_enriches_source_items_from_candidates():
    pack = build_daily_briefing_input_pack(
        generated_at=_now(),
        content_items=[
            {
                "contentId": "news-policy-1",
                "title": "정부 부동산 세제 개편 시동…임대 매물 잠김 우려 - 강원일보",
                "url": "https://news.google.com/rss/articles/wrapped?oc=5",
                "canonicalUrl": "https://www.kwnews.co.kr/page/view/example",
                "domain": "www.kwnews.co.kr",
                "contentType": "news",
            }
        ],
    )
    generated = {
        "title": "세제 논의와 전세 압력의 연결고리",
        "summaryHeadlines": ["세제 개편 논의 본격화", "전세 압력 재점검", "지역별 온도차 확대"],
        "sections": {
            "오늘의 핵심 흐름": (
                "세제 개편 논의는 단일 정책 뉴스라기보다 매물 출회와 임대시장 심리를 함께 흔드는 변수로 읽어야 합니다. "
                "시장 참여자가 실제로 체감하는 변화는 세금 부담 자체보다 그 부담이 매도 대기, 임대료 기대, 전세 수요 이동으로 "
                "어떻게 이어지는지에서 나타납니다. 따라서 오늘의 핵심은 정책 발표 여부보다 관련 논의가 가격·전세·공급 자료와 "
                "같은 방향으로 반복되는지 확인하는 것입니다."
            ),
            "주목할 지역과 이유": (
                "수도권 핵심 권역은 세제와 전세 이슈가 가장 빠르게 결합되는 시장입니다. 서울은 매물 잠김 우려와 전세 부담이 "
                "동시에 언급되고, 경기 일부 생활권은 외곽 수요 이동의 영향을 받을 수 있습니다. 이런 지역은 단순 순위보다 "
                "정책 변수와 수급 지표가 같이 움직이는지 확인해야 합니다."
            ),
            "시장 변수": (
                "변수는 세제, 전세, 공급의 조합입니다. 세제 논의가 매물 의사결정을 늦추면 전세 물량에도 영향을 줄 수 있고, "
                "공급 일정이 약한 권역에서는 체감 압력이 더 크게 남을 수 있습니다. 반대로 입주가 확인되는 지역은 같은 정책 "
                "논의 아래에서도 부담이 다르게 나타날 수 있습니다."
            ),
            "관련 뉴스·리포트": (
                "이번 브리핑은 세제 개편 보도와 임대시장 영향 분석을 근거로 삼았습니다. 기사 하나를 결론으로 삼기보다 "
                "정책 논의가 반복적으로 어떤 시장 변수와 연결되는지 확인하는 방식이 적절합니다. 원문 근거는 아래 링크에서 "
                "추가로 확인할 수 있습니다."
            ),
        },
        "focusRegions": [],
        "sourceItems": [{"sourceItemId": "news-policy-1"}],
    }

    payload = apply_daily_briefing_llm_generation(
        pack,
        generated,
        model_name="claude-opus-4-8",
    )

    assert payload["sourceItems"][0]["url"] == "https://www.kwnews.co.kr/page/view/example"
    assert payload["sourceItems"][0]["label"] == "www.kwnews.co.kr"
    assert payload["sourceItems"][0]["title"] == "정부 부동산 세제 개편 시동…임대 매물 잠김 우려 - 강원일보"


def test_rule_based_daily_briefing_fallback_still_returns_three_noun_style_headlines():
    pack = build_daily_briefing_input_pack(
        generated_at=_now(),
        curated_items=[
            {
                "sourceItemId": "manual-report-1",
                "sourceType": "report",
                "title": "수도권 전세 압력 재부각",
                "url": "https://example.com/report",
                "lens": "new_variables",
            },
            {
                "sourceItemId": "manual-report-2",
                "sourceType": "report",
                "title": "서울 동남권 거래 회복 흐름",
                "url": "https://example.com/report2",
                "lens": "repeated_flow",
            },
        ],
    )

    payload = build_rule_based_daily_briefing(pack, model_name="rule-based")

    assert len(payload["summaryHeadlines"]) == 3
    assert payload["summaryHeadlines"][0] == "수도권 전세 압력 재부각"
    assert payload["summaryHeadlines"][1] == "서울 동남권 거래 회복 흐름"
    assert payload["summaryHeadlines"][2] == "주요 시장 변수 점검"


class _DailyBriefingSpringClient:
    def __init__(self) -> None:
        self.published = []

    def list_real_estate_market_facts(self, **_kwargs):
        return [
            {
                "targetId": "region-seoul",
                "factType": "jeonse_pressure",
                "valueJson": {"label": "수도권 전세 압력"},
                "provider": "reb_stat",
            }
        ]

    def list_real_estate_map_layer_targets(self, **_kwargs):
        return [
            {
                "targetId": "region-seoul",
                "displayName": "서울",
                "periods": {"month": {"changePct": 0.35, "sampleCount": 200}},
            }
        ]

    def list_real_estate_newsroom_items(self, **_kwargs):
        return [
            {
                "contentId": "news-1",
                "title": "수도권 전세 정책 점검",
                "url": "https://example.com/news",
                "contentType": "news",
            }
        ]

    def publish_real_estate_daily_briefings(self, briefings):
        self.published.extend(briefings)


def test_daily_briefing_refresh_job_publishes_llm_generated_payload():
    client = _DailyBriefingSpringClient()
    seen_pack = {}

    def llm_generator(pack):
        seen_pack.update(pack)
        return {
            "title": "오늘의 부동산 시장 브리핑",
            "summaryHeadlines": [
                "수도권 전세 압력 재부각",
                "서울 거래 회복 흐름",
                "공급·정책 이슈 집중",
            ],
            "sections": [
                {
                    "sectionId": "flow",
                    "title": "오늘의 핵심 흐름",
                    "body": (
                        "전세 압력 재부각은 단기 뉴스 하나보다 수도권 수급이 다시 시장의 중심 변수로 올라왔다는 신호입니다. "
                        "거래 회복 기대와 임대시장 부담이 함께 언급될 때 시장은 가격 방향보다 선호 지역 압축과 대기 수요의 "
                        "움직임으로 먼저 반응할 수 있습니다. 따라서 오늘의 핵심은 특정 지역의 상승 단정이 아니라 전세·거래·정책 "
                        "재료가 같은 방향으로 반복되는지 확인하는 데 있습니다. 이런 조합은 하루짜리 사건보다 최근 며칠간 "
                        "같은 논점이 다시 등장하는지 볼 때 더 의미가 분명해집니다."
                    ),
                },
                {
                    "sectionId": "regions",
                    "title": "주목할 지역과 이유",
                    "body": (
                        "서울은 전세 부담과 거래 회복 기대가 함께 붙는 권역이어서 우선 확인할 필요가 있습니다. 경기 남부는 "
                        "공급과 정책 이슈가 같이 언급되는 만큼 같은 수도권 안에서도 해석 기준이 다릅니다. 지역을 볼 때는 "
                        "순위보다 왜 관심이 붙었는지, 그 이유가 여러 자료에서 반복되는지를 확인해야 합니다. 특히 같은 수도권이라도 "
                        "서울의 대기 수요와 경기 남부의 공급 기대는 서로 다른 속도로 시장에 반영될 수 있습니다."
                    ),
                },
                {
                    "sectionId": "variables",
                    "title": "시장 변수",
                    "body": (
                        "공급과 정책은 오늘 브리핑의 핵심 변수입니다. 세제 논의가 매물 의사결정에 영향을 주는 동안 공급 일정은 "
                        "전세와 매매 심리를 완충하거나 압박할 수 있습니다. 두 변수가 같은 방향으로 작동하는 지역과 엇갈리는 "
                        "지역을 나눠 보는 것이 필요합니다. 그래서 변수 해석은 정책명 자체보다 전세, 거래, 입주 일정이 함께 "
                        "움직이는지를 확인하는 쪽에 무게가 있습니다."
                    ),
                },
                {
                    "sectionId": "sources",
                    "title": "관련 뉴스·리포트",
                    "body": (
                        "정책 뉴스와 리포트는 브리핑의 근거로 연결됩니다. 개별 보도만으로 결론을 내리지 않고, 전세·거래·공급 "
                        "자료와 함께 반복되는 논점을 확인해야 합니다. 원문 근거는 추가 검토를 위한 출처이며 투자 행동을 "
                        "지시하는 신호가 아닙니다. 같은 주제가 여러 출처에서 반복될 때만 오늘의 핵심 흐름으로 끌어올리는 "
                        "방식이 더 안전합니다."
                    ),
                },
            ],
        }

    job = RealEstateDailyBriefingRefreshJob(
        client=client,
        llm_generator=llm_generator,
        model_name="claude opus 4 8",
        clock=_now,
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.briefing_count == 1
    assert seen_pack["briefingDate"] == "2026-06-24"
    assert client.published[0]["summaryHeadlines"][0] == "수도권 전세 압력 재부각"
    assert client.published[0]["modelName"] == "claude opus 4 8"


def test_daily_briefing_generation_rejects_time_window_section_titles():
    pack = build_daily_briefing_input_pack(generated_at=_now())

    with pytest.raises(ValueError):
        apply_daily_briefing_llm_generation(
            pack,
            {
                "summaryHeadlines": ["수도권 전세 압력", "서울 거래 회복", "정책 이슈 집중"],
                "sections": [
                    {"sectionId": "today", "title": "24시간 흐름", "body": "오늘 들어온 사건 목록입니다."}
                ],
            },
            model_name="claude opus 4 8",
        )
