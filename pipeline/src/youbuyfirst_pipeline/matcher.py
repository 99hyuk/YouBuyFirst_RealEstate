from __future__ import annotations

import re

from youbuyfirst_pipeline.models import AliasCandidate, Instrument, InstrumentAliasRule, Mention


class InstrumentMatcher:
    def __init__(self, instruments: list[Instrument], review_aliases: list[InstrumentAliasRule] | None = None) -> None:
        self.entries: list[tuple[Instrument, str, re.Pattern[str] | None]] = []
        for instrument in instruments:
            aliases = {instrument.symbol, instrument.name, *instrument.aliases}
            for alias in sorted((a.strip() for a in aliases if a and a.strip()), key=len, reverse=True):
                pattern = _ticker_pattern(alias) if _is_ascii_token(alias) else None
                self.entries.append((instrument, alias, pattern))
        self.candidate_entries: list[tuple[InstrumentAliasRule, re.Pattern[str] | None]] = []
        for rule in review_aliases or []:
            if not _should_surface_candidate(rule):
                continue
            alias = rule.alias.strip()
            if not alias:
                continue
            pattern = _ticker_pattern(alias) if _is_ascii_token(alias) else None
            self.candidate_entries.append((rule, pattern))

    def match(self, text: str) -> list[Mention]:
        mentions: list[Mention] = []
        seen: set[tuple[str, str, str]] = set()
        spans_by_instrument: dict[tuple[str, str], list[tuple[int, int]]] = {}
        upper_text = text.upper()

        for instrument, alias, pattern in self.entries:
            instrument_key = (instrument.market, instrument.symbol)
            span = _find_first_available_span(
                text=upper_text if pattern else text,
                alias=alias.upper() if pattern else alias,
                pattern=pattern,
                existing_spans=spans_by_instrument.get(instrument_key, []),
            )
            if span is None:
                continue

            key = (instrument.market, instrument.symbol, alias)
            if key in seen:
                continue
            seen.add(key)
            spans_by_instrument.setdefault(instrument_key, []).append(span)
            mentions.append(Mention(market=instrument.market, symbol=instrument.symbol, matched_text=alias))
        return mentions

    def alias_candidates(self, text: str) -> list[AliasCandidate]:
        candidates: list[AliasCandidate] = []
        seen: set[tuple[str | None, str | None, str]] = set()
        upper_text = text.upper()

        for rule, pattern in self.candidate_entries:
            alias = rule.alias.strip()
            span = _find_first_available_span(
                text=upper_text if pattern else text,
                alias=alias.upper() if pattern else alias,
                pattern=pattern,
                existing_spans=[],
            )
            if span is None:
                continue
            key = (rule.market.upper() if rule.market else None, rule.symbol.upper() if rule.symbol else None, alias)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                AliasCandidate(
                    alias=alias,
                    suggested_market=rule.market.upper() if rule.market else None,
                    suggested_symbol=rule.symbol.upper() if rule.symbol else None,
                    reason="ambiguous-alias" if rule.ambiguous else "review-alias",
                )
            )
        return candidates


def _is_ascii_token(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9.\-]+", value))


def _should_surface_candidate(rule: InstrumentAliasRule) -> bool:
    status = rule.status.strip().upper()
    return status != "BLOCKED" and (rule.ambiguous or status == "REVIEW")


def _ticker_pattern(value: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![A-Z0-9]){re.escape(value.upper())}(?![A-Z0-9])")


def _find_first_available_span(
    text: str,
    alias: str,
    pattern: re.Pattern[str] | None,
    existing_spans: list[tuple[int, int]],
) -> tuple[int, int] | None:
    if pattern:
        for match in pattern.finditer(text):
            if not _is_inside_existing_span(match.span(), existing_spans):
                return match.span()
        return None

    start_at = 0
    while True:
        index = text.find(alias, start_at)
        if index == -1:
            return None
        span = (index, index + len(alias))
        if not _is_inside_existing_span(span, existing_spans):
            return span
        start_at = index + 1


def _is_inside_existing_span(candidate: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    start, end = candidate
    return any(existing_start <= start and end <= existing_end for existing_start, existing_end in spans)
