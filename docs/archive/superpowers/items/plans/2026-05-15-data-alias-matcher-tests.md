# Data Alias Matcher Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand data-track matcher coverage for alias overlap and ticker boundaries, then fix only the matcher behavior proven broken by the new tests.

**Architecture:** Keep the matcher as a small in-memory scanner over `Instrument` aliases. Preserve the existing output contract of one `Mention` per unique `(market, symbol, matched_text)` in a post, while allowing a shorter alias to be reported when it appears separately outside a longer alias span for the same instrument.

**Tech Stack:** Python 3.10+, pytest, existing `youbuyfirst_pipeline.matcher.InstrumentMatcher`.

---

### Task 1: Add Matcher Boundary Tests

**Files:**
- Modify: `pipeline/tests/test_matcher.py`

- [ ] **Step 1: Write the failing overlap test**

```python
def test_matches_short_alias_when_it_appears_again_outside_long_alias():
    matcher = InstrumentMatcher(
        [
            Instrument(market="US", symbol="NVDA", name="NVIDIA", aliases=["엔비디아", "엔비"]),
        ]
    )

    mentions = matcher.match("엔비디아는 강하고 엔비도 같이 언급됨")

    assert [(m.market, m.symbol, m.matched_text) for m in mentions] == [
        ("US", "NVDA", "엔비디아"),
        ("US", "NVDA", "엔비"),
    ]
```

- [ ] **Step 2: Write the existing ticker-boundary coverage test**

```python
def test_ascii_tickers_require_token_boundaries():
    matcher = InstrumentMatcher(
        [
            Instrument(market="US", symbol="TSLA", name="Tesla", aliases=["테슬라"]),
        ]
    )

    mentions = matcher.match("TSLAX와 myTSLAwatch는 제외하고 tsla는 언급")

    assert [(m.market, m.symbol, m.matched_text) for m in mentions] == [
        ("US", "TSLA", "TSLA"),
    ]
```

- [ ] **Step 3: Run the overlap test to verify it fails**

Run: `python -m pytest pipeline/tests/test_matcher.py::test_matches_short_alias_when_it_appears_again_outside_long_alias -q`

Expected: FAIL because the matcher currently checks only the first occurrence of a non-ASCII alias, so `엔비` inside `엔비디아` hides the later standalone `엔비`.

### Task 2: Scan Later Alias Occurrences

**Files:**
- Modify: `pipeline/src/youbuyfirst_pipeline/matcher.py`
- Test: `pipeline/tests/test_matcher.py`

- [ ] **Step 1: Replace single-span lookup with first available span lookup**

```python
span = _find_first_available_span(
    text=upper_text if pattern else text,
    alias=alias.upper() if pattern else alias,
    pattern=pattern,
    existing_spans=spans_by_instrument.get(instrument_key, []),
)
```

- [ ] **Step 2: Add the helper**

```python
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
```

- [ ] **Step 3: Run matcher tests**

Run: `python -m pytest pipeline/tests/test_matcher.py -q`

Expected: PASS for all matcher tests.

- [ ] **Step 4: Run pipeline tests**

Run: `python -m pytest pipeline/tests -q`

Expected: PASS for all pipeline tests.
