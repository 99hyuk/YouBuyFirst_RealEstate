from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RealEstateAliasRule:
    target_type: str
    target_id: str
    alias: str
    alias_type: str = "official"
    review_state: str = "approved"
    confidence: float = 1.0
    ambiguous: bool = False
    source: str | None = None


@dataclass(frozen=True)
class _AliasEntry:
    rule: RealEstateAliasRule
    normalized_alias: str


@dataclass(frozen=True)
class RealEstatePostForMatching:
    source: str
    external_id: str
    published_at: datetime
    title: str
    content_snippet: str
    url: str | None = None


@dataclass(frozen=True)
class RealEstateTargetMention:
    target_type: str
    target_id: str
    matched_text: str
    match_source: str
    confidence: float
    review_state: str
    alias_type: str

    def to_dict(self) -> dict:
        return {
            "targetType": self.target_type,
            "targetId": self.target_id,
            "matchedText": self.matched_text,
            "matchSource": self.match_source,
            "confidence": self.confidence,
            "reviewState": self.review_state,
            "aliasType": self.alias_type,
        }


@dataclass(frozen=True)
class RealEstateAliasCandidate:
    target_type: str
    target_id: str
    alias: str
    alias_type: str
    source: str
    evidence_url: str | None
    confidence: float
    review_state: str = "candidate"
    created_by: str = "system"
    ambiguous: bool = False

    def to_request_dict(self) -> dict:
        return {
            "targetType": self.target_type,
            "targetId": self.target_id,
            "alias": self.alias,
            "aliasType": self.alias_type,
            "source": self.source,
            "evidenceUrl": self.evidence_url,
            "confidence": self.confidence,
            "reviewState": self.review_state,
            "createdBy": self.created_by,
            "ambiguous": self.ambiguous,
        }


@dataclass(frozen=True)
class RealEstateMatchedPost:
    source: str
    external_id: str
    published_at: datetime
    url: str | None
    title: str
    content_snippet: str
    mentions: list[RealEstateTargetMention] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "externalId": self.external_id,
            "publishedAt": _iso(self.published_at),
            "url": self.url,
            "title": self.title,
            "contentSnippet": self.content_snippet,
            "matched": bool(self.mentions),
            "mentions": [mention.to_dict() for mention in self.mentions],
        }


class RealEstateTargetMatcher:
    def __init__(self, aliases: list[RealEstateAliasRule]) -> None:
        self._entries_by_first_char: dict[str, list[_AliasEntry]] = {}
        for alias in aliases:
            if not _is_confirmed_alias(alias):
                continue
            normalized_alias = alias.alias.strip()
            if len(normalized_alias) < 2:
                continue
            match_key = _match_key(normalized_alias)
            if len(match_key) < 2:
                continue
            normalized_rule = RealEstateAliasRule(
                target_type=alias.target_type.strip(),
                target_id=alias.target_id.strip(),
                alias=normalized_alias,
                alias_type=alias.alias_type.strip() or "official",
                review_state=alias.review_state.strip().lower() or "approved",
                confidence=round(float(alias.confidence), 2),
                ambiguous=alias.ambiguous,
                source=alias.source,
            )
            self._entries_by_first_char.setdefault(match_key[0], []).append(
                _AliasEntry(rule=normalized_rule, normalized_alias=match_key)
            )

        for entries in self._entries_by_first_char.values():
            entries.sort(key=lambda entry: len(entry.normalized_alias), reverse=True)

    def match_post(self, post: RealEstatePostForMatching) -> RealEstateMatchedPost:
        mentions = self.match_text(post.title, match_source="title")
        seen_targets = {(mention.target_type, mention.target_id, mention.matched_text) for mention in mentions}
        for mention in self.match_text(post.content_snippet, match_source="content_snippet"):
            key = (mention.target_type, mention.target_id, mention.matched_text)
            if key in seen_targets:
                continue
            seen_targets.add(key)
            mentions.append(mention)
        mentions.sort(key=lambda mention: (0 if mention.match_source == "title" else 1, -len(mention.matched_text), mention.target_id))
        return RealEstateMatchedPost(
            source=post.source,
            external_id=post.external_id,
            published_at=post.published_at,
            url=post.url,
            title=post.title,
            content_snippet=post.content_snippet,
            mentions=mentions,
        )

    def match_text(self, text: str, *, match_source: str) -> list[RealEstateTargetMention]:
        if not text:
            return []
        normalized_text, spans = _matchable_text_with_spans(text)
        if not normalized_text:
            return []
        mentions: list[RealEstateTargetMention] = []
        spans_by_target: dict[tuple[str, str], list[tuple[int, int]]] = {}
        seen: set[tuple[str, str, str, str]] = set()
        for entry in self._relevant_aliases(normalized_text):
            alias = entry.rule
            target_key = (alias.target_type, alias.target_id)
            span = _first_available_span(
                normalized_text,
                spans,
                entry.normalized_alias,
                spans_by_target.get(target_key, []),
            )
            if span is None:
                continue
            key = (alias.target_type, alias.target_id, alias.alias, match_source)
            if key in seen:
                continue
            seen.add(key)
            spans_by_target.setdefault(target_key, []).append(span)
            mentions.append(
                RealEstateTargetMention(
                    target_type=alias.target_type,
                    target_id=alias.target_id,
                    matched_text=text[span[0]:span[1]],
                    match_source=match_source,
                    confidence=alias.confidence,
                    review_state="approved",
                    alias_type=alias.alias_type,
                )
            )
        return mentions

    def _relevant_aliases(self, normalized_text: str) -> list[_AliasEntry]:
        entries: list[_AliasEntry] = []
        seen_first_chars: set[str] = set()
        for char in normalized_text:
            if char in seen_first_chars:
                continue
            seen_first_chars.add(char)
            entries.extend(self._entries_by_first_char.get(char, []))
        entries.sort(key=lambda entry: len(entry.normalized_alias), reverse=True)
        return entries


