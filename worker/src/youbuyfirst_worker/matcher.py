from __future__ import annotations

import re

from youbuyfirst_worker.models import Instrument, Mention


class InstrumentMatcher:
    def __init__(self, instruments: list[Instrument]) -> None:
        self.entries: list[tuple[Instrument, str, re.Pattern[str] | None]] = []
        for instrument in instruments:
            aliases = {instrument.symbol, instrument.name, *instrument.aliases}
            for alias in sorted((a.strip() for a in aliases if a and a.strip()), key=len, reverse=True):
                pattern = _ticker_pattern(alias) if _is_ascii_token(alias) else None
                self.entries.append((instrument, alias, pattern))

    def match(self, text: str) -> list[Mention]:
        mentions: list[Mention] = []
        seen: set[tuple[str, str, str]] = set()
        spans_by_instrument: dict[tuple[str, str], list[tuple[int, int]]] = {}
        upper_text = text.upper()

        for instrument, alias, pattern in self.entries:
            span = None
            if pattern:
                match = pattern.search(upper_text)
                if match:
                    span = match.span()
            elif alias in text:
                index = text.find(alias)
                span = (index, index + len(alias))
            if span is None:
                continue

            instrument_key = (instrument.market, instrument.symbol)
            if _is_inside_existing_span(span, spans_by_instrument.get(instrument_key, [])):
                continue
            key = (instrument.market, instrument.symbol, alias)
            if key in seen:
                continue
            seen.add(key)
            spans_by_instrument.setdefault(instrument_key, []).append(span)
            mentions.append(Mention(market=instrument.market, symbol=instrument.symbol, matched_text=alias))
        return mentions


def _is_ascii_token(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9.\-]+", value))


def _ticker_pattern(value: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![A-Z0-9]){re.escape(value.upper())}(?![A-Z0-9])")


def _is_inside_existing_span(candidate: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    start, end = candidate
    return any(existing_start <= start and end <= existing_end for existing_start, existing_end in spans)
