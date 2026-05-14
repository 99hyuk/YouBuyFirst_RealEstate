from __future__ import annotations

import csv
from pathlib import Path

from youbuyfirst_pipeline.models import Instrument


def load_instruments(path: str | Path) -> list[Instrument]:
    instruments: list[Instrument] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            aliases = [alias.strip() for alias in (row.get("aliases") or "").split("|") if alias.strip()]
            instruments.append(
                Instrument(
                    market=(row.get("market") or "").strip().upper(),
                    symbol=(row.get("symbol") or "").strip().upper(),
                    name=(row.get("name") or "").strip(),
                    aliases=aliases,
                )
            )
    return instruments

