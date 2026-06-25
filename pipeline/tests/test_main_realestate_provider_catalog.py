import asyncio
import json
from pathlib import Path
import subprocess
import sys

from youbuyfirst_pipeline import main as pipeline_main


PIPELINE_ROOT = Path(__file__).resolve().parents[1]


def test_realestate_public_data_providers_command_prints_catalog(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-public-data-providers",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    dataset_ids = [item["datasetId"] for item in payload["items"]]

    assert dataset_ids[:4] == [
        "molit_apt_trade",
        "molit_apt_rent",
        "molit_offi_trade",
        "molit_offi_rent",
    ]
    assert "serviceKey" not in str(payload)


def test_realestate_public_data_providers_command_prints_sql_seed(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-public-data-providers",
            "--realestate-provider-output",
            "sql",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    output = capsys.readouterr().out

    assert "insert into real_estate_public_data_datasets" in output
    assert "'molit_apt_trade', 'molit', '국토교통부'" in output
    assert "'molit_official_apartment_price_csv'" in output
    assert "serviceKey" not in output


def test_realestate_public_data_providers_subprocess_outputs_utf8_sql():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "youbuyfirst_pipeline.main",
            "realestate-public-data-providers",
            "--realestate-provider-output",
            "sql",
        ],
        cwd=PIPELINE_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    output = result.stdout.decode("utf-8")
    assert "'molit_apt_trade', 'molit', '국토교통부'" in output
