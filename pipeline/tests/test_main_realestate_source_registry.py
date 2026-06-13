import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


def test_realestate_crawl_target_manifest_command_writes_manifest(tmp_path, monkeypatch, capsys):
    candidates_path = tmp_path / "sources.jsonl"
    output_path = tmp_path / "crawl-targets.json"
    candidates_path.write_text(
        "\n".join(
            [
                json.dumps(
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
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
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
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-crawl-target-manifest",
            "--realestate-source-candidates-jsonl",
            str(candidates_path),
            "--realestate-crawl-target-manifest-output",
            str(output_path),
            "--crawl-runtime-environment",
            "local",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["counts"] == {"accepted": 1, "skipped": 1}
    assert stdout_payload["items"][0]["targetId"] == "PPOMPPU:house"
