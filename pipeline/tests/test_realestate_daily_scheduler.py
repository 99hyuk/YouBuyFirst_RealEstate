import asyncio
from datetime import datetime, timezone

from youbuyfirst_pipeline.realestate_daily_scheduler import (
    RealEstateCommunityCrawlRefreshJob,
    RealEstateCommunityComplexSeedRefreshJob,
    RealEstateComplexRegistryRefreshResult,
    RealEstateComplexRegistryRefreshJob,
    RealEstateDailyRefreshJob,
    RealEstateEvidenceLogRefreshJob,
    RealEstateMapLayerRefreshJob,
    RealEstateOfficialStatsRefreshJob,
    RealEstateRecentIssuesRefreshJob,
    _ranking_with_window_defaults,
)
from youbuyfirst_pipeline.realestate_recent_issues import SerpApiRecentIssueResult
from youbuyfirst_pipeline.realestate_reaction_scheduler import RealEstateReactionSnapshotRefreshResult


class _Step:
    def __init__(self, result=None, fail: bool = False) -> None:
        self.result = result or {"status": "OK"}
        self.fail = fail
        self.calls = 0

    def run_once(self):
        self.calls += 1
        if self.fail:
            raise RuntimeError("step failed")
        return self.result


class _CommunityPipeline:
    def __init__(self, results) -> None:
        self.results = results
        self.calls = 0

    async def run_once(self):
        self.calls += 1
        return self.results


class _ComplexRegistrySpringClient:
    def __init__(self) -> None:
        self.market_fact_requests = []
        self.market_data_targets = [
            {
                "targetId": "region-seoul-jongno",
                "lawdCode": "11110",
                "enabled": True,
            }
        ]
        self.targets = []
        self.complexes = []
        self.aliases = []
        self.target_edges = []
        self.regions = []

    def list_real_estate_market_facts(self, *, target_id=None, legal_dong_code=None, fact_type=None, limit=20, page=0):
        self.market_fact_requests.append(
            {
                "target_id": target_id,
                "legal_dong_code": legal_dong_code,
                "fact_type": fact_type,
                "limit": limit,
                "page": page,
            }
        )
        if fact_type == "apt_trade" and page == 0:
            return [
                {
                    "factType": "apt_trade",
                    "legalDongCode": "11110",
                    "valueJson": {
                        "apartmentName": "Sajik Palace",
                        "legalDongName": "Sajik-dong",
                        "jibun": "1-1",
                        "builtYear": 2015,
                    },
                }
            ]
        if fact_type == "apt_rent" and page == 0:
            return [
                {
                    "factType": "apt_rent",
                    "legalDongCode": "11110",
                    "valueJson": {
                        "apartmentName": "Sajik Palace",
                        "legalDongName": "Sajik-dong",
                        "jibun": "1-1",
                    },
                }
            ]
        return [
            {
                "factType": "sale_price_index_change_pct",
                "legalDongCode": "00000",
                "valueJson": {"regionName": "전국", "value": 0.2},
            }
        ]

    def list_real_estate_market_data_targets(self, enabled=True):
        return self.market_data_targets

    def list_real_estate_regions(self, *, region_level=None, limit=500):
        if region_level is None:
            return self.regions
        return [region for region in self.regions if region.get("regionLevel") == region_level]

    def publish_real_estate_targets(self, targets) -> None:
        self.targets.extend(targets)

    def publish_real_estate_complexes(self, complexes) -> None:
        self.complexes.extend(complexes)

    def publish_real_estate_aliases(self, aliases) -> None:
        self.aliases.extend(aliases)

    def publish_real_estate_target_edges(self, edges) -> None:
        self.target_edges.extend(edges)


class _CommunityComplexSeedSpringClient:
    def __init__(self) -> None:
        self.post_requests = []
        self.targets = []
        self.complexes = []
        self.aliases = []
        self.target_edges = []

    def list_community_posts_for_reaction_refresh(self, *, source, published_from, published_to, limit):
        self.post_requests.append(
            {
                "source": source,
                "publishedFrom": published_from,
                "publishedTo": published_to,
                "limit": limit,
            }
        )
        return [
            {
                "source": "PPOMPPU",
                "externalId": "post-1",
                "publishedAt": "2026-06-16T01:00:00Z",
                "title": "MRP rent anxiety",
                "contentSnippet": "",
            }
        ]

    def list_real_estate_aliases(self, *, review_state="approved", ambiguous=False, target_type=None, limit=500):
        return [
            {
                "targetType": "complex",
                "targetId": "complex-molit-mrp",
                "alias": "Mapo Raemian Prugio",
                "aliasType": "official",
                "reviewState": "approved",
                "confidence": 0.96,
                "ambiguous": False,
            }
        ]

    def publish_real_estate_targets(self, targets) -> None:
        self.targets.extend(targets)

    def publish_real_estate_complexes(self, complexes) -> None:
        self.complexes.extend(complexes)

    def publish_real_estate_aliases(self, aliases) -> None:
        self.aliases.extend(aliases)

    def publish_real_estate_target_edges(self, edges) -> None:
        self.target_edges.extend(edges)


class _RecentIssueSearchClient:
    def __init__(self) -> None:
        self.queries = []

    def search(self, query: str, *, result_limit: int):
        self.queries.append((query, result_limit))
        if "블로그" in query:
            link = f"https://blog.naver.com/demo/recent-issue-{len(self.queries)}"
        elif "영상" in query:
            link = f"https://www.youtube.com/watch?v=recent{len(self.queries)}"
        elif "리포트" in query:
            link = f"https://www.kbstar.com/report/recent-issue-{len(self.queries)}"
        else:
            link = f"https://example.com/recent-issue-{len(self.queries)}"
        return [
            SerpApiRecentIssueResult(
                title=f"{query} 기사",
                link=link,
                source="Example News",
                snippet="최근 이슈 후보입니다.",
            )
        ]


