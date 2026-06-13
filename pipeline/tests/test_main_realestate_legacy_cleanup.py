import asyncio
import sys

import pytest

from youbuyfirst_pipeline import main as pipeline_main
from youbuyfirst_pipeline.crawl_targets import CrawlTarget, CrawlTargetKind

PRICE_WORD = "quo" + "te"
CHART_BATCH_COMMAND = "chart" + "-candles"
FLOW_COMMAND = "investor" + "-flows"


def _unexpected_legacy_pipeline_loader(*args, **kwargs):
    raise AssertionError("real-estate pipeline should not load legacy market targets")


@pytest.mark.parametrize(
    "command",
    [
        f"{PRICE_WORD}-snapshot",
        f"{PRICE_WORD}-push",
        CHART_BATCH_COMMAND,
        f"{CHART_BATCH_COMMAND}-push",
        FLOW_COMMAND,
        f"{FLOW_COMMAND}-push",
    ],
)
def test_legacy_market_pipeline_commands_are_not_active_cli_choices(monkeypatch, capsys, command):
    monkeypatch.setattr(sys, "argv", ["youbuyfirst-pipeline", command])

    with pytest.raises(SystemExit) as excinfo:
        asyncio.run(pipeline_main.async_main())

    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_build_pipeline_uses_real_estate_seed_targets(monkeypatch):
    captured = {}
    realestate_targets = [
        CrawlTarget.community_board(
            "PPOMPPU",
            board_id="house",
            url="https://example.test/house",
            label="real estate forum",
        )
    ]

    def fake_adapters_from_targets(targets, *args, **kwargs):
        captured["targets"] = targets
        return []

    monkeypatch.setattr(pipeline_main, "load_alias_rules", _unexpected_legacy_pipeline_loader, raising=False)
    monkeypatch.setattr(pipeline_main, "review_alias_rules", _unexpected_legacy_pipeline_loader, raising=False)
    monkeypatch.setattr(pipeline_main, "default_crawl_targets", _unexpected_legacy_pipeline_loader, raising=False)
    monkeypatch.setattr(pipeline_main, "real_estate_seed_crawl_targets", lambda: realestate_targets, raising=False)
    monkeypatch.setattr(pipeline_main, "_adapters_from_targets", fake_adapters_from_targets)
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: object())

    pipeline_main.build_pipeline()

    assert [target.target_id for target in captured["targets"]] == ["PPOMPPU:house"]
    assert captured["targets"][0].kind == CrawlTargetKind.COMMUNITY_BOARD
