from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_reactions import (
    RealEstateReactionObservation,
    build_real_estate_reaction_snapshots,
    load_real_estate_reaction_observations,
)


def test_build_real_estate_reaction_snapshots_groups_current_window_and_previous_mentions():
    window_start = datetime(2026, 6, 11, 0, 0, tzinfo=timezone.utc)
    as_of = datetime(2026, 6, 11, 1, 2, tzinfo=timezone.utc)
    observations = [
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-daejeon",
            published_at=datetime(2026, 6, 10, 23, 10, tzinfo=timezone.utc),
            source="naver-cafe:estate",
            reaction_direction="concern",
        ),
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-daejeon",
            published_at=datetime(2026, 6, 10, 23, 45, tzinfo=timezone.utc),
            source="dcinside:immovables",
            reaction_direction="neutral",
        ),
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-daejeon",
            published_at=datetime(2026, 6, 11, 0, 5, tzinfo=timezone.utc),
            source="naver-cafe:estate",
            reaction_direction="expectation",
            issues=[
                {
                    "issueKey": "rail",
                    "label": "rail",
                    "direction": "expectation",
                    "confidence": 0.8,
                    "summary": "rail access is repeatedly mentioned",
                }
            ],
        ),
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-daejeon",
            published_at=datetime(2026, 6, 11, 0, 15, tzinfo=timezone.utc),
            source="naver-cafe:estate",
            reaction_direction="expectation",
            issues=[
                {
                    "issueKey": "rail",
                    "label": "rail",
                    "direction": "expectation",
                    "confidence": 0.6,
                    "summary": "rail access is repeatedly mentioned",
                }
            ],
        ),
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-daejeon",
            published_at=datetime(2026, 6, 11, 0, 25, tzinfo=timezone.utc),
            source="dcinside:immovables",
            reaction_direction="concern",
            issues=[
                {
                    "issueKey": "supply",
                    "label": "supply",
                    "direction": "concern",
                    "confidence": 0.9,
                }
            ],
        ),
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-daejeon",
            published_at=datetime(2026, 6, 11, 0, 35, tzinfo=timezone.utc),
            source="ppomppu:house",
            reaction_direction="neutral",
        ),
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-seoul",
            published_at=datetime(2026, 6, 11, 0, 20, tzinfo=timezone.utc),
            source="naver-cafe:estate",
            reaction_direction="concern",
        ),
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-daejeon",
            published_at=datetime(2026, 6, 11, 1, 0, tzinfo=timezone.utc),
            source="naver-cafe:estate",
            reaction_direction="expectation",
        ),
    ]

    snapshots = build_real_estate_reaction_snapshots(
        observations,
        window_start=window_start,
        window_minutes=60,
        as_of=as_of,
    )

    assert [snapshot.target_id for snapshot in snapshots] == ["region-daejeon", "region-seoul"]
    first = snapshots[0].to_request_dict()
    assert first == {
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
        "coverageStatus": "partial",
        "stale": False,
        "issues": [
            {
                "issueKey": "rail",
                "label": "rail",
                "share": 0.5,
                "direction": "expectation",
                "summary": "rail access is repeatedly mentioned",
                "confidence": 0.7,
            },
            {
                "issueKey": "supply",
                "label": "supply",
                "share": 0.25,
                "direction": "concern",
                "summary": "",
                "confidence": 0.9,
            },
        ],
    }


def test_build_real_estate_reaction_snapshots_marks_low_sample_and_source_skewed_coverage():
    window_start = datetime(2026, 6, 11, 0, 0, tzinfo=timezone.utc)
    low_sample = build_real_estate_reaction_snapshots(
        [
            RealEstateReactionObservation(
                target_type="region",
                target_id="region-seoul",
                published_at=datetime(2026, 6, 11, 0, 5, tzinfo=timezone.utc),
                source="naver-cafe:estate",
                reaction_direction="expectation",
            ),
            RealEstateReactionObservation(
                target_type="region",
                target_id="region-seoul",
                published_at=datetime(2026, 6, 11, 0, 15, tzinfo=timezone.utc),
                source="naver-cafe:estate",
                reaction_direction="concern",
            ),
        ],
        window_start=window_start,
        window_minutes=60,
        as_of=datetime(2026, 6, 11, 1, 2, tzinfo=timezone.utc),
    )[0].to_request_dict()

    source_skewed = build_real_estate_reaction_snapshots(
        [
            RealEstateReactionObservation(
                target_type="region",
                target_id="region-busan",
                published_at=datetime(2026, 6, 11, 0, minute, tzinfo=timezone.utc),
                source="naver-cafe:estate",
                reaction_direction="expectation",
            )
            for minute in [5, 10, 15, 20, 25]
        ],
        window_start=window_start,
        window_minutes=60,
        as_of=datetime(2026, 6, 11, 1, 2, tzinfo=timezone.utc),
    )[0].to_request_dict()

    assert low_sample["coverageStatus"] == "low_sample"
    assert low_sample["confidence"] == 0.39
    assert source_skewed["coverageStatus"] == "source_skewed"
    assert source_skewed["sourceSkew"] == 1.0
    assert source_skewed["confidence"] == 0.48


def test_build_real_estate_reaction_snapshots_marks_stale_when_collection_lag_is_large():
    window_start = datetime(2026, 6, 11, 0, 0, tzinfo=timezone.utc)
    snapshots = build_real_estate_reaction_snapshots(
        [
            RealEstateReactionObservation(
                target_type="region",
                target_id="region-jeju",
                published_at=datetime(2026, 6, 11, 0, 5, tzinfo=timezone.utc),
                source="naver-cafe:estate",
                reaction_direction="expectation",
            ),
            RealEstateReactionObservation(
                target_type="region",
                target_id="region-jeju",
                published_at=datetime(2026, 6, 11, 0, 15, tzinfo=timezone.utc),
                source="dcinside:immovables",
                reaction_direction="concern",
            ),
            RealEstateReactionObservation(
                target_type="region",
                target_id="region-jeju",
                published_at=datetime(2026, 6, 11, 0, 25, tzinfo=timezone.utc),
                source="naver-cafe:estate",
                reaction_direction="neutral",
            ),
        ],
        window_start=window_start,
        window_minutes=1440,
        as_of=datetime(2026, 6, 11, 8, 30, tzinfo=timezone.utc),
        stale_after_minutes=120,
    )

    payload = snapshots[0].to_request_dict()
    assert payload["coverageStatus"] == "stale"
    assert payload["stale"] is True
    assert payload["confidence"] == 0.38


def test_load_real_estate_reaction_observations_reads_jsonl_records(tmp_path):
    path = tmp_path / "observations.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"targetType":"region","targetId":"region-busan","publishedAt":"2026-06-11T00:10:00Z","source":"dcinside","reactionDirection":"concern","issues":[]}',
                '{"targetType":"complex","targetId":"complex-apt-1","publishedAt":"2026-06-11T00:12:00+00:00","source":"naver-cafe","reactionDirection":"expectation"}',
            ]
        ),
        encoding="utf-8",
    )

    observations = load_real_estate_reaction_observations(path)

    assert observations == [
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-busan",
            published_at=datetime(2026, 6, 11, 0, 10, tzinfo=timezone.utc),
            source="dcinside",
            reaction_direction="concern",
            issues=[],
        ),
        RealEstateReactionObservation(
            target_type="complex",
            target_id="complex-apt-1",
            published_at=datetime(2026, 6, 11, 0, 12, tzinfo=timezone.utc),
            source="naver-cafe",
            reaction_direction="expectation",
            issues=[],
        ),
    ]
