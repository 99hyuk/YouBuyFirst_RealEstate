# Data AI Mention Resolver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the pipeline ask the AI provider to accept or reject matcher candidates before creating persisted mentions and analyses.

**Architecture:** Add an internal `MentionDecision` model and replace `LLMProvider.analyze` with `LLMProvider.resolve_mentions`. `CommunityPipeline._enrich` will convert accepted decisions into the existing `Mention` and `Analysis` payloads, keeping backend compatibility.

**Tech Stack:** Python 3.10+, pytest, existing pipeline dataclasses, OpenAI Responses JSON schema.

---

### Task 1: Provider Contract Tests

**Files:**
- Modify: `pipeline/tests/test_llm.py`

- [ ] **Step 1: Write the accepted mention test**

```python
def test_mock_llm_resolves_real_stock_mention_with_reaction_direction():
    provider = MockLLMProvider()

    decisions = provider.resolve_mentions(
        title="테슬라 강하다",
        content="TSLA 실적 기대감 때문에 매수세가 붙는 듯",
        mentions=[Mention(market="US", symbol="TSLA", matched_text="테슬라")],
    )

    assert len(decisions) == 1
    assert decisions[0].is_mentioned is True
    assert decisions[0].market == "US"
    assert decisions[0].symbol == "TSLA"
    assert decisions[0].reaction_direction == "bullish"
    assert 0 <= decisions[0].confidence <= 1
```

- [ ] **Step 2: Write the rejected mention test**

```python
def test_mock_llm_rejects_candidate_when_context_is_not_a_stock_mention():
    provider = MockLLMProvider()

    decisions = provider.resolve_mentions(
        title="애플 먹고 싶다",
        content="사과 가격이 너무 비싸서 장보기 힘들다",
        mentions=[Mention(market="US", symbol="AAPL", matched_text="애플")],
    )

    assert len(decisions) == 1
    assert decisions[0].is_mentioned is False
    assert decisions[0].reaction_direction == "neutral"
```

- [ ] **Step 3: Verify RED**

Run: `python -m pytest tests/test_llm.py::test_mock_llm_resolves_real_stock_mention_with_reaction_direction tests/test_llm.py::test_mock_llm_rejects_candidate_when_context_is_not_a_stock_mention -q`

Expected: FAIL because `MockLLMProvider.resolve_mentions` does not exist.

### Task 2: Pipeline Filtering Test

**Files:**
- Create: `pipeline/tests/test_pipeline.py`

- [ ] **Step 1: Write the `_enrich` filtering test**

```python
def test_enrich_keeps_only_ai_accepted_mentions_and_analyses():
    post = RawPost(
        source="TEST",
        external_id="1",
        url="https://example.com/1",
        title="애플 먹고 싶고 테슬라 강하다",
        content="사과 이야기는 종목이 아니고 TSLA는 실적 기대",
        author="sample",
        published_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
    )
    matcher = InstrumentMatcher(
        [
            Instrument(market="US", symbol="AAPL", name="Apple", aliases=["애플"]),
            Instrument(market="US", symbol="TSLA", name="Tesla", aliases=["테슬라"]),
        ]
    )
    pipeline = CommunityPipeline(adapters=[], matcher=matcher, llm_provider=MockLLMProvider(), client=_NoopClient())

    enriched = pipeline._enrich(post)

    assert [(mention.market, mention.symbol, mention.matched_text) for mention in enriched.mentions] == [
        ("US", "TSLA", "테슬라")
    ]
    assert [(analysis.market, analysis.symbol, analysis.sentiment) for analysis in enriched.analyses] == [
        ("US", "TSLA", "bullish")
    ]
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_pipeline.py::test_enrich_keeps_only_ai_accepted_mentions_and_analyses -q`

Expected: FAIL because `_enrich` still sends every matcher candidate through as a mention.

### Task 3: Implement Contract

**Files:**
- Modify: `pipeline/src/youbuyfirst_pipeline/models.py`
- Modify: `pipeline/src/youbuyfirst_pipeline/llm.py`
- Modify: `pipeline/src/youbuyfirst_pipeline/pipeline.py`
- Modify: `pipeline/tests/test_llm.py`
- Create: `pipeline/tests/test_pipeline.py`

- [ ] **Step 1: Add `MentionDecision`**

```python
@dataclass(frozen=True)
class MentionDecision:
    market: str
    symbol: str
    matched_text: str
    is_mentioned: bool
    reaction_direction: str
    confidence: float
    rationale: str
    model: str
```

- [ ] **Step 2: Rename provider contract to `resolve_mentions`**

Implement the mock and OpenAI providers so they return `list[MentionDecision]`.

- [ ] **Step 3: Filter accepted decisions in `_enrich`**

`CommunityPipeline._enrich` should create `Mention` and `Analysis` only from decisions where `is_mentioned` is true.

- [ ] **Step 4: Verify GREEN**

Run: `python -m pytest tests/test_llm.py tests/test_pipeline.py -q`

Expected: PASS.

### Task 4: Full Verification

**Files:**
- No new files.

- [ ] **Step 1: Run pipeline tests**

Run: `python -m pytest tests -q`

Expected: PASS for all pipeline tests.

- [ ] **Step 2: Run whitespace check**

Run: `git diff --check`

Expected: no output and exit code 0.
