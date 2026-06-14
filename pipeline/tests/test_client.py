from youbuyfirst_pipeline.client import SpringIngestionClient


class _Response:
    def __init__(self, json_payload: dict | None = None) -> None:
        self.json_payload = json_payload or {}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.json_payload


class _FakeHttpxClient:
    posts: list[dict] = []
    gets: list[dict] = []

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self) -> "_FakeHttpxClient":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def post(self, url: str, json: dict) -> _Response:
        self.posts.append({"url": url, "json": json, "timeout": self.timeout})
        if url.endswith("/internal/realestate/public-data/promote-staging"):
            return _Response({"promotedFacts": 1})
        if url.endswith("/internal/realestate/map/layer-snapshots/refresh"):
            return _Response(
                {
                    "layerType": json["layerType"],
                    "periods": json["periods"],
                    "asOf": json["asOf"],
                    "acceptedSnapshots": 2,
                    "skippedTargets": 1,
                }
            )
        return _Response()

    def get(self, url: str, params: dict | None = None) -> _Response:
        self.gets.append({"url": url, "params": params, "timeout": self.timeout})
        if url.endswith("/internal/realestate/aliases"):
            return _Response(
                {
                    "items": [
                        {
                            "targetType": "region",
                            "targetId": "region-seoul-jongno",
                            "alias": "jongno-newbuild",
                            "aliasType": "community_slang",
                            "reviewState": "approved",
                            "confidence": 0.91,
                            "ambiguous": False,
                            "source": "manual:review",
                        }
                    ]
                }
            )
        if url.endswith("/internal/realestate/target-edges"):
            return _Response(
                {
                    "items": [
                        {
                            "fromTargetType": "region",
                            "fromTargetId": "region-seoul",
                            "toTargetType": "region",
                            "toTargetId": "region-seoul-jongno",
                            "edgeType": "contains",
                            "reviewState": "approved",
                            "confidence": 0.9,
                            "source": "admin:registry",
                        }
                    ]
                }
            )
        if url.endswith("/internal/realestate/public-data/import-runs"):
            return _Response(
                {
                    "items": [
                        {
                            "runKey": "molit_apt_trade:11110:202606",
                            "providerDataset": "molit_apt_trade",
                            "status": "completed",
                            "rowsLanded": 12,
                        }
                    ]
                }
            )
        if url.endswith("/api/realestate/reactions/rankings"):
            return _Response(
                {
                    "window": "60m",
                    "windowStart": "2026-06-14T00:00:00Z",
                    "windowEnd": "2026-06-14T01:00:00Z",
                    "freshness": {
                        "source": "real_estate_reaction_snapshots",
                        "asOf": "2026-06-14T01:02:00Z",
                        "staleCount": 0,
                        "sourceCount": 2,
                        "coverageStatus": "partial",
                    },
                    "items": [
                        {
                            "rank": 1,
                            "targetId": "region-daejeon",
                            "targetType": "region",
                            "displayName": "대전",
                            "mentionCount": 24,
                            "mentionDeltaPct": 38.5,
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
            )
        if url.endswith("/api/realestate/targets/region-daejeon/market-facts"):
            return _Response(
                {
                    "items": [
                        {
                            "targetId": "region-daejeon",
                            "factType": "apt_trade",
                            "providerObjectId": "molit_apt_trade:30110:202606:1",
                            "observedAt": "2026-06-03",
                            "valueJson": {"dealAmountManwon": 42000},
                        }
                    ]
                }
            )
        if url.endswith("/api/realestate/targets/region-daejeon/content"):
            return _Response(
                {
                    "items": [
                        {
                            "contentId": "serpapi-region-daejeon-transport",
                            "title": "대전 교통 이슈 후보",
                            "targetId": "region-daejeon",
                            "linkType": "search_candidate",
                            "reviewState": "candidate",
                        }
                    ]
                }
            )
        if url.endswith("/api/realestate/targets/region-daejeon/timeline"):
            return _Response(
                {
                    "items": [
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
                    ]
                }
            )
        return _Response(
            {
                "items": [
                    {
                        "targetId": "region-seoul-jongno",
                        "provider": "molit",
                        "providerDataset": "molit_apt_trade",
                        "lawdCode": "11110",
                        "enabled": True,
                    }
                ]
            }
        )


class _MarketFact:
    def __init__(self, provider_object_id: str) -> None:
        self.provider_object_id = provider_object_id

    def to_ingestion_dict(self) -> dict:
        return {
            "provider": "molit",
            "providerDataset": "molit_apt_trade",
            "providerObjectId": self.provider_object_id,
            "factType": "apt_trade",
        }


class _RegionImport:
    def __init__(self, target_id: str, display_name: str) -> None:
        self.target_id = target_id
        self.display_name = display_name

    def to_import_dict(self) -> dict:
        return {
            "targetId": self.target_id,
            "displayName": self.display_name,
            "regionLevel": "sigungu",
            "legalDongCode": "26350",
        }


class _ReactionSnapshot:
    def __init__(self, target_id: str) -> None:
        self.target_id = target_id

    def to_request_dict(self) -> dict:
        return {
            "targetType": "region",
            "targetId": self.target_id,
            "windowStart": "2026-06-11T00:00:00Z",
            "windowEnd": "2026-06-11T01:00:00Z",
            "asOf": "2026-06-11T01:02:00Z",
            "mentionCount": 4,
            "previousMentionCount": 2,
            "expectationScore": 50,
            "concernScore": 25,
            "neutralScore": 25,
            "heatScore": 71,
            "confidence": 0.66,
            "sourceCount": 3,
            "sourceSkew": 0.5,
            "coverageStatus": "partial",
            "stale": False,
            "issues": [],
        }


class _ContentItem:
    def __init__(self, content_id: str) -> None:
        self.content_id = content_id

    def to_content_item_dict(self) -> dict:
        return {
            "contentId": self.content_id,
            "sourceId": "serpapi:google_news",
            "contentType": "news",
            "title": "대전 교통 이슈 후보",
            "url": "https://example.com/daejeon-transport",
            "ingestedAt": "2026-06-12T01:30:00Z",
            "dataStatus": "candidate",
            "targets": [
                {
                    "targetId": "region-daejeon",
                    "linkType": "search_candidate",
                    "confidence": 0.45,
                    "reviewState": "candidate",
                }
            ],
        }


class _AliasCandidate:
    def __init__(self, alias: str) -> None:
        self.alias = alias

    def to_request_dict(self) -> dict:
        return {
            "targetType": "complex",
            "targetId": "complex-mrp",
            "alias": self.alias,
            "aliasType": "community_slang",
            "source": "community:auto-candidate:PPOMPPU:house",
            "evidenceUrl": "https://example.test/post-mrp-1",
            "confidence": 0.62,
            "reviewState": "candidate",
            "createdBy": "system",
            "ambiguous": False,
        }


class _RawIngestion:
    def to_request_dict(self) -> dict:
        return {
            "run": {
                "runKey": "molit_apt_trade:11110:202606",
                "providerDataset": "molit_apt_trade",
                "runType": "backfill",
                "requestedFrom": "2026-06-01",
                "requestedTo": "2026-06-30",
                "requestParams": {
                    "LAWD_CD": "11110",
                    "DEAL_YMD": "202606",
                },
                "status": "running",
                "startedAt": "2026-06-12T00:00:00Z",
            },
            "items": [
                {
                    "providerDataset": "molit_apt_trade",
                    "providerObjectId": "molit_apt_trade:11110:202606:raw-1",
                    "legalDongCode": "11110",
                    "observedAt": "2026-06-03",
                    "asOf": "2026-06-01",
                    "rawPayload": {"aptNm": "Sajik Palace"},
                    "landingStatus": "landed",
                }
            ],
        }


def test_spring_client_defaults_to_longer_timeout_for_ingestion_batches():
    assert SpringIngestionClient("http://backend:8080").timeout_seconds == 60.0


def test_spring_client_publishes_real_estate_market_facts(monkeypatch):
    _FakeHttpxClient.posts = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    client.publish_real_estate_market_facts(
        [
            _MarketFact("molit_apt_trade:11110:202606:first"),
            _MarketFact("molit_apt_trade:11110:202606:second"),
        ]
    )

    assert _FakeHttpxClient.posts == [
        {
            "url": "http://backend:8080/internal/realestate/market-facts",
            "json": {
                "items": [
                    {
                        "provider": "molit",
                        "providerDataset": "molit_apt_trade",
                        "providerObjectId": "molit_apt_trade:11110:202606:first",
                        "factType": "apt_trade",
                    },
                    {
                        "provider": "molit",
                        "providerDataset": "molit_apt_trade",
                        "providerObjectId": "molit_apt_trade:11110:202606:second",
                        "factType": "apt_trade",
                    },
                ]
            },
            "timeout": 45,
        }
    ]


def test_spring_client_publishes_real_estate_public_data_raw_ingestion(monkeypatch):
    _FakeHttpxClient.posts = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    client.publish_real_estate_public_data_raw_ingestion(_RawIngestion())

    assert _FakeHttpxClient.posts == [
        {
            "url": "http://backend:8080/internal/realestate/public-data/raw-ingestions",
            "json": _raw_ingestion_payload(),
            "timeout": 45,
        }
    ]


def test_spring_client_promotes_real_estate_public_data_staging(monkeypatch):
    _FakeHttpxClient.posts = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    result = client.promote_real_estate_public_data_staging(
        provider_dataset="molit_apt_rent",
        run_key="molit_apt_rent:11110:202606",
        validation_status="valid",
        limit=10,
    )

    assert result == {"promotedFacts": 1}
    assert _FakeHttpxClient.posts == [
        {
            "url": "http://backend:8080/internal/realestate/public-data/promote-staging",
            "json": {
                "providerDataset": "molit_apt_rent",
                "runKey": "molit_apt_rent:11110:202606",
                "validationStatus": "valid",
                "limit": 10,
            },
            "timeout": 45,
        }
    ]


def test_spring_client_lists_real_estate_public_data_import_runs(monkeypatch):
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    runs = client.list_real_estate_public_data_import_runs(
        provider_dataset="molit_apt_trade",
        status="completed",
        limit=500,
    )

    assert runs == [
        {
            "runKey": "molit_apt_trade:11110:202606",
            "providerDataset": "molit_apt_trade",
            "status": "completed",
            "rowsLanded": 12,
        }
    ]
    assert _FakeHttpxClient.gets == [
        {
            "url": "http://backend:8080/internal/realestate/public-data/import-runs",
            "params": {
                "providerDataset": "molit_apt_trade",
                "status": "completed",
                "limit": "500",
            },
            "timeout": 45,
        }
    ]


def test_spring_client_lists_real_estate_public_data_import_runs_by_run_keys(monkeypatch):
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    client.list_real_estate_public_data_import_runs(
        run_keys=[
            "molit_apt_trade:11110:202606",
            "molit_apt_trade:11680:202606",
        ],
        status="completed",
    )

    assert _FakeHttpxClient.gets == [
        {
            "url": "http://backend:8080/internal/realestate/public-data/import-runs",
            "params": {
                "status": "completed",
                "limit": "2",
                "runKey": [
                    "molit_apt_trade:11110:202606",
                    "molit_apt_trade:11680:202606",
                ],
            },
            "timeout": 45,
        }
    ]


def test_spring_client_lists_real_estate_market_data_targets(monkeypatch):
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    targets = client.list_real_estate_market_data_targets(enabled=True)

    assert targets == [
        {
            "targetId": "region-seoul-jongno",
            "provider": "molit",
            "providerDataset": "molit_apt_trade",
            "lawdCode": "11110",
            "enabled": True,
        }
    ]


def test_spring_client_gets_real_estate_reaction_ranking(monkeypatch):
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    ranking = client.get_real_estate_reaction_ranking(
        target_type="region",
        window_minutes=60,
        limit=5,
    )

    assert ranking["items"][0]["targetId"] == "region-daejeon"
    assert _FakeHttpxClient.gets == [
        {
            "url": "http://backend:8080/api/realestate/reactions/rankings",
            "params": {
                "type": "region",
                "windowMinutes": "60",
                "limit": "5",
            },
            "timeout": 45,
        }
    ]


def test_spring_client_lists_target_market_facts_and_content(monkeypatch):
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    facts = client.list_real_estate_target_market_facts("region-daejeon", limit=10)
    content_items = client.list_real_estate_target_content_items("region-daejeon", feed="all", limit=10)

    assert facts[0]["providerObjectId"] == "molit_apt_trade:30110:202606:1"
    assert content_items[0]["contentId"] == "serpapi-region-daejeon-transport"
    assert _FakeHttpxClient.gets[-2:] == [
        {
            "url": "http://backend:8080/api/realestate/targets/region-daejeon/market-facts",
            "params": {
                "limit": "10",
            },
            "timeout": 45,
        },
        {
            "url": "http://backend:8080/api/realestate/targets/region-daejeon/content",
            "params": {
                "feed": "all",
                "limit": "10",
            },
            "timeout": 45,
        },
    ]


def test_spring_client_lists_real_estate_aliases_for_matcher(monkeypatch):
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    aliases = client.list_real_estate_aliases(
        review_state="approved",
        ambiguous=False,
        target_type="region",
    )

    assert aliases == [
        {
            "targetType": "region",
            "targetId": "region-seoul-jongno",
            "alias": "jongno-newbuild",
            "aliasType": "community_slang",
            "reviewState": "approved",
            "confidence": 0.91,
            "ambiguous": False,
            "source": "manual:review",
        }
    ]
    assert _FakeHttpxClient.gets == [
        {
            "url": "http://backend:8080/internal/realestate/aliases",
            "params": {
                "reviewState": "approved",
                "ambiguous": "false",
                "targetType": "region",
            },
            "timeout": 45,
        }
    ]


def test_spring_client_publishes_real_estate_alias_candidates(monkeypatch):
    _FakeHttpxClient.posts = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    client.publish_real_estate_alias_candidates([_AliasCandidate("MRP")])

    assert _FakeHttpxClient.posts == [
        {
            "url": "http://backend:8080/internal/realestate/aliases/candidates",
            "json": {
                "items": [
                    {
                        "targetType": "complex",
                        "targetId": "complex-mrp",
                        "alias": "MRP",
                        "aliasType": "community_slang",
                        "source": "community:auto-candidate:PPOMPPU:house",
                        "evidenceUrl": "https://example.test/post-mrp-1",
                        "confidence": 0.62,
                        "reviewState": "candidate",
                        "createdBy": "system",
                        "ambiguous": False,
                    }
                ]
            },
            "timeout": 45,
        }
    ]


def test_spring_client_lists_real_estate_target_edges_for_rollup(monkeypatch):
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    edges = client.list_real_estate_target_edges(
        review_state="approved",
        edge_type="contains",
        direction="both",
    )

    assert edges == [
        {
            "fromTargetType": "region",
            "fromTargetId": "region-seoul",
            "toTargetType": "region",
            "toTargetId": "region-seoul-jongno",
            "edgeType": "contains",
            "reviewState": "approved",
            "confidence": 0.9,
            "source": "admin:registry",
        }
    ]
    assert _FakeHttpxClient.gets == [
        {
            "url": "http://backend:8080/internal/realestate/target-edges",
            "params": {
                "reviewState": "approved",
                "edgeType": "contains",
                "direction": "both",
            },
            "timeout": 45,
        }
    ]


def test_spring_client_publishes_real_estate_regions(monkeypatch):
    _FakeHttpxClient.posts = []
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    client.publish_real_estate_regions(
        [
            _RegionImport("region-26350", "Busan Haeundae-gu"),
        ]
    )

    assert _FakeHttpxClient.posts == [
        {
            "url": "http://backend:8080/internal/realestate/regions",
            "json": {
                "items": [
                    {
                        "targetId": "region-26350",
                        "displayName": "Busan Haeundae-gu",
                        "regionLevel": "sigungu",
                        "legalDongCode": "26350",
                    }
                ]
            },
            "timeout": 45,
        }
    ]
    assert _FakeHttpxClient.gets == []


def test_spring_client_publishes_real_estate_reaction_snapshots(monkeypatch):
    _FakeHttpxClient.posts = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    client.publish_real_estate_reaction_snapshots(
        [
            _ReactionSnapshot("region-daejeon"),
            _ReactionSnapshot("region-seoul"),
        ]
    )

    assert _FakeHttpxClient.posts == [
        {
            "url": "http://backend:8080/internal/realestate/reaction-snapshots",
            "json": {
                "items": [
                    _ReactionSnapshot("region-daejeon").to_request_dict(),
                    _ReactionSnapshot("region-seoul").to_request_dict(),
                ]
            },
            "timeout": 45,
        }
    ]


def test_spring_client_publishes_real_estate_content_items(monkeypatch):
    _FakeHttpxClient.posts = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    client.publish_real_estate_content_items(
        [
            _ContentItem("serpapi-issue-1"),
            _ContentItem("serpapi-issue-2"),
        ]
    )

    assert _FakeHttpxClient.posts == [
        {
            "url": "http://backend:8080/internal/realestate/content-items",
            "json": {
                "items": [
                    _ContentItem("serpapi-issue-1").to_content_item_dict(),
                    _ContentItem("serpapi-issue-2").to_content_item_dict(),
                ]
            },
            "timeout": 45,
        }
    ]


def test_spring_client_publishes_real_estate_evidence_logs(monkeypatch):
    _FakeHttpxClient.posts = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    log = {
        "evidenceLogId": "evidence-region-daejeon-20260611000000-realestate-eval-v1",
        "targetId": "region-daejeon",
        "evaluationVersion": "realestate-eval-v1",
        "promptVersion": "rule-evidence-v1",
        "tone": "watch",
        "summary": "관심과 기대 반응이 빠르게 관찰됩니다.",
        "dataQuality": "partial",
        "evaluatedAt": "2026-06-12T02:00:00Z",
        "asOf": "2026-06-11T01:02:00Z",
        "skipReason": None,
        "evidenceItems": [
            {
                "evidenceItemId": "reaction-region-daejeon-20260611000000",
                "evidenceType": "reaction",
                "refType": "reaction_snapshot",
                "refId": "region-daejeon-20260611000000",
                "label": "반응 스냅샷",
                "valueText": "언급 4건 · 기대 50.0% / 우려 25.0%",
                "severity": "watch",
            }
        ],
    }

    client.publish_real_estate_evidence_logs([log])

    assert _FakeHttpxClient.posts == [
        {
            "url": "http://backend:8080/internal/realestate/evidence-logs",
            "json": {"logs": [log]},
            "timeout": 45,
        }
    ]


def test_spring_client_lists_real_estate_target_timeline_events(monkeypatch):
    _FakeHttpxClient.gets = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    items = client.list_real_estate_target_timeline_events("region-daejeon", limit=3)

    assert items[0]["eventType"] == "supply"
    assert _FakeHttpxClient.gets == [
        {
            "url": "http://backend:8080/api/realestate/targets/region-daejeon/timeline",
            "params": {"limit": "3"},
            "timeout": 45,
        }
    ]


def test_spring_client_refreshes_real_estate_map_layer_snapshots(monkeypatch):
    _FakeHttpxClient.posts = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient("http://backend:8080", timeout_seconds=45)

    result = client.refresh_real_estate_map_layer_snapshots(
        layer_type="sigungu",
        periods=("month", "halfYear"),
        as_of="2026-06-21T00:00:00Z",
    )

    assert result["acceptedSnapshots"] == 2
    assert _FakeHttpxClient.posts == [
        {
            "url": "http://backend:8080/internal/realestate/map/layer-snapshots/refresh",
            "json": {
                "layerType": "sigungu",
                "periods": ["month", "halfYear"],
                "asOf": "2026-06-21T00:00:00Z",
            },
            "timeout": 45,
        }
    ]


def _raw_ingestion_payload() -> dict:
    return _RawIngestion().to_request_dict()