def test_complex_registry_refresh_job_builds_complex_aliases_and_edges_from_backend_market_facts():
    client = _ComplexRegistrySpringClient()
    job = RealEstateComplexRegistryRefreshJob(client=client, market_fact_limit=100)

    result = job.run_once()

    assert result.status == "OK"
    assert result.market_fact_count == 2
    assert result.target_count == 1
    assert result.complex_count == 1
    assert result.alias_count == 2
    assert result.edge_count == 1
    assert client.market_fact_requests == [
        {
            "target_id": None,
            "legal_dong_code": None,
            "fact_type": "apt_trade",
            "limit": 100,
            "page": 0,
        },
        {
            "target_id": None,
            "legal_dong_code": None,
            "fact_type": "apt_rent",
            "limit": 100,
            "page": 0,
        }
    ]
    assert client.targets[0]["targetType"] == "complex"
    assert client.complexes[0]["regionTargetId"] == "region-seoul-jongno"
    assert [alias["alias"] for alias in client.aliases] == [
        "Sajik Palace",
        "Sajik-dong Sajik Palace",
    ]
    assert client.target_edges[0]["fromTargetId"] == "region-seoul-jongno"
    assert client.target_edges[0]["toTargetId"] == client.targets[0]["targetId"]


def test_complex_registry_refresh_job_links_complex_to_eupmyeondong_when_backend_regions_match_dong_name():
    client = _ComplexRegistrySpringClient()
    client.market_data_targets = [
        {
            "targetId": "region-seoul-mapo",
            "lawdCode": "11440",
            "enabled": True,
        }
    ]
    client.regions = [
        {
            "targetId": "region-seoul-mapo",
            "targetType": "region",
            "displayName": "서울특별시 마포구",
            "regionLevel": "sigungu",
            "parentTargetId": "region-seoul",
            "legalDongCode": "11440",
            "regionCode": "11440",
        },
        {
            "targetId": "region-1144010100",
            "targetType": "region",
            "displayName": "서울특별시 마포구 아현동",
            "regionLevel": "eupmyeondong",
            "parentTargetId": "region-seoul-mapo",
            "legalDongCode": "1144010100",
            "regionCode": "1144010100",
        },
    ]

    def list_market_facts(*, target_id=None, legal_dong_code=None, fact_type=None, limit=20, page=0):
        client.market_fact_requests.append(
            {
                "target_id": target_id,
                "legal_dong_code": legal_dong_code,
                "fact_type": fact_type,
                "limit": limit,
                "page": page,
            }
        )
        if page > 0:
            return []
        if fact_type == "apt_trade":
            return [
                {
                    "factType": "apt_trade",
                    "legalDongCode": "11440",
                    "valueJson": {
                        "apartmentName": "마포 래미안 푸르지오",
                        "legalDongName": "아현동",
                        "jibun": "777",
                    },
                }
            ]
        return []

    client.list_real_estate_market_facts = list_market_facts
    job = RealEstateComplexRegistryRefreshJob(client=client, market_fact_limit=100)

    result = job.run_once()

    assert result.status == "OK"
    assert result.complex_count == 1
    assert client.complexes[0]["regionTargetId"] == "region-1144010100"
    assert client.target_edges[0]["fromTargetId"] == "region-1144010100"


