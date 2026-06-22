from youbuyfirst_pipeline.realestate_top10_readiness import build_real_estate_top10_readiness


class _Client:
    def __init__(self, *, complex_rows=None, region_rows=None, aliases=None, edges=None):
        self.complex_rows = complex_rows or []
        self.region_rows = region_rows or []
        self.aliases = aliases or []
        self.edges = edges or []
        self.ranking_requests = []

    def list_real_estate_aliases(self, **kwargs):
        assert kwargs["target_type"] == "complex"
        return list(self.aliases)

    def list_real_estate_target_edges(self, **kwargs):
        assert kwargs["edge_type"] == "contains"
        return list(self.edges)

    def get_real_estate_reaction_ranking(self, *, target_type: str, window_minutes: int, limit: int):
        self.ranking_requests.append(
            {
                "targetType": target_type,
                "windowMinutes": window_minutes,
                "limit": limit,
            }
        )
        if target_type == "complex":
            return {"items": list(self.complex_rows)}
        return {"items": list(self.region_rows)}


def test_top10_readiness_is_ready_when_complex_registry_snapshots_and_region_rollup_are_connected():
    client = _Client(
        aliases=[
            {
                "targetType": "complex",
                "targetId": "complex-molit-1144010100-maraepu",
                "alias": "마래푸",
                "source": "molit:market-fact",
            },
            {
                "targetType": "complex",
                "targetId": "complex-community-dongtan-lotte-castle",
                "alias": "동탄역 롯데캐슬",
                "source": "community:observed-complex-seed",
            },
        ],
        edges=[
            {
                "fromTargetType": "region",
                "fromTargetId": "region-1144010100",
                "toTargetType": "complex",
                "toTargetId": "complex-molit-1144010100-maraepu",
                "edgeType": "contains",
                "source": "molit:market-fact",
            }
        ],
        complex_rows=[
            {
                "targetType": "complex",
                "targetId": "complex-molit-1144010100-maraepu",
                "displayName": "마포래미안푸르지오",
            },
            {
                "targetType": "complex",
                "targetId": "complex-community-dongtan-lotte-castle",
                "displayName": "동탄역 롯데캐슬",
            },
        ],
        region_rows=[
            {
                "targetType": "region",
                "targetId": "region-seoul-mapo",
                "displayName": "서울 마포구",
            }
        ],
    )

    payload = build_real_estate_top10_readiness(client, window_minutes=10080, limit=1)

    assert payload["status"] == "READY"
    assert payload["missing"] == []
    assert payload["complexRegistry"] == {
        "complexCount": 2,
        "marketFactBackedComplexCount": 1,
        "communityObservedComplexCount": 1,
        "aliasCount": 2,
        "edgeCount": 1,
    }
    assert payload["reactionSnapshots"] == {"complex": 2, "region": 1}
    assert payload["frontTop10"]["complexOnly"] is True
    assert payload["frontTop10"]["broadRegionRows"] == []
    assert client.ranking_requests == [
        {"targetType": "complex", "windowMinutes": 10080, "limit": 1},
        {"targetType": "region", "windowMinutes": 10080, "limit": 1},
    ]


def test_top10_readiness_marks_partial_when_complex_ranking_is_missing_or_region_rows_are_broad():
    client = _Client(
        aliases=[
            {
                "targetType": "complex",
                "targetId": "complex-community-dongtan-lotte-castle",
                "alias": "동탄역 롯데캐슬",
                "source": "community:observed-complex-seed",
            }
        ],
        edges=[],
        complex_rows=[
            {
                "targetType": "region",
                "targetId": "region-seoul-mapo",
                "displayName": "마포구",
            }
        ],
        region_rows=[
            {
                "targetType": "region",
                "targetId": "region-seoul",
                "displayName": "서울특별시",
            }
        ],
    )

    payload = build_real_estate_top10_readiness(client, window_minutes=10080, limit=10)

    assert payload["status"] == "PARTIAL"
    assert payload["missing"] == [
        "complex_region_edge_empty",
        "market_fact_backed_complex_empty",
        "complex_snapshot_empty",
        "complex_ranking_contains_non_complex",
        "region_ranking_contains_broad_sido",
    ]
    assert payload["frontTop10"]["invalidComplexRows"] == ["region-seoul-mapo"]
    assert payload["frontTop10"]["broadRegionRows"] == ["region-seoul"]


def test_top10_readiness_marks_partial_when_front_top10_rows_are_short():
    client = _Client(
        aliases=[
            {
                "targetType": "complex",
                "targetId": "complex-molit-1144010100-sample",
                "alias": "sample complex",
                "source": "molit:market-fact",
            }
        ],
        edges=[
            {
                "fromTargetType": "region",
                "fromTargetId": "region-1144010100",
                "toTargetType": "complex",
                "toTargetId": "complex-molit-1144010100-sample",
                "edgeType": "contains",
                "source": "molit:market-fact",
            }
        ],
        complex_rows=[
            {
                "targetType": "complex",
                "targetId": f"complex-molit-1144010100-sample-{index}",
                "displayName": f"Sample Complex {index}",
            }
            for index in range(8)
        ],
        region_rows=[
            {
                "targetType": "region",
                "targetId": f"region-seoul-mapo-{index}",
                "displayName": f"Sample Region {index}",
            }
            for index in range(9)
        ],
    )

    payload = build_real_estate_top10_readiness(client, window_minutes=10080, limit=10)

    assert payload["status"] == "PARTIAL"
    assert payload["missing"] == ["complex_top10_short", "region_top10_short"]
    assert payload["frontTop10"]["requiredItems"] == 10
    assert payload["frontTop10"]["complexItems"] == 8
    assert payload["frontTop10"]["regionItems"] == 9
