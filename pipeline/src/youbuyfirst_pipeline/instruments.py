from __future__ import annotations

import csv
from pathlib import Path

from youbuyfirst_pipeline.models import Instrument, InstrumentAliasRule


def load_instruments(path: str | Path, alias_rules: list[InstrumentAliasRule] | None = None) -> list[Instrument]:
    accepted_aliases: dict[tuple[str, str], list[str]] = {}
    for rule in alias_rules or []:
        if rule.status.upper() != "ACCEPTED" or rule.ambiguous:
            continue
        key = (rule.market.upper(), rule.symbol.upper())
        accepted_aliases.setdefault(key, []).append(rule.alias)

    instruments: list[Instrument] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            market = (row.get("market") or "").strip().upper()
            symbol = (row.get("symbol") or "").strip().upper()
            aliases = [alias.strip() for alias in (row.get("aliases") or "").split("|") if alias.strip()]
            aliases = _dedupe_aliases([*aliases, *accepted_aliases.get((market, symbol), [])])
            instruments.append(
                Instrument(
                    market=market,
                    symbol=symbol,
                    name=(row.get("name") or "").strip(),
                    aliases=aliases,
                )
            )
    return instruments


def load_alias_rules(path: str | Path) -> list[InstrumentAliasRule]:
    alias_path = Path(path)
    if not alias_path.exists():
        return []
    rules: list[InstrumentAliasRule] = []
    with alias_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            alias = (row.get("alias") or "").strip()
            if not alias:
                continue
            rules.append(
                InstrumentAliasRule(
                    market=(row.get("market") or "").strip().upper(),
                    symbol=(row.get("symbol") or "").strip().upper(),
                    alias=alias,
                    status=(row.get("status") or "ACCEPTED").strip().upper(),
                    confidence=_parse_float(row.get("confidence"), default=1.0),
                    ambiguous=_parse_bool(row.get("ambiguous")),
                    source=(row.get("source") or "").strip() or None,
                    notes=(row.get("notes") or "").strip() or None,
                )
            )
    return rules


def review_alias_rules(rules: list[InstrumentAliasRule]) -> list[InstrumentAliasRule]:
    return [
        rule
        for rule in rules
        if rule.status.upper() != "BLOCKED" and (rule.ambiguous or rule.status.upper() == "REVIEW")
    ]


def _dedupe_aliases(values: list[str]) -> list[str]:
    aliases: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        aliases.append(value)
    return aliases


def _parse_float(value: str | None, default: float) -> float:
    if value is None or value.strip() == "":
        return default
    return float(value)


def _parse_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y"}
