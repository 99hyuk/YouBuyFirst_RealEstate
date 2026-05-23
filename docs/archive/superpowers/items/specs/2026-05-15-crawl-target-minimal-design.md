# CrawlTarget Minimal Design

## Background

The crawl pipeline currently builds crawler adapters directly from environment variables and instruments. That works for the MVP, but it leaves no explicit unit for "Samsung Naver board", "SK Hynix Naver board", or "FM Korea stock board". Source policy already decides whether a source may run in the current runtime. `CrawlTarget` should sit below that policy as the concrete execution unit.

## Goals

- Represent crawler work as explicit target objects before adapters are created.
- Keep source policy as the higher-level gate. A target does not make a source runnable by itself.
- Preserve the existing backend ingestion contract. This PR does not add DB migrations, admin APIs, or backend `SKIPPED` states.
- Make local run output easier to inspect by including target metadata in `run_once()` results.

## Non-Goals

- No persistent target table.
- No admin page or API for editing targets.
- No backoff queue, retry priority scheduler, or source review checklist.
- No new crawler source.
- No legal judgement that a source is safe for public operation.

## Design

Add `pipeline/src/youbuyfirst_pipeline/crawl_targets.py` with:

- `CrawlTargetKind`
  - `stock-board`: a board tied to one stock symbol, such as a Naver stock discussion board.
  - `community-board`: a broad community board, such as FM Korea stock board.
- `CrawlTarget`
  - `source`
  - `target_id`
  - `kind`
  - optional `market`, `symbol`, `url`
  - `priority`
  - `label`
- helper constructors for stock-board and community-board targets.
- `default_crawl_targets()` to build the MVP target list from instruments and environment values.

The `main.build_pipeline()` path will build targets first, then create adapters from those targets:

- `NAVER` stock-board targets become `NaverBoardAdapter(fetcher, stock_code=target.symbol)`.
- `FMKOREA` community-board targets become `FmkoreaAdapter(fetcher, url=target.url)`.

Adapters will keep a `target` attribute. `CommunityPipeline.run_once()` will continue to gate by `adapter.source`, then include `targetId` and `targetLabel` in returned result dictionaries when available.

## Data Flow

```text
env + instruments
-> default_crawl_targets()
-> adapters from targets
-> CommunityPipeline.run_once()
-> source policy gate by source
-> target adapter fetch
-> parser/enrichment/ingestion
-> run result includes target metadata
```

## Testing

- Unit tests prove default targets include one Naver target per selected KR symbol and one FM Korea community target.
- Unit tests prove target ids are deterministic and source names are normalized.
- Pipeline tests prove skipped/empty/ingested results include target metadata.
- Existing crawler and source policy tests must continue passing.

## Risks

- This is not yet a real queue. The `priority` field is a stable contract for the next PR, not a scheduler behavior change.
- Source policy still gates by source, not individual target. Per-target policy can be added later if needed, but starting source-level keeps the public-operation boundary conservative.
