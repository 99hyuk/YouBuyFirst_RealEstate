from youbuyfirst_pipeline.realestate_source_registry import (
    build_real_estate_crawl_target_manifest,
)
from youbuyfirst_pipeline.source_policy import CrawlRuntimeEnvironment


def test_build_crawl_target_manifest_keeps_only_local_public_board_candidates():
    candidates = [
        {
            "sourceId": "ppomppu_house",
            "displayName": "뽐뿌 부동산포럼",
            "sourceType": "general_board",
            "primaryUrl": "https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1",
            "crawlPolicy": "local-research-only",
            "requiresLogin": False,
            "publicListObserved": True,
            "adapterSource": "PPOMPPU",
            "boardId": "house",
            "priority": "P0",
            "allowedStorage": ["title", "contentSnippet", "url", "authorHash"],
            "targetScope": ["region", "complex", "policy_area"],
        },
        {
            "sourceId": "dc_immovables",
            "displayName": "디시인사이드 부동산 갤러리",
            "sourceType": "general_board",
            "primaryUrl": "https://gall.dcinside.com/board/lists/?id=immovables",
            "crawlPolicyCandidate": "public-http-candidate",
            "requiresLogin": False,
            "publicListObserved": True,
            "priority": "P0",
        },
        {
            "sourceId": "naver_boodongsan_study",
            "displayName": "부동산스터디",
            "sourceType": "national_investment",
            "primaryUrl": "https://cafe.naver.com/jaegebal",
            "crawlPolicy": "excluded-naver-cafe",
            "requiresLogin": True,
            "publicListObserved": False,
            "priority": "P1",
        },
    ]

    manifest = build_real_estate_crawl_target_manifest(
        candidates,
        runtime_environment=CrawlRuntimeEnvironment.LOCAL,
    )

    assert [item["targetId"] for item in manifest["items"]] == ["PPOMPPU:house", "DCINSIDE:immovables"]
    assert [item["priority"] for item in manifest["items"]] == [200, 210]
    assert manifest["items"][0] == {
        "targetId": "PPOMPPU:house",
        "sourceId": "ppomppu_house",
        "source": "PPOMPPU",
        "boardId": "house",
        "kind": "community-board",
        "url": "https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1",
        "label": "뽐뿌 부동산포럼",
        "sourceType": "general_board",
        "targetScope": ["region", "complex", "policy_area"],
        "crawlPolicy": "local-research-only",
        "runtimeEnvironment": "local",
        "priority": 200,
        "crawlIntervalSeconds": 3600,
        "allowedStorage": ["title", "contentSnippet", "url", "authorHash"],
    }
    assert manifest["counts"] == {"accepted": 2, "skipped": 1}
    assert manifest["skipped"] == [
        {
            "sourceId": "naver_boodongsan_study",
            "reason": "source policy excluded-naver-cafe is not crawlable",
        }
    ]


def test_build_crawl_target_manifest_blocks_local_research_candidates_in_public_runtime():
    manifest = build_real_estate_crawl_target_manifest(
        [
            {
                "sourceId": "ppomppu_house",
                "displayName": "뽐뿌 부동산포럼",
                "sourceType": "general_board",
                "primaryUrl": "https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1",
                "crawlPolicy": "local-research-only",
                "requiresLogin": False,
                "publicListObserved": True,
                "adapterSource": "PPOMPPU",
                "boardId": "house",
                "priority": "P0",
            }
        ],
        runtime_environment=CrawlRuntimeEnvironment.PUBLIC,
    )

    assert manifest["items"] == []
    assert manifest["counts"] == {"accepted": 0, "skipped": 1}
    assert manifest["skipped"] == [
        {
            "sourceId": "ppomppu_house",
            "reason": "source policy local-research-only is not allowed in public runtime",
        }
    ]
