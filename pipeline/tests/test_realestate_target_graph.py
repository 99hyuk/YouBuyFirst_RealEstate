from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_reactions import (
    RealEstateReactionObservation,
    build_real_estate_reaction_snapshots,
)
from youbuyfirst_pipeline.realestate_target_graph import (
    RealEstateTargetEdgeRule,
    load_real_estate_target_edge_rules,
    roll_up_real_estate_reaction_observations,
)


def test_roll_up_real_estate_reaction_observations_adds_parent_region_snapshot(tmp_path):
    edge_path = tmp_path / "target_edges.jsonl"
    edge_path.write_text(
        '{"fromTargetType":"region","fromTargetId":"region-seoul","toTargetType":"region","toTargetId":"region-seoul-jongno","edgeType":"contains","reviewState":"approved","confidence":0.8}',
        encoding="utf-8",
    )
    window_start = datetime(2026, 6, 11, 0, 0, tzinfo=timezone.utc)
    observations = [
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-seoul-jongno",
            published_at=datetime(2026, 6, 11, 0, 5, tzinfo=timezone.utc),
            source="naver-cafe:estate",
            reaction_direction="expectation",
            issues=[
                {
                    "issueKey": "redevelopment",
                    "label": "redevelopment",
                    "direction": "expectation",
                    "summary": "rebuild expectation",
                    "confidence": 0.7,
                }
            ],
            external_id="post-1",
            confidence=0.9,
        )
    ]

    rolled_up = roll_up_real_estate_reaction_observations(
        observations,
        load_real_estate_target_edge_rules(edge_path),
    )
    snapshots = build_real_estate_reaction_snapshots(
        rolled_up,
        window_start=window_start,
        window_minutes=60,
        as_of=datetime(2026, 6, 11, 1, 0, tzinfo=timezone.utc),
    )

    assert [snapshot.target_id for snapshot in snapshots] == ["region-seoul", "region-seoul-jongno"]
    parent_observation = next(observation for observation in rolled_up if observation.target_id == "region-seoul")
    assert parent_observation.external_id == "post-1"
    assert parent_observation.matched_text == "rollup:region-seoul-jongno"
    assert parent_observation.match_source == "target_graph:contains"
    assert parent_observation.confidence == 0.72
    assert snapshots[0].to_request_dict()["issues"][0]["issueKey"] == "redevelopment"


def test_roll_up_real_estate_reaction_observations_uses_transitive_contains_edges():
    observations = [
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-seoul-jongno-sajik",
            published_at=datetime(2026, 6, 11, 0, 5, tzinfo=timezone.utc),
            source="dcinside:immovables",
            reaction_direction="concern",
            confidence=0.8,
        )
    ]
    edges = [
        RealEstateTargetEdgeRule(
            from_target_type="region",
            from_target_id="region-seoul",
            to_target_type="region",
            to_target_id="region-seoul-jongno",
            edge_type="contains",
            review_state="approved",
            confidence=0.9,
        ),
        RealEstateTargetEdgeRule(
            from_target_type="region",
            from_target_id="region-seoul-jongno",
            to_target_type="region",
            to_target_id="region-seoul-jongno-sajik",
            edge_type="contains",
            review_state="approved",
            confidence=0.8,
        ),
    ]

    rolled_up = roll_up_real_estate_reaction_observations(observations, edges)

    assert [(observation.target_id, observation.confidence) for observation in rolled_up] == [
        ("region-seoul", 0.58),
        ("region-seoul-jongno", 0.64),
        ("region-seoul-jongno-sajik", 0.8),
    ]


def test_roll_up_real_estate_reaction_observations_does_not_duplicate_existing_parent_mention():
    published_at = datetime(2026, 6, 11, 0, 5, tzinfo=timezone.utc)
    observations = [
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-seoul",
            published_at=published_at,
            source="naver-cafe:estate",
            reaction_direction="expectation",
            external_id="post-1",
        ),
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-seoul-jongno",
            published_at=published_at,
            source="naver-cafe:estate",
            reaction_direction="expectation",
            external_id="post-1",
        ),
    ]
    edges = [
        RealEstateTargetEdgeRule(
            from_target_type="region",
            from_target_id="region-seoul",
            to_target_type="region",
            to_target_id="region-seoul-jongno",
            edge_type="contains",
        )
    ]

    rolled_up = roll_up_real_estate_reaction_observations(observations, edges)

    assert [(observation.target_id, observation.match_source) for observation in rolled_up] == [
        ("region-seoul", None),
        ("region-seoul-jongno", None),
    ]


def test_roll_up_real_estate_reaction_observations_counts_one_post_once_per_ancestor_target():
    published_at = datetime(2026, 6, 11, 0, 5, tzinfo=timezone.utc)
    observations = [
        RealEstateReactionObservation(
            target_type="region",
            target_id="region-1144010100",
            published_at=published_at,
            source="naver-cafe:estate",
            reaction_direction="concern",
            external_id="post-maraepu-ahyeon",
            matched_text="아현동",
            confidence=0.9,
        ),
        RealEstateReactionObservation(
            target_type="complex",
            target_id="complex-molit-1144010100-maraepu",
            published_at=published_at,
            source="naver-cafe:estate",
            reaction_direction="concern",
            external_id="post-maraepu-ahyeon",
            matched_text="마래푸",
            confidence=0.88,
        ),
    ]
    edges = [
        RealEstateTargetEdgeRule(
            from_target_type="region",
            from_target_id="region-seoul",
            to_target_type="region",
            to_target_id="region-seoul-mapo",
            edge_type="contains",
            confidence=0.9,
        ),
        RealEstateTargetEdgeRule(
            from_target_type="region",
            from_target_id="region-seoul-mapo",
            to_target_type="region",
            to_target_id="region-1144010100",
            edge_type="contains",
            confidence=0.8,
        ),
        RealEstateTargetEdgeRule(
            from_target_type="region",
            from_target_id="region-1144010100",
            to_target_type="complex",
            to_target_id="complex-molit-1144010100-maraepu",
            edge_type="contains",
            confidence=0.74,
        ),
    ]

    rolled_up = roll_up_real_estate_reaction_observations(observations, edges)
    snapshots = build_real_estate_reaction_snapshots(
        rolled_up,
        window_start=datetime(2026, 6, 11, 0, 0, tzinfo=timezone.utc),
        window_minutes=60,
        as_of=datetime(2026, 6, 11, 1, 0, tzinfo=timezone.utc),
    )

    assert [(snapshot.target_id, snapshot.mention_count) for snapshot in snapshots] == [
        ("complex-molit-1144010100-maraepu", 1),
        ("region-1144010100", 1),
        ("region-seoul", 1),
        ("region-seoul-mapo", 1),
    ]
