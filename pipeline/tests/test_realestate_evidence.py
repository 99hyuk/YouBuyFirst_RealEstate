from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_evidence import build_real_estate_evidence_logs


def test_build_real_estate_evidence_log_combines_reaction_market_issue_and_similarity():
    logs = build_real_estate_evidence_logs(
        [_reaction_snapshot()],
        target_id="region-daejeon",
        window_start="2026-06-11T00:00:00Z",
        evaluated_at=datetime(2026, 6, 12, 2, 0, tzinfo=timezone.utc),
        market_facts=[
            {
                "targetId": "region-daejeon",
                "factType": "apt_trade",
                "observedAt": "2026-06-10",
                "asOf": "2026-06-10T00:00:00Z",
                "provider": "molit",
                "providerDataset": "molit_apt_trade",
                "providerObjectId": "molit_apt_trade:30200:202606:1",
                "valueJson": {"dealAmountManwon": 73000},
            }
        ],
        similar_windows=[
            {
                "matchedTargetId": "region-gwangju",
                "similarityScore": 0.962,
                "evidenceItem": {
                    "evidenceItemId": "similar-region-daejeon-region-gwangju",
                    "evidenceType": "similar_window",
                    "refType": "similar_window",
                    "refId": "region-gwangju-2026-03-01",
                    "label": "유사 과거 window",
                    "valueText": "유사도 96.2% · 매매 +6.0%",
                    "severity": "info",
                },
            }
        ],
        content_items=[
            {
                "contentId": "serpapi-issue-daejeon-transport",
                "sourceId": "serpapi:google_news",
                "title": "대전 광역교통 이슈 후보",
                "url": "https://example.com/daejeon-transport",
                "publishedAt": "2026-06-10T09:00:00Z",
                "targets": [
                    {
                        "targetId": "region-daejeon",
                        "linkType": "search_candidate",
                        "confidence": 0.45,
                        "reviewState": "candidate",
                    }
                ],
            }
        ],
        timeline_events=[
            {
                "id": "policy-event-supply-daejeon-region-daejeon-primary",
                "targetId": "region-daejeon",
                "eventType": "supply",
                "sourceRefType": "policy_event",
                "sourceRefId": "policy-event-supply-daejeon",
                "title": "대전 도심 공급계획 발표",
                "summary": "도심 공급 후보지와 교통 개선 일정이 함께 언급됩니다.",
                "occurredAt": "2026-06-09T00:00:00Z",
                "asOf": "2026-06-09T00:00:00Z",
                "dataStatus": "approved",
            }
        ],
        evaluation_version="realestate-eval-v1",
        prompt_version="rule-evidence-v1",
    )

    assert len(logs) == 1
    log = logs[0]
    assert log["evidenceLogId"] == "evidence-region-daejeon-20260611000000-20260612020000-realestate-eval-v1"
    assert log["targetId"] == "region-daejeon"
    assert log["tone"] == "watch"
    assert log["summary"] == "관심과 기대 반응이 빠르게 관찰됩니다."
    assert log["subtitle"] == "언급 4건, 직전 대비 +100.0%, 주요 쟁점: 교통, 공급"
    assert log["dataQuality"] == "partial"
    assert log["confidence"] == 0.66
    assert log["evaluatedAt"] == "2026-06-12T02:00:00Z"
    assert log["asOf"] == "2026-06-11T01:02:00Z"
    assert log["skipReason"] is None
    assert "partial" in log["caveats"]

    evidence_types = [item["evidenceType"] for item in log["evidenceItems"]]
    assert evidence_types == ["reaction", "market_fact", "timeline_event", "similar_window", "search_candidate"]
    assert log["evidenceItems"][0]["valueText"] == "언급 4건 · 기대 50.0% / 우려 25.0%"
    assert log["evidenceItems"][1]["valueText"] == "매매 73,000만원"
    assert log["evidenceItems"][2] == {
        "evidenceItemId": "timeline-event-region-daejeon-policy-event-supply-daejeon-region-daejeon-primary",
        "evidenceType": "timeline_event",
        "refType": "timeline_event",
        "refId": "policy-event-supply-daejeon-region-daejeon-primary",
        "label": "타임라인: 공급",
        "valueText": "대전 도심 공급계획 발표",
        "severity": "info",
    }
    assert log["evidenceItems"][4]["valueText"] == "대전 광역교통 이슈 후보"

    unsafe_words = ["사라", "팔아라", "청약 넣어라", "지금 들어가라", "수익 보장"]
    assert not any(word in f"{log['summary']} {log['subtitle']}" for word in unsafe_words)


def test_build_real_estate_evidence_log_marks_missing_supporting_sources():
    logs = build_real_estate_evidence_logs(
        [_reaction_snapshot(coverage_status="source_skewed", stale=True)],
        target_id="region-daejeon",
        window_start="2026-06-11T00:00:00Z",
        evaluated_at="2026-06-12T02:00:00Z",
    )

    assert logs[0]["dataQuality"] == "stale"
    assert logs[0]["caveats"] == [
        "source_skewed",
        "stale",
        "market_fact_missing",
        "timeline_event_missing",
        "similar_window_missing",
        "search_candidate_missing",
    ]


def _reaction_snapshot(coverage_status: str = "partial", stale: bool = False) -> dict:
    return {
        "targetType": "region",
        "targetId": "region-daejeon",
        "windowStart": "2026-06-11T00:00:00Z",
        "windowEnd": "2026-06-11T01:00:00Z",
        "asOf": "2026-06-11T01:02:00Z",
        "mentionCount": 4,
        "previousMentionCount": 2,
        "expectationScore": 50.0,
        "concernScore": 25.0,
        "neutralScore": 25.0,
        "heatScore": 71,
        "confidence": 0.66,
        "sourceCount": 3,
        "sourceSkew": 0.5,
        "coverageStatus": coverage_status,
        "stale": stale,
        "issues": [
            {
                "issueKey": "rail",
                "label": "교통",
                "share": 0.5,
                "direction": "expectation",
                "summary": "교통 기대가 반복 언급됩니다.",
                "confidence": 0.7,
            },
            {
                "issueKey": "supply",
                "label": "공급",
                "share": 0.25,
                "direction": "concern",
                "summary": "공급 부담도 함께 언급됩니다.",
                "confidence": 0.9,
            },
        ],
    }