def test_community_complex_seed_refresh_job_reuses_existing_alias_targets():
    from youbuyfirst_pipeline.realestate_community_complex_seed import CommunityComplexSeed

    client = _CommunityComplexSeedSpringClient()
    job = RealEstateCommunityComplexSeedRefreshJob(
        client=client,
        window_minutes=10080,
        posts_limit=5000,
        clock=lambda: datetime(2026, 6, 16, 2, 0, tzinfo=timezone.utc),
        seeds=[
            CommunityComplexSeed(
                target_id="complex-community-mrp",
                display_name="Mapo Raemian Prugio",
                slug="community-mrp",
                region_target_id="region-seoul-mapo",
                aliases=("Mapo Raemian Prugio", "MRP"),
                legal_dong_code="11440",
                address_hint="Seoul Mapo Ahyeon",
            )
        ],
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.post_count == 1
    assert result.observed_target_count == 1
    assert result.target_count == 0
    assert result.complex_count == 0
    assert result.alias_count == 1
    assert result.edge_count == 0
    assert client.post_requests == [
        {
            "source": None,
            "publishedFrom": "2026-06-09T02:00:00Z",
            "publishedTo": "2026-06-16T02:00:00Z",
            "limit": 5000,
        }
    ]
    assert client.targets == []
    assert client.complexes == []
    assert client.target_edges == []
    assert client.aliases[0]["targetId"] == "complex-molit-mrp"
    assert client.aliases[0]["alias"] == "MRP"


def test_complex_registry_refresh_job_paginates_backend_market_facts_before_building_complex_registry():
    client = _ComplexRegistrySpringClient()

    def list_market_facts(*, target_id=None, legal_dong_code=None, fact_type=None, limit=20, page=0):
        client.market_fact_requests.append(
            {
                "target_id": target_id,
                "legal_dong_code": legal_dong_code,
                "fact_type": fact_type,
                "limit": limit,
                "page": page,
            }
        )
        rows_by_type_and_page = {
            ("apt_trade", 0): [
                {
                    "factType": "apt_trade",
                    "legalDongCode": "11110",
                    "providerObjectId": "molit:trade:1",
                    "valueJson": {
                        "apartmentName": "Sajik Palace",
                        "legalDongName": "Sajik-dong",
                        "jibun": "1-1",
                    },
                },
                {
                    "factType": "apt_trade",
                    "legalDongCode": "11110",
                    "providerObjectId": "molit:trade:2",
                    "valueJson": {
                        "apartmentName": "Gwanghwamun Central",
                        "legalDongName": "Sajik-dong",
                        "jibun": "2-2",
                    },
                },
            ],
            ("apt_trade", 1): [
                {
                    "factType": "apt_trade",
                    "legalDongCode": "11110",
                    "providerObjectId": "molit:trade:3",
                    "valueJson": {
                        "apartmentName": "Jongno House",
                        "legalDongName": "Sajik-dong",
                        "jibun": "3-3",
                    },
                }
            ],
            ("apt_rent", 0): [
                {
                    "factType": "apt_rent",
                    "legalDongCode": "11110",
                    "providerObjectId": "molit:rent:1",
                    "valueJson": {
                        "apartmentName": "Sajik Rent",
                        "legalDongName": "Sajik-dong",
                        "jibun": "4-4",
                    },
                }
            ],
        }
        return rows_by_type_and_page.get((fact_type, page), [])

    client.list_real_estate_market_facts = list_market_facts
    job = RealEstateComplexRegistryRefreshJob(client=client, market_fact_limit=2)

    result = job.run_once()

    assert result.status == "OK"
    assert result.market_fact_count == 4
    assert result.complex_count == 4
    assert client.market_fact_requests == [
        {"target_id": None, "legal_dong_code": None, "fact_type": "apt_trade", "limit": 2, "page": 0},
        {"target_id": None, "legal_dong_code": None, "fact_type": "apt_trade", "limit": 2, "page": 1},
        {"target_id": None, "legal_dong_code": None, "fact_type": "apt_rent", "limit": 2, "page": 0},
    ]


class _RecentIssueSpringClient:
    def __init__(self, *, map_layer_targets_enabled: bool = False) -> None:
        self.content_batches = []
        self.ranking_calls = []
        self.map_layer_calls = []
        self.map_layer_targets_enabled = map_layer_targets_enabled

    def get_real_estate_reaction_ranking(self, *, target_type: str, window_minutes: int, limit: int):
        self.ranking_calls.append(
            {
                "target_type": target_type,
                "window_minutes": window_minutes,
                "limit": limit,
            }
        )
        return {
            "window": "60m",
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
            "items": [
                {
                    "targetId": "region-daejeon",
                    "targetType": "region",
                    "displayName": "대전광역시",
                    "issueMix": [
                        {"label": "교통"},
                        {"label": "정책"},
                    ],
                },
                {
                    "targetId": "region-seoul-mapo",
                    "targetType": "region",
                    "displayName": "서울 마포구",
                    "issueMix": [],
                },
            ],
        }

    def publish_real_estate_content_items(self, items) -> None:
        self.content_batches.append([item.to_content_item_dict() for item in items])

    def list_real_estate_map_layer_targets(
        self,
        *,
        layer_type: str = "sido",
        parent_target_id: str | None = None,
        period: str = "month",
        limit: int = 100,
    ):
        self.map_layer_calls.append(
            {
                "layer_type": layer_type,
                "parent_target_id": parent_target_id,
                "period": period,
                "limit": limit,
            }
        )
        if not self.map_layer_targets_enabled:
            return []
        return [
            {
                "targetId": "region-seoul-mapo",
                "targetType": "region",
                "displayName": "Seoul Mapo",
                "periods": {
                    "month": {
                        "changePct": 0.31,
                        "confidence": 0.72,
                        "sourceLabel": "REB",
                        "dataStatus": "ok",
                    }
                },
            },
            {
                "targetId": "region-busan",
                "targetType": "region",
                "displayName": "Busan",
                "periods": {
                    "month": {
                        "changePct": -0.22,
                        "confidence": 0.68,
                        "sourceLabel": "REB",
                        "dataStatus": "ok",
                    }
                },
            },
            {
                "targetId": "region-daegu",
                "targetType": "region",
                "displayName": "Daegu",
                "periods": {
                    "month": {
                        "changePct": 0.12,
                        "confidence": 0.66,
                        "sourceLabel": "REB",
                        "dataStatus": "ok",
                    }
                },
            },
        ][:limit]


class _EvidenceSpringClient:
    def __init__(self, ranking: dict | None = None, *, map_layer_targets_enabled: bool = False) -> None:
        self.ranking = ranking or {
            "window": "60m",
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
            "freshness": {
                "source": "real_estate_reaction_snapshots",
                "asOf": "2026-06-14T01:02:00Z",
                "coverageStatus": "partial",
            },
            "items": [
                {
                    "targetId": "region-daejeon",
                    "targetType": "region",
                    "displayName": "대전",
                    "mentionCount": 24,
                    "reactionDirectionRatio": {
                        "expectation": 0.58,
                        "concern": 0.27,
                        "neutral": 0.15,
                    },
                    "heatScore": 81,
                    "confidence": 0.74,
                    "sourceCount": 2,
                    "sourceSkew": 0.41,
                    "coverageStatus": "partial",
                    "stale": False,
                    "issueMix": [
                        {
                            "issueKey": "transport",
                            "label": "교통",
                            "share": 0.45,
                            "direction": "expectation",
                            "summary": "광역 교통 기대가 반복됩니다.",
                            "confidence": 0.7,
                        }
                    ],
                }
            ],
        }
        self.ranking_calls = []
        self.market_fact_calls = []
        self.general_market_fact_calls = []
        self.content_calls = []
        self.timeline_calls = []
        self.map_layer_calls = []
        self.published_logs = []
        self.target_market_facts_enabled = True
        self.map_layer_targets_enabled = map_layer_targets_enabled

    def get_real_estate_reaction_ranking(self, *, target_type: str, window_minutes: int, limit: int):
        self.ranking_calls.append(
            {
                "target_type": target_type,
                "window_minutes": window_minutes,
                "limit": limit,
            }
        )
        return self.ranking

    def list_real_estate_target_market_facts(self, target_id: str, *, limit: int):
        self.market_fact_calls.append({"target_id": target_id, "limit": limit})
        if not self.target_market_facts_enabled:
            return []
        return [
            {
                "targetId": target_id,
                "factType": "apt_trade",
                "providerObjectId": "molit_apt_trade:30110:202606:1",
                "observedAt": "2026-06-03",
                "valueJson": {"dealAmountManwon": 42000},
            }
        ]

    def list_real_estate_market_facts(
        self,
        *,
        target_id: str | None = None,
        legal_dong_code: str | None = None,
        fact_type: str | None = None,
        limit: int,
        page: int = 0,
    ):
        self.general_market_fact_calls.append(
            {
                "target_id": target_id,
                "legal_dong_code": legal_dong_code,
                "fact_type": fact_type,
                "limit": limit,
                "page": page,
            }
        )
        return [
            {
                "targetId": None,
                "legalDongCode": "00000",
                "factType": "sale_price_index_change_pct",
                "providerObjectId": "reb_rone_main_snapshot:A202:202606",
                "observedAt": "2026-06-01",
                "valueJson": {"value": 0.12, "unit": "%"},
            }
        ]

    def list_real_estate_target_content_items(self, target_id: str, *, feed: str, limit: int):
        self.content_calls.append({"target_id": target_id, "feed": feed, "limit": limit})
        return [
            {
                "contentId": "serpapi-region-daejeon-transport",
                "title": "대전 교통 이슈 후보",
                "targetId": target_id,
                "linkType": "search_candidate",
                "reviewState": "candidate",
            }
        ]

    def list_real_estate_target_timeline_events(self, target_id: str, *, limit: int):
        self.timeline_calls.append({"target_id": target_id, "limit": limit})
        return [
            {
                "id": "policy-event-supply-daejeon-region-daejeon-primary",
                "targetId": target_id,
                "eventType": "supply",
                "sourceRefType": "policy_event",
                "sourceRefId": "policy-event-supply-daejeon",
                "title": "대전 도심 공급계획 발표",
                "summary": "도심 공급 후보지와 교통 개선 일정이 함께 언급됩니다.",
                "occurredAt": "2026-06-09T00:00:00Z",
                "asOf": "2026-06-09T00:00:00Z",
                "dataStatus": "approved",
            }
        ]

    def publish_real_estate_evidence_logs(self, logs) -> None:
        self.published_logs.append(list(logs))

    def list_real_estate_map_layer_targets(
        self,
        *,
        layer_type: str = "sido",
        parent_target_id: str | None = None,
        period: str = "month",
        limit: int = 100,
    ):
        self.map_layer_calls.append(
            {
                "layer_type": layer_type,
                "parent_target_id": parent_target_id,
                "period": period,
                "limit": limit,
            }
        )
        if not self.map_layer_targets_enabled:
            return []
        return [
            {
                "targetId": "region-daejeon",
                "targetType": "region",
                "displayName": "Daejeon",
                "periods": {"month": {"changePct": 0.18, "confidence": 0.70, "dataStatus": "ok"}},
            },
            {
                "targetId": "region-busan",
                "targetType": "region",
                "displayName": "Busan",
                "periods": {"month": {"changePct": -0.22, "confidence": 0.68, "dataStatus": "ok"}},
            },
            {
                "targetId": "region-daegu",
                "targetType": "region",
                "displayName": "Daegu",
                "periods": {"month": {"changePct": 0.12, "confidence": 0.66, "dataStatus": "ok"}},
            },
        ][:limit]


class _MapLayerSpringClient:
    def __init__(self) -> None:
        self.calls = []

    def refresh_real_estate_map_layer_snapshots(self, *, layer_type: str, periods, as_of: str):
        self.calls.append({"layer_type": layer_type, "periods": list(periods), "as_of": as_of})
        return {
            "layerType": layer_type,
            "periods": list(periods),
            "asOf": as_of,
            "acceptedSnapshots": 2 if layer_type == "sido" else 1,
            "skippedTargets": 3,
        }


class _OfficialStatsSpringClient:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.published_batches = []

    def publish_real_estate_market_facts(self, facts) -> None:
        if self.fail:
            raise RuntimeError("backend unavailable")
        self.published_batches.append(list(facts))


def test_daily_refresh_job_runs_steps_in_order_and_summarizes_ok_status():
    market_step = _Step({"status": "OK", "fact_count": 3})
    reaction_step = _Step({"status": "OK", "snapshot_count": 2})
    job = RealEstateDailyRefreshJob(
        [
            ("market_facts", market_step),
            ("reaction_snapshots", reaction_step),
        ]
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.step_count == 2
    assert result.ok_count == 2
    assert result.failed_count == 0
    assert [step.name for step in result.steps] == ["market_facts", "reaction_snapshots"]
    assert market_step.calls == 1
    assert reaction_step.calls == 1


def test_daily_refresh_job_marks_partial_when_a_step_fails():
    job = RealEstateDailyRefreshJob(
        [
            ("market_facts", _Step({"status": "OK"})),
            ("reaction_snapshots", _Step(fail=True)),
        ]
    )

    result = job.run_once()

    assert result.status == "PARTIAL"
    assert result.ok_count == 1
    assert result.failed_count == 1
    assert result.steps[1].status == "ERROR"


def test_daily_refresh_job_marks_partial_when_a_step_needs_attention():
    job = RealEstateDailyRefreshJob(
        [
            ("market_facts", _Step({"status": "OK"})),
            ("recent_issues", _Step({"status": "CONFIG_MISSING", "missing": ["SERPAPI_API_KEY"]})),
            ("evidence_logs", _Step({"status": "PARTIAL", "log_count": 1})),
        ]
    )

    result = job.run_once()

    assert result.status == "PARTIAL"
    assert result.ok_count == 3
    assert result.failed_count == 0
    assert [step.status for step in result.steps] == ["OK", "CONFIG_MISSING", "PARTIAL"]


def test_daily_refresh_job_marks_partial_when_complex_registry_is_empty():
    job = RealEstateDailyRefreshJob(
        [
            ("market_facts", _Step({"status": "OK", "fact_count": 12})),
            ("complex_registry", _Step({"status": "EMPTY", "market_fact_count": 0, "complex_count": 0})),
            ("reaction_snapshots", _Step({"status": "EMPTY", "snapshot_count": 0})),
        ]
    )

    result = job.run_once()

    assert result.status == "PARTIAL"
    assert result.ok_count == 3
    assert result.failed_count == 0
    assert [step.status for step in result.steps] == ["OK", "EMPTY", "EMPTY"]


def test_daily_refresh_job_serializes_reaction_snapshot_type_counts_as_camel_case():
    job = RealEstateDailyRefreshJob(
        [
            (
                "reaction_snapshots",
                _Step(
                    RealEstateReactionSnapshotRefreshResult(
                        status="OK",
                        observation_count=2,
                        snapshot_count=2,
                        snapshot_counts_by_type={"complex": 1, "region": 1},
                    )
                ),
            )
        ]
    )

    payload = job.run_once().to_dict()

    detail = payload["steps"][0]["detail"]
    assert detail["observationCount"] == 2
    assert detail["snapshotCount"] == 2
    assert detail["snapshotCountsByType"] == {"complex": 1, "region": 1}
    assert "snapshot_counts_by_type" not in detail


def test_daily_refresh_job_summarizes_top10_readiness_from_complex_registry_and_snapshots():
    job = RealEstateDailyRefreshJob(
        [
            (
                "complex_registry",
                _Step(
                    RealEstateComplexRegistryRefreshResult(
                        status="OK",
                        market_fact_count=20,
                        target_count=10,
                        complex_count=10,
                        alias_count=20,
                        edge_count=10,
                    )
                ),
            ),
            (
                "community_complex_seed",
                _Step(
                    {
                        "status": "OK",
                        "observedTargetCount": 10,
                        "targetCount": 10,
                        "aliasCount": 10,
                        "edgeCount": 10,
                    }
                ),
            ),
            (
                "reaction_snapshots",
                _Step(
                    RealEstateReactionSnapshotRefreshResult(
                        status="OK",
                        observation_count=20,
                        snapshot_count=20,
                        snapshot_counts_by_type={"complex": 10, "region": 10},
                    )
                ),
            ),
        ]
    )

    payload = job.run_once().to_dict()

    assert payload["top10Readiness"] == {
        "status": "READY",
        "missing": [],
        "complexRegistry": {
            "complexCount": 10,
            "aliasCount": 20,
            "edgeCount": 10,
        },
        "communityComplexSeed": {
            "observedTargetCount": 10,
            "targetCount": 10,
            "aliasCount": 10,
            "edgeCount": 10,
        },
        "reactionSnapshots": {
            "complex": 10,
            "region": 10,
        },
        "frontTop10": {
            "requiredItems": 10,
        },
    }


def test_daily_refresh_job_marks_top10_partial_when_snapshot_counts_are_short():
    job = RealEstateDailyRefreshJob(
        [
            (
                "complex_registry",
                _Step(
                    RealEstateComplexRegistryRefreshResult(
                        status="OK",
                        market_fact_count=20,
                        target_count=10,
                        complex_count=10,
                        alias_count=20,
                        edge_count=10,
                    )
                ),
            ),
            (
                "community_complex_seed",
                _Step(
                    {
                        "status": "OK",
                        "observedTargetCount": 8,
                        "targetCount": 8,
                        "aliasCount": 8,
                        "edgeCount": 8,
                    }
                ),
            ),
            (
                "reaction_snapshots",
                _Step(
                    RealEstateReactionSnapshotRefreshResult(
                        status="OK",
                        observation_count=17,
                        snapshot_count=17,
                        snapshot_counts_by_type={"complex": 8, "region": 9},
                    )
                ),
            ),
        ]
    )

    payload = job.run_once().to_dict()

    assert payload["top10Readiness"]["status"] == "PARTIAL"
    assert payload["top10Readiness"]["missing"] == [
        "complex_top10_short",
        "region_top10_short",
    ]
    assert payload["top10Readiness"]["frontTop10"] == {
        "requiredItems": 10,
    }


def test_daily_refresh_job_requires_community_complex_seed_before_snapshots_for_top10_readiness():
    job = RealEstateDailyRefreshJob(
        [
            (
                "complex_registry",
                _Step(
                    RealEstateComplexRegistryRefreshResult(
                        status="OK",
                        market_fact_count=2,
                        target_count=1,
                        complex_count=1,
                        alias_count=4,
                        edge_count=1,
                    )
                ),
            ),
            (
                "reaction_snapshots",
                _Step(
                    RealEstateReactionSnapshotRefreshResult(
                        status="OK",
                        observation_count=2,
                        snapshot_count=2,
                        snapshot_counts_by_type={"complex": 1, "region": 1},
                    )
                ),
            ),
        ]
    )

    payload = job.run_once().to_dict()

    assert payload["top10Readiness"]["status"] == "PARTIAL"
    assert payload["top10Readiness"]["missing"] == [
        "community_complex_seed_missing",
        "complex_top10_short",
        "region_top10_short",
    ]


def test_daily_refresh_job_does_not_mark_top10_ready_when_complex_registry_runs_after_snapshots():
    job = RealEstateDailyRefreshJob(
        [
            (
                "reaction_snapshots",
                _Step(
                    RealEstateReactionSnapshotRefreshResult(
                        status="OK",
                        observation_count=2,
                        snapshot_count=2,
                        snapshot_counts_by_type={"complex": 1, "region": 1},
                    )
                ),
            ),
            (
                "complex_registry",
                _Step(
                    RealEstateComplexRegistryRefreshResult(
                        status="OK",
                        market_fact_count=2,
                        target_count=1,
                        complex_count=1,
                        alias_count=4,
                        edge_count=1,
                    )
                ),
            ),
        ]
    )

    payload = job.run_once().to_dict()

    assert payload["top10Readiness"]["status"] == "PARTIAL"
    assert payload["top10Readiness"]["missing"] == ["complex_registry_order_invalid"]


def test_official_stats_refresh_job_pushes_collected_facts_to_market_facts():
    client = _OfficialStatsSpringClient()
    job = RealEstateOfficialStatsRefreshJob(
        client=client,
        collector=lambda: ["sale-index", "jeonse-index"],
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.provider == "reb"
    assert result.provider_dataset == "reb_rone_monthly_apt_sale_price_index"
    assert result.fact_count == 2
    assert client.published_batches == [["sale-index", "jeonse-index"]]


def test_official_stats_refresh_job_marks_provider_error_without_push():
    client = _OfficialStatsSpringClient()

    def failing_collector():
        raise RuntimeError("provider failed")

    job = RealEstateOfficialStatsRefreshJob(client=client, collector=failing_collector)

    result = job.run_once()

    assert result.status == "PROVIDER_ERROR"
    assert result.fact_count == 0
    assert client.published_batches == []


def test_official_stats_refresh_job_marks_client_error_when_backend_push_fails():
    client = _OfficialStatsSpringClient(fail=True)
    job = RealEstateOfficialStatsRefreshJob(client=client, collector=lambda: ["sale-index"])

    result = job.run_once()

    assert result.status == "CLIENT_ERROR"
    assert result.fact_count == 1


def test_community_crawl_refresh_job_runs_pipeline_and_summarizes_results():
    pipeline = _CommunityPipeline(
        [
            {
                "source": "PPOMPPU",
                "status": "OK",
                "seenPosts": 8,
                "acceptedPosts": 5,
            },
            {
                "source": "DCINSIDE",
                "status": "blocked",
                "seenPosts": 2,
                "acceptedPosts": 0,
            },
        ]
    )
    job = RealEstateCommunityCrawlRefreshJob(pipeline=pipeline)

    result = job.run_once()

    assert pipeline.calls == 1
    assert result.status == "PARTIAL"
    assert result.source_count == 2
    assert result.seen_post_count == 10
    assert result.accepted_post_count == 5
    assert result.blocked_count == 1
    assert result.failed_count == 0


def test_community_crawl_refresh_job_can_run_inside_existing_event_loop():
    pipeline = _CommunityPipeline(
        [
            {
                "source": "PPOMPPU",
                "status": "OK",
                "seenPosts": 2,
                "acceptedPosts": 1,
            }
        ]
    )
    job = RealEstateCommunityCrawlRefreshJob(pipeline=pipeline)

    async def run_job():
        return job.run_once()

    result = asyncio.run(run_job())

    assert result.status == "OK"
    assert result.source_count == 1
    assert result.seen_post_count == 2
    assert result.accepted_post_count == 1


def test_recent_issues_refresh_job_publishes_candidate_content(tmp_path):
    targets_path = tmp_path / "targets.jsonl"
    targets_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","displayName":"대전","keywords":["교통"]}',
        encoding="utf-8",
    )
    spring_client = _RecentIssueSpringClient()
    search_client = _RecentIssueSearchClient()
    job = RealEstateRecentIssuesRefreshJob(
        client=spring_client,
        search_client=search_client,
        search_targets_jsonl=targets_path,
        issue_keywords=("교통",),
        result_limit=2,
        clock=lambda: datetime(2026, 6, 14, 0, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.target_count == 1
    assert result.item_count == 1
    assert search_client.queries == [("대전 교통 부동산", 2)]
    assert spring_client.content_batches[0][0]["dataStatus"] == "candidate"
    assert spring_client.content_batches[0][0]["targets"][0]["targetId"] == "region-daejeon"


def test_recent_issues_refresh_job_can_use_latest_backend_ranking_as_search_targets():
    spring_client = _RecentIssueSpringClient()
    search_client = _RecentIssueSearchClient()
    job = RealEstateRecentIssuesRefreshJob(
        client=spring_client,
        search_client=search_client,
        search_targets_jsonl=None,
        issue_keywords=(),
        target_type="region",
        window_minutes=60,
        ranking_limit=2,
        result_limit=2,
        clock=lambda: datetime(2026, 6, 14, 0, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.target_count == 2
    assert result.item_count == 9
    assert spring_client.ranking_calls == [
        {
            "target_type": "region",
            "window_minutes": 60,
            "limit": 2,
        }
    ]
    queries = [query for query, _limit in search_client.queries]
    assert len(search_client.queries) == 9
    assert any("블로그" in query for query in queries)
    assert any("영상" in query for query in queries)
    assert any("리포트" in query for query in queries)
    assert {item["targets"][0]["targetId"] for item in spring_client.content_batches[0]} == {
        "region-daejeon",
        "region-seoul-mapo",
    }


def test_recent_issues_refresh_job_fills_reaction_ranking_with_map_layer_targets():
    spring_client = _RecentIssueSpringClient(map_layer_targets_enabled=True)
    search_client = _RecentIssueSearchClient()
    job = RealEstateRecentIssuesRefreshJob(
        client=spring_client,
        search_client=search_client,
        search_targets_jsonl=None,
        issue_keywords=(),
        target_type="region",
        window_minutes=60,
        ranking_limit=4,
        result_limit=2,
        clock=lambda: datetime(2026, 6, 14, 0, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.target_count == 4
    assert spring_client.map_layer_calls == [
        {
            "layer_type": "sido",
            "parent_target_id": None,
            "period": "month",
            "limit": 8,
        }
    ]
    assert {item["targets"][0]["targetId"] for item in spring_client.content_batches[0]} == {
        "region-daejeon",
        "region-seoul-mapo",
        "region-busan",
        "region-daegu",
    }


def test_evidence_log_refresh_job_builds_logs_from_latest_backend_snapshots():
    spring_client = _EvidenceSpringClient()
    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        target_type="region",
        window_minutes=60,
        ranking_limit=1,
        market_fact_limit=10,
        content_limit=10,
        timeline_limit=10,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.target_count == 1
    assert result.log_count == 1
    assert result.market_fact_count == 1
    assert result.timeline_event_count == 1
    assert result.content_item_count == 1
    assert spring_client.ranking_calls == [
        {
            "target_type": "region",
            "window_minutes": 60,
            "limit": 1,
        }
    ]
    published_log = spring_client.published_logs[0][0]
    assert published_log["targetId"] == "region-daejeon"
    assert published_log["evaluatedAt"] == "2026-06-14T02:00:00Z"
    assert "market_fact_missing" not in published_log["caveats"]
    assert "timeline_event_missing" not in published_log["caveats"]
    assert "search_candidate_missing" not in published_log["caveats"]
    assert {item["evidenceType"] for item in published_log["evidenceItems"]} == {
        "reaction",
        "market_fact",
        "timeline_event",
        "search_candidate",
    }


def test_evidence_log_refresh_job_fills_reaction_ranking_with_map_layer_rows():
    spring_client = _EvidenceSpringClient(map_layer_targets_enabled=True)
    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        target_type="region",
        window_minutes=60,
        ranking_limit=3,
        market_fact_limit=10,
        content_limit=10,
        timeline_limit=10,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "PARTIAL"
    assert result.target_count == 3
    assert result.log_count == 3
    assert spring_client.map_layer_calls == [
        {
            "layer_type": "sido",
            "parent_target_id": None,
            "period": "month",
            "limit": 6,
        }
    ]
    assert [log["targetId"] for log in spring_client.published_logs[0]] == [
        "region-daejeon",
        "region-busan",
        "region-daegu",
    ]
    fallback_log = spring_client.published_logs[0][1]
    assert fallback_log["targetId"] == "region-busan"
    assert "market_data_only" in fallback_log["caveats"]


def test_evidence_log_refresh_job_uses_national_market_fact_context_when_target_fact_is_missing():
    spring_client = _EvidenceSpringClient()
    spring_client.target_market_facts_enabled = False
    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        target_type="region",
        window_minutes=60,
        ranking_limit=5,
        market_fact_limit=3,
        content_limit=10,
        timeline_limit=10,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "PARTIAL"
    assert result.market_fact_count == 1
    assert spring_client.general_market_fact_calls == [
        {
            "target_id": None,
            "legal_dong_code": "00000",
            "fact_type": None,
            "limit": 3,
            "page": 0,
        }
    ]
    published_log = spring_client.published_logs[0][0]
    assert "market_fact_missing" not in published_log["caveats"]
    assert "national_market_fact_only" in published_log["caveats"]
    market_fact_item = next(item for item in published_log["evidenceItems"] if item["evidenceType"] == "market_fact")
    assert market_fact_item["refType"] == "national_market_fact"
    assert market_fact_item["label"] == "전국 배경 시장 사실: 매매가격지수 변동률"
    assert market_fact_item["valueText"] == "매매가격지수 변동률 +0.12%"


def test_evidence_log_refresh_job_can_attach_similar_window_candidates():
    spring_client = _EvidenceSpringClient()
    similar_calls = []

    def similar_windows_provider(target_id: str, ranking_row: dict, ranking: dict):
        similar_calls.append(
            {
                "target_id": target_id,
                "window_start": ranking["windowStart"],
                "row_target_id": ranking_row["targetId"],
            }
        )
        return [
            {
                "sourceTargetId": target_id,
                "matchedTargetId": "region-gwangju",
                "matchedWindowStart": "2026-03-01T00:00:00Z",
                "matchedWindowEnd": "2026-03-01T01:00:00Z",
                "similarityScore": 0.91,
                "evidenceItem": {
                    "evidenceItemId": "similar-region-daejeon-region-gwangju",
                    "evidenceType": "similar_window",
                    "refType": "similar_window",
                    "refId": "snapshot-gwangju-20260301000000",
                    "label": "유사 과거 window",
                    "valueText": "유사도 91.0% · 매매 +6.0%",
                    "severity": "info",
                },
            }
        ]

    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        similar_windows_provider=similar_windows_provider,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.similar_window_count == 1
    assert similar_calls == [
        {
            "target_id": "region-daejeon",
            "window_start": "2026-06-14T00:00:00Z",
            "row_target_id": "region-daejeon",
        }
    ]
    published_log = spring_client.published_logs[0][0]
    assert "similar_window_missing" not in published_log["caveats"]
    assert {item["evidenceType"] for item in published_log["evidenceItems"]} == {
        "reaction",
        "market_fact",
        "timeline_event",
        "similar_window",
        "search_candidate",
    }


def test_evidence_log_refresh_job_can_apply_llm_evaluator_before_publish():
    spring_client = _EvidenceSpringClient()
    llm_calls = []

    def llm_evaluator(log):
        llm_calls.append(log)
        updated = dict(log)
        updated["summary"] = "관심이 빠르게 증가했고 교통 쟁점이 함께 확인됩니다."
        updated["modelName"] = "gpt-5-mini"
        updated["promptVersion"] = "gms-evidence-v1"
        return updated

    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
        llm_evaluator=llm_evaluator,
    )

    result = job.run_once()

    assert result.status == "OK"
    assert len(llm_calls) == 1
    published_log = spring_client.published_logs[0][0]
    assert published_log["summary"] == "관심이 빠르게 증가했고 교통 쟁점이 함께 확인됩니다."
    assert published_log["modelName"] == "gpt-5-mini"
    assert published_log["promptVersion"] == "gms-evidence-v1"


def test_evidence_log_refresh_job_publishes_rule_log_when_llm_evaluator_fails():
    spring_client = _EvidenceSpringClient()
    llm_calls = []

    def llm_evaluator(log):
        llm_calls.append(log)
        raise TimeoutError("gms read timed out")

    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
        llm_evaluator=llm_evaluator,
    )

    result = job.run_once()

    assert result.status == "PARTIAL"
    assert result.log_count == 1
    assert result.llm_error_count == 1
    assert len(llm_calls) == 1
    published_log = spring_client.published_logs[0][0]
    assert "llm_evaluation_failed" in published_log["caveats"]
    assert published_log["dataQuality"] == "partial"
    assert published_log["summary"]


def test_evidence_log_refresh_job_skips_publish_when_latest_ranking_is_empty():
    spring_client = _EvidenceSpringClient(
        ranking={
            "window": "60m",
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
            "freshness": {
                "source": "real_estate_reaction_snapshots",
                "asOf": "2026-06-14T01:02:00Z",
                "coverageStatus": "empty",
            },
            "items": [],
        }
    )
    job = RealEstateEvidenceLogRefreshJob(client=spring_client)

    result = job.run_once()

    assert result.status == "EMPTY"
    assert result.target_count == 0
    assert result.log_count == 0
    assert spring_client.published_logs == []


def test_evidence_log_refresh_job_marks_partial_when_search_candidates_are_missing():
    class _NoContentEvidenceSpringClient(_EvidenceSpringClient):
        def list_real_estate_target_content_items(self, target_id: str, *, feed: str, limit: int):
            self.content_calls.append({"target_id": target_id, "feed": feed, "limit": limit})
            return []

    spring_client = _NoContentEvidenceSpringClient()
    job = RealEstateEvidenceLogRefreshJob(
        client=spring_client,
        target_type="region",
        window_minutes=60,
        ranking_limit=5,
        clock=lambda: datetime(2026, 6, 14, 2, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "PARTIAL"
    assert result.log_count == 1
    assert result.content_item_count == 0
    published_log = spring_client.published_logs[0][0]
    assert "search_candidate_missing" in published_log["caveats"]


def test_ranking_with_window_defaults_ends_at_refresh_time_not_future_midnight_window():
    ranking = _ranking_with_window_defaults(
        {},
        window_minutes=10_080,
        now=datetime(2026, 6, 21, 9, 30, tzinfo=timezone.utc),
    )

    assert ranking["windowStart"] == "2026-06-14T09:30:00Z"
    assert ranking["windowEnd"] == "2026-06-21T09:30:00Z"
    assert ranking["freshness"]["asOf"] == "2026-06-21T09:30:00Z"


def test_map_layer_refresh_job_calls_backend_for_each_layer_type():
    spring_client = _MapLayerSpringClient()
    job = RealEstateMapLayerRefreshJob(
        client=spring_client,
        layer_types=("sido", "sigungu"),
        periods=("month", "halfYear"),
        clock=lambda: datetime(2026, 6, 21, 0, 0, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.layer_count == 2
    assert result.snapshot_count == 3
    assert result.skipped_target_count == 6
    assert spring_client.calls == [
        {
            "layer_type": "sido",
            "periods": ["month", "halfYear"],
            "as_of": "2026-06-21T00:00:00Z",
        },
        {
            "layer_type": "sigungu",
            "periods": ["month", "halfYear"],
            "as_of": "2026-06-21T00:00:00Z",
        },
    ]