def load_real_estate_alias_rules(path: str | Path) -> list[RealEstateAliasRule]:
    records = _load_json_records(path)
    return [_alias_from_mapping(record) for record in records]


def load_real_estate_posts_for_matching(path: str | Path) -> list[RealEstatePostForMatching]:
    records = _load_json_records(path)
    return real_estate_posts_for_matching_from_records(records)


def real_estate_posts_for_matching_from_records(records: list[dict[str, Any]]) -> list[RealEstatePostForMatching]:
    return [_post_from_mapping(record) for record in records]


def match_real_estate_posts(
    posts: list[RealEstatePostForMatching],
    aliases: list[RealEstateAliasRule],
) -> list[RealEstateMatchedPost]:
    matcher = RealEstateTargetMatcher(aliases)
    return [matcher.match_post(post) for post in posts]


def suggest_real_estate_alias_candidates(
    posts: list[RealEstatePostForMatching],
    aliases: list[RealEstateAliasRule],
) -> list[RealEstateAliasCandidate]:
    matcher = RealEstateTargetMatcher(aliases)
    known_alias_keys_by_target = _known_alias_keys_by_target(aliases)
    candidates: dict[tuple[str, str, str], RealEstateAliasCandidate] = {}
    for post in posts:
        matched_post = matcher.match_post(post)
        for mention in matched_post.mentions:
            target_key = (mention.target_type, mention.target_id)
            known_alias_keys = known_alias_keys_by_target.get(target_key, set())
            for alias in _parenthesized_aliases_after_text(post.title, mention.matched_text):
                alias_key = _match_key(alias)
                if len(alias_key) < 2 or alias_key in known_alias_keys:
                    continue
                candidate_key = (mention.target_type, mention.target_id, alias_key)
                candidates.setdefault(
                    candidate_key,
                    RealEstateAliasCandidate(
                        target_type=mention.target_type,
                        target_id=mention.target_id,
                        alias=alias,
                        alias_type="community_slang",
                        source=f"community:auto-candidate:{post.source}",
                        evidence_url=post.url,
                        confidence=0.62 if mention.match_source == "title" else 0.52,
                    ),
                )
    return sorted(candidates.values(), key=lambda candidate: (candidate.target_type, candidate.target_id, candidate.alias))


