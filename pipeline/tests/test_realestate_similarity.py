from youbuyfirst_pipeline.realestate_similarity import (
    find_real_estate_similar_windows,
    load_real_estate_reaction_snapshot_payloads,
)


def test_find_real_estate_similar_windows_ranks_reaction_issue_and_market_flow(tmp_path):
    snapshots_path = tmp_path / "snapshots.jsonl"
    snapshots_path.write_text(
        "\n".join(
            [
                '{"targetType":"region","targetId":"region-daejeon","windowStart":"2026-06-11T00:00:00Z","windowEnd":"2026-06-11T01:00:00Z","asOf":"2026-06-11T01:02:00Z","mentionCount":4,"previousMentionCount":2,"expectationScore":50.0,"concernScore":25.0,"neutralScore":25.0,"heatScore":71,"confidence":0.66,"sourceCount":3,"sourceSkew":0.5,"coverageStatus":"partial","stale":false,"issues":[{"issueKey":"rail","label":"교통","share":0.5,"direction":"expectation","summary":"교통 기대가 반복 언급됩니다.","confidence":0.7},{"issueKey":"supply","label":"공급","share":0.25,"direction":"concern","summary":"공급 부담도 함께 언급됩니다.","confidence":0.9}]}',
                '{"targetType":"region","targetId":"region-gwangju","windowStart":"2026-03-01T00:00:00Z","windowEnd":"2026-03-01T01:00:00Z","asOf":"2026-03-01T01:02:00Z","mentionCount":8,"previousMentionCount":4,"expectationScore":52.0,"concernScore":24.0,"neutralScore":24.0,"heatScore":70,"confidence":0.72,"sourceCount":3,"sourceSkew":0.5,"coverageStatus":"partial","stale":false,"issues":[{"issueKey":"rail","label":"교통","share":0.45,"direction":"expectation","summary":"교통 기대가 반복 언급됩니다.","confidence":0.8},{"issueKey":"supply","label":"공급","share":0.3,"direction":"concern","summary":"공급 부담도 함께 언급됩니다.","confidence":0.7}]}',
                '{"targetType":"region","targetId":"region-busan","windowStart":"2026-02-01T00:00:00Z","windowEnd":"2026-02-01T01:00:00Z","asOf":"2026-02-01T01:02:00Z","mentionCount":12,"previousMentionCount":2,"expectationScore":5.0,"concernScore":80.0,"neutralScore":15.0,"heatScore":95,"confidence":0.7,"sourceCount":2,"sourceSkew":0.8,"coverageStatus":"source_skewed","stale":false,"issues":[{"issueKey":"loan","label":"대출","share":0.6,"direction":"concern","summary":"대출 우려가 큽니다.","confidence":0.8}]}',
            ]
        ),
        encoding="utf-8",
    )
    market_facts = [
        {
            "targetId": "region-gwangju",
            "factType": "apt_trade",
            "observedAt": "2026-03-10",
            "valueJson": {"dealAmountManwon": 50000},
        },
        {
            "targetId": "region-gwangju",
            "factType": "apt_trade",
            "observedAt": "2026-04-20",
            "valueJson": {"dealAmountManwon": 53000},
        },
    ]

    matches = find_real_estate_similar_windows(
        load_real_estate_reaction_snapshot_payloads(snapshots_path),
        source_target_id="region-daejeon",
        source_window_start="2026-06-11T00:00:00Z",
        market_facts=market_facts,
        horizon_days=90,
        top_n=2,
    )

    assert [match.matched_target_id for match in matches] == ["region-gwangju", "region-busan"]
    assert matches[0].similarity_score > 0.95
    assert matches[0].issue_overlap == ["rail", "supply"]
    assert matches[0].after_market_summary["items"] == [
        {
            "factType": "apt_trade",
            "metric": "dealAmountManwon",
            "firstObservedAt": "2026-03-10",
            "lastObservedAt": "2026-04-20",
            "firstValue": 50000.0,
            "lastValue": 53000.0,
            "deltaPct": 6.0,
            "sampleCount": 2,
        }
    ]
    assert matches[0].to_evidence_item_dict()["evidenceType"] == "similar_window"
    assert matches[0].to_evidence_item_dict()["refType"] == "similar_window"
    assert "유사도" in matches[0].to_evidence_item_dict()["valueText"]
