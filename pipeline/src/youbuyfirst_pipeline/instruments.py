from __future__ import annotations

import csv
import json
import logging
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from youbuyfirst_pipeline.models import Instrument, InstrumentAliasRule

logger = logging.getLogger(__name__)


def load_instrument_snapshot(
    path: str | Path,
    alias_rules: list[InstrumentAliasRule] | None = None,
    *,
    snapshot_url: str | None = None,
    timeout_seconds: float = 10.0,
    snapshot_retries: int = 1,
    snapshot_retry_delay_seconds: float = 0.0,
    fallback_on_snapshot_error: bool = True,
) -> list[Instrument]:
    if snapshot_url and snapshot_url.strip():
        snapshot_url = snapshot_url.strip()
        attempts = max(1, snapshot_retries)
        last_error: RuntimeError | None = None
        for attempt in range(1, attempts + 1):
            try:
                return load_instruments_from_snapshot_url(snapshot_url, timeout_seconds=timeout_seconds)
            except RuntimeError as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                if snapshot_retry_delay_seconds > 0:
                    time.sleep(snapshot_retry_delay_seconds)
        if fallback_on_snapshot_error:
            logger.warning(
                "Falling back to instrument CSV after snapshot load failed from %s: %s",
                snapshot_url,
                last_error,
            )
            return load_instruments(path, alias_rules)
        if last_error is not None:
            raise last_error
    return load_instruments(path, alias_rules)


def load_instruments_from_snapshot_url(url: str, *, timeout_seconds: float = 10.0) -> list[Instrument]:
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"failed to load instrument snapshot from {url}") from exc

    if not isinstance(payload, list):
        raise ValueError("instrument snapshot response must be a JSON array")
    return [_instrument_from_snapshot_item(item) for item in payload]


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


def _instrument_from_snapshot_item(item: object) -> Instrument:
    if not isinstance(item, dict):
        raise ValueError("instrument snapshot entries must be objects")
    aliases = item.get("aliases") or []
    if not isinstance(aliases, list):
        raise ValueError("instrument snapshot aliases must be arrays")
    return Instrument(
        instrument_id=_parse_int(item.get("instrumentId")),
        market=str(item.get("market") or "").strip().upper(),
        symbol=str(item.get("symbol") or "").strip().upper(),
        name=str(item.get("name") or "").strip(),
        aliases=_dedupe_aliases([str(alias).strip() for alias in aliases if str(alias).strip()]),
    )


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


def _parse_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _parse_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y"}