def build_real_estate_alias_coverage_report(
    posts: list[RealEstatePostForMatching],
    aliases: list[RealEstateAliasRule],
    *,
    top_target_limit: int = 10,
    unmatched_example_limit: int = 5,
    candidate_alias_limit: int = 10,
) -> dict[str, Any]:
    matched_posts = match_real_estate_posts(posts, aliases)
    posts_by_source: dict[str, list[RealEstatePostForMatching]] = {}
    matches_by_source: dict[str, list[RealEstateMatchedPost]] = {}
    for post, matched_post in zip(posts, matched_posts, strict=True):
        posts_by_source.setdefault(post.source, []).append(post)
        matches_by_source.setdefault(matched_post.source, []).append(matched_post)

    source_reports: list[dict[str, Any]] = []
    total_matched_posts = 0
    total_mentions = 0
    total_candidates = 0
    total_target_keys: set[tuple[str, str]] = set()
    for source in sorted(posts_by_source):
        source_posts = posts_by_source[source]
        source_matches = matches_by_source.get(source, [])
        matched_post_count = sum(1 for matched_post in source_matches if matched_post.mentions)
        mention_count = sum(len(matched_post.mentions) for matched_post in source_matches)
        target_rows = _alias_coverage_top_targets(source_matches, limit=top_target_limit)
        source_target_keys = {
            (mention.target_type, mention.target_id)
            for matched_post in source_matches
            for mention in matched_post.mentions
        }
        candidates = suggest_real_estate_alias_candidates(source_posts, aliases)
        source_reports.append(
            {
                "source": source,
                "postCount": len(source_posts),
                "matchedPostCount": matched_post_count,
                "unmatchedPostCount": len(source_posts) - matched_post_count,
                "matchRate": _coverage_rate(matched_post_count, len(source_posts)),
                "mentionCount": mention_count,
                "targetCount": len(source_target_keys),
                "candidateAliasCount": len(candidates),
                "topTargets": target_rows,
                "unmatchedExamples": _alias_coverage_unmatched_examples(source_matches, limit=unmatched_example_limit),
                "candidateAliases": [
                    candidate.to_request_dict()
                    for candidate in candidates[:candidate_alias_limit]
                ],
            }
        )
        total_matched_posts += matched_post_count
        total_mentions += mention_count
        total_candidates += len(candidates)
        total_target_keys.update(source_target_keys)

    post_count = len(posts)
    return {
        "totals": {
            "sourceCount": len(source_reports),
            "postCount": post_count,
            "matchedPostCount": total_matched_posts,
            "unmatchedPostCount": post_count - total_matched_posts,
            "matchRate": _coverage_rate(total_matched_posts, post_count),
            "mentionCount": total_mentions,
            "targetCount": len(total_target_keys),
            "candidateAliasCount": total_candidates,
        },
        "sources": source_reports,
    }


def parse_real_estate_match_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return _as_utc(value)
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return _as_utc(datetime.fromisoformat(normalized))


