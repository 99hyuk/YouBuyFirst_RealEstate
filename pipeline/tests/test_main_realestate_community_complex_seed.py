import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


class _FakeSpringClient:
    def __init__(self) -> None:
        self.targets = []
        self.complexes = []
        self.aliases = []
        self.edges = []
        self.post_requests = []

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
                "source": "DCINSIDE",
                "externalId": "post-1",
                "publishedAt": "2026-06-16T00:00:00Z",
                "title": "헬리오시티랑 리센츠 거래량 얘기",
                "contentSnippet": "",
            }
        ]

    def list_real_estate_aliases(self, **_kwargs):
        return [
            {
                "targetType": "complex",
                "targetId": "complex-molit-helio-city",
                "alias": "헬리오시티",
                "aliasType": "official",
                "reviewState": "approved",
                "confidence": 0.96,
                "ambiguous": False,
                "source": "backend:test",
            }
        ]

    def publish_real_estate_targets(self, targets) -> None:
        self.targets.extend(targets)

    def publish_real_estate_complexes(self, complexes) -> None:
        self.complexes.extend(complexes)

    def publish_real_estate_aliases(self, aliases) -> None:
        self.aliases.extend(aliases)

    def publish_real_estate_target_edges(self, edges) -> None:
        self.edges.extend(edges)


def test_realestate_community_complex_seeds_push_reads_backend_posts_and_publishes(monkeypatch, capsys):
    fake_client = _FakeSpringClient()
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-community-complex-seeds-push",
            "--realestate-use-backend-community-posts",
            "--realestate-daily-reaction-window-minutes",
            "10080",
            "--realestate-community-posts-limit",
            "5000",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "observedComplexTargets": 2,
        "publishedTargets": 2,
        "publishedComplexes": 2,
        "publishedAliases": 3,
        "publishedEdges": 2,
    }
    assert fake_client.post_requests[0]["limit"] == 5000
    assert [target["targetId"] for target in fake_client.targets] == [
        "complex-community-helio-city",
        "complex-community-ricenz",
    ]
    assert {complex_row["markerDataStatus"] for complex_row in fake_client.complexes} == {"community_observed"}
    assert {alias["reviewState"] for alias in fake_client.aliases} == {"approved"}
    assert {edge["fromTargetId"] for edge in fake_client.edges} == {"region-seoul-songpa"}


def test_realestate_community_complex_seeds_push_reuses_backend_alias_targets(monkeypatch, capsys):
    fake_client = _FakeSpringClient()
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-community-complex-seeds-push",
            "--realestate-use-backend-community-posts",
            "--realestate-use-backend-aliases",
            "--realestate-daily-reaction-window-minutes",
            "10080",
            "--realestate-community-posts-limit",
            "5000",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "observedComplexTargets": 2,
        "publishedTargets": 1,
        "publishedComplexes": 1,
        "publishedAliases": 2,
        "publishedEdges": 1,
    }
    assert [target["targetId"] for target in fake_client.targets] == [
        "complex-community-ricenz",
    ]
    assert [alias["targetId"] for alias in fake_client.aliases] == [
        "complex-molit-helio-city",
        "complex-community-ricenz",
    ]
