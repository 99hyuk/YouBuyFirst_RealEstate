from __future__ import annotations

from dataclasses import dataclass
import re

from youbuyfirst_pipeline.models import AliasCandidate, Instrument, InstrumentAliasRule, Mention


_ASCII_TEXT_TOKEN_PATTERN = re.compile(r"(?<![A-Z0-9])([A-Z0-9]+(?:[.\-][A-Z0-9]+)*)(?![A-Z0-9])")


@dataclass(frozen=True)
class _MentionEntry:
    instrument: Instrument
    alias: str
    pattern: re.Pattern[str] | None


@dataclass(frozen=True)
class _CandidateEntry:
    rule: InstrumentAliasRule
    alias: str
    pattern: re.Pattern[str] | None


class InstrumentMatcher:
    def __init__(self, instruments: list[Instrument], review_aliases: list[InstrumentAliasRule] | None = None) -> None:
        self.entries: list[_MentionEntry] = []
        self._ascii_entries_by_token: dict[str, list[_MentionEntry]] = {}
        self._non_ascii_entries_by_first_char: dict[str, list[_MentionEntry]] = {}
        for instrument in instruments:
            aliases = {instrument.symbol, instrument.name, *instrument.aliases}
            for alias in sorted((a.strip() for a in aliases if a and a.strip()), key=len, reverse=True):
                pattern = _ticker_pattern(alias) if _is_ascii_token(alias) else None
                entry = _MentionEntry(instrument=instrument, alias=alias, pattern=pattern)
                self.entries.append(entry)
                _add_indexed_entry(entry, self._ascii_entries_by_token, self._non_ascii_entries_by_first_char)

        self.candidate_entries: list[_CandidateEntry] = []
        self._ascii_candidate_entries_by_token: dict[str, list[_CandidateEntry]] = {}
        self._non_ascii_candidate_entries_by_first_char: dict[str, list[_CandidateEntry]] = {}
        for rule in review_aliases or []:
            if not _should_surface_candidate(rule):
                continue
            alias = rule.alias.strip()
            if not alias:
                continue
            pattern = _ticker_pattern(alias) if _is_ascii_token(alias) else None
            entry = _CandidateEntry(rule=rule, alias=alias, pattern=pattern)
            self.candidate_entries.append(entry)
            _add_indexed_entry(
                entry,
                self._ascii_candidate_entries_by_token,
                self._non_ascii_candidate_entries_by_first_char,
            )

    def match(self, text: str) -> list[Mention]:
        mentions: list[Mention] = []
        seen: set[tuple[str, str, str]] = set()
        spans_by_instrument: dict[tuple[str, str], list[tuple[int, int]]] = {}
        upper_text = text.upper()

        for entry in _iter_relevant_entries(
            text=text,
            upper_text=upper_text,
            ascii_entries_by_token=self._ascii_entries_by_token,
            non_ascii_entries_by_first_char=self._non_ascii_entries_by_first_char,
        ):
            instrument = entry.instrument
            instrument_key = (instrument.market, instrument.symbol)
            span = _find_first_available_span(
                text=upper_text if entry.pattern else text,
                alias=entry.alias.upper() if entry.pattern else entry.alias,
                pattern=entry.pattern,
                existing_spans=spans_by_instrument.get(instrument_key, []),
            )
            if span is None:
                continue

            key = (instrument.market, instrument.symbol, entry.alias)
            if key in seen:
                continue
            seen.add(key)
            spans_by_instrument.setdefault(instrument_key, []).append(span)
            mentions.append(
                Mention(
                    market=instrument.market,
                    symbol=instrument.symbol,
                    matched_text=entry.alias,
                    instrument_id=instrument.instrument_id,
                )
            )
        return mentions

    def alias_candidates(self, text: str) -> list[AliasCandidate]:
        candidates: list[AliasCandidate] = []
        seen: set[tuple[str | None, str | None, str]] = set()
        upper_text = text.upper()

        for entry in _iter_relevant_entries(
            text=text,
            upper_text=upper_text,
            ascii_entries_by_token=self._ascii_candidate_entries_by_token,
            non_ascii_entries_by_first_char=self._non_ascii_candidate_entries_by_first_char,
        ):
            rule = entry.rule
            span = _find_first_available_span(
                text=upper_text if entry.pattern else text,
                alias=entry.alias.upper() if entry.pattern else entry.alias,
                pattern=entry.pattern,
                existing_spans=[],
            )
            if span is None:
                continue
            key = (rule.market.upper() if rule.market else None, rule.symbol.upper() if rule.symbol else None, entry.alias)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                AliasCandidate(
                    alias=entry.alias,
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


def _add_indexed_entry(
    entry: _MentionEntry | _CandidateEntry,
    ascii_entries_by_token: dict,
    non_ascii_entries_by_first_char: dict,
) -> None:
    if entry.pattern:
        ascii_entries_by_token.setdefault(entry.alias.upper(), []).append(entry)
        return
    non_ascii_entries_by_first_char.setdefault(entry.alias[0], []).append(entry)


def _iter_relevant_entries(
    text: str,
    upper_text: str,
    ascii_entries_by_token: dict,
    non_ascii_entries_by_first_char: dict,
) -> list[_MentionEntry | _CandidateEntry]:
    entries: list[_MentionEntry | _CandidateEntry] = []
    for token in _unique_ascii_tokens(upper_text):
        entries.extend(ascii_entries_by_token.get(token, []))
    for first_char in _unique_chars(text):
        entries.extend(non_ascii_entries_by_first_char.get(first_char, []))
    entries.sort(key=lambda entry: len(entry.alias), reverse=True)
    return entries


def _unique_ascii_tokens(upper_text: str) -> list[str]:
    seen: set[str] = set()
    tokens: list[str] = []
    for match in _ASCII_TEXT_TOKEN_PATTERN.finditer(upper_text):
        for token in _ascii_token_lookup_keys(match.group(1)):
            if token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return tokens


def _ascii_token_lookup_keys(token: str) -> list[str]:
    keys = [token]
    for index, char in enumerate(token):
        if char in ".-" and index > 0:
            keys.append(token[:index])
    return keys


def _unique_chars(text: str) -> list[str]:
    seen: set[str] = set()
    chars: list[str] = []
    for char in text:
        if char in seen:
            continue
        seen.add(char)
        chars.append(char)
    return chars


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