def _load_json_records(path: str | Path) -> list[dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8-sig").strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        if isinstance(payload, dict) and "items" in payload:
            records = payload.get("items", [])
        elif isinstance(payload, dict):
            records = [payload]
        else:
            records = payload
    if not isinstance(records, list):
        raise ValueError("real-estate matcher input must be JSON array, {items: []}, or JSONL")
    return [record for record in records if isinstance(record, dict)]


def _alias_from_mapping(record: dict[str, Any]) -> RealEstateAliasRule:
    target_type = str(record.get("targetType") or record.get("target_type") or "").strip()
    target_id = str(record.get("targetId") or record.get("target_id") or "").strip()
    alias = str(record.get("alias") or "").strip()
    if not target_type or not target_id or not alias:
        raise ValueError("real-estate alias requires targetType, targetId, and alias")
    return RealEstateAliasRule(
        target_type=target_type,
        target_id=target_id,
        alias=alias,
        alias_type=str(record.get("aliasType") or record.get("alias_type") or "official").strip() or "official",
        review_state=str(record.get("reviewState") or record.get("review_state") or "approved").strip().lower(),
        confidence=round(_float(record.get("confidence"), default=1.0), 2),
        ambiguous=bool(record.get("ambiguous", False)),
        source=str(record.get("source")).strip() if record.get("source") else None,
    )


def _post_from_mapping(record: dict[str, Any]) -> RealEstatePostForMatching:
    source = str(record.get("source") or "").strip()
    external_id = str(record.get("externalId") or record.get("external_id") or "").strip()
    published_at = record.get("publishedAt") or record.get("published_at")
    title = str(record.get("title") or "").strip()
    content_snippet = str(record.get("contentSnippet") or record.get("content_snippet") or record.get("content") or "").strip()
    if not source or not external_id or not published_at:
        raise ValueError("real-estate post requires source, externalId, and publishedAt")
    return RealEstatePostForMatching(
        source=source,
        external_id=external_id,
        published_at=parse_real_estate_match_datetime(published_at),
        title=title,
        content_snippet=content_snippet,
        url=str(record.get("url")).strip() if record.get("url") else None,
    )


def _is_confirmed_alias(alias: RealEstateAliasRule) -> bool:
    return alias.review_state.strip().lower() == "approved" and not alias.ambiguous


def _known_alias_keys_by_target(aliases: list[RealEstateAliasRule]) -> dict[tuple[str, str], set[str]]:
    known_alias_keys: dict[tuple[str, str], set[str]] = {}
    for alias in aliases:
        key = _match_key(alias.alias)
        if len(key) < 2:
            continue
        known_alias_keys.setdefault((alias.target_type, alias.target_id), set()).add(key)
    return known_alias_keys


def _parenthesized_aliases_after_text(text: str, matched_text: str) -> list[str]:
    if not text or not matched_text:
        return []
    aliases: list[str] = []
    start_at = 0
    while True:
        match_index = text.find(matched_text, start_at)
        if match_index == -1:
            return aliases
        cursor = match_index + len(matched_text)
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor < len(text) and text[cursor] in {"(", "["}:
            close_char = ")" if text[cursor] == "(" else "]"
            end_index = text.find(close_char, cursor + 1)
            if end_index != -1:
                candidate = text[cursor + 1:end_index].strip()
                if _looks_like_alias_candidate(candidate):
                    aliases.append(candidate)
        start_at = match_index + 1


def _looks_like_alias_candidate(value: str) -> bool:
    if len(_match_key(value)) < 2:
        return False
    if len(value) > 24:
        return False
    return True


def _alias_coverage_top_targets(
    matched_posts: list[RealEstateMatchedPost],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for matched_post in matched_posts:
        for mention in matched_post.mentions:
            key = (mention.target_type, mention.target_id)
            row = rows.setdefault(
                key,
                {
                    "targetType": mention.target_type,
                    "targetId": mention.target_id,
                    "mentionCount": 0,
                    "aliasTypes": set(),
                    "matchedTexts": set(),
                },
            )
            row["mentionCount"] += 1
            row["aliasTypes"].add(mention.alias_type)
            row["matchedTexts"].add(mention.matched_text)
    normalized_rows = [
        {
            "targetType": row["targetType"],
            "targetId": row["targetId"],
            "mentionCount": row["mentionCount"],
            "aliasTypes": sorted(row["aliasTypes"]),
            "matchedTexts": sorted(row["matchedTexts"]),
        }
        for row in rows.values()
    ]
    normalized_rows.sort(key=lambda row: (-row["mentionCount"], row["targetType"], row["targetId"]))
    return normalized_rows[:limit]


def _alias_coverage_unmatched_examples(
    matched_posts: list[RealEstateMatchedPost],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for matched_post in matched_posts:
        if matched_post.mentions:
            continue
        examples.append(
            {
                "externalId": matched_post.external_id,
                "publishedAt": _iso(matched_post.published_at),
                "title": matched_post.title,
                "url": matched_post.url,
            }
        )
        if len(examples) >= limit:
            break
    return examples


def _coverage_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _first_available_span(
    normalized_text: str,
    normalized_spans: list[tuple[int, int]],
    normalized_alias: str,
    existing_spans: list[tuple[int, int]],
) -> tuple[int, int] | None:
    start_at = 0
    while True:
        index = normalized_text.find(normalized_alias, start_at)
        if index == -1:
            return None
        span = (
            normalized_spans[index][0],
            normalized_spans[index + len(normalized_alias) - 1][1],
        )
        if not _inside_existing_span(span, existing_spans):
            return span
        start_at = index + 1


def _inside_existing_span(candidate: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    start, end = candidate
    return any(existing_start <= start and end <= existing_end for existing_start, existing_end in spans)


def _matchable_text_with_spans(value: str) -> tuple[str, list[tuple[int, int]]]:
    chars: list[str] = []
    spans: list[tuple[int, int]] = []
    for index, char in enumerate(value):
        normalized = _match_char(char)
        if not normalized:
            continue
        for normalized_char in normalized:
            chars.append(normalized_char)
            spans.append((index, index + 1))
    return "".join(chars), spans


def _match_key(value: str) -> str:
    return "".join(_match_char(char) for char in value)


def _match_char(char: str) -> str:
    normalized = char.casefold()
    if normalized.isalnum():
        return normalized
    return ""


def _float(value: object, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")
