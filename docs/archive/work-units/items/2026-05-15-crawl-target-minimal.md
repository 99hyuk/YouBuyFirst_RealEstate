# Work Unit: CrawlTarget Minimal

## Goal

Introduce `CrawlTarget` as the explicit crawl execution unit below source policy and above crawler adapters.

## Scope

- Add a static `CrawlTarget` model for stock-board and community-board targets.
- Build MVP Naver and FM Korea targets from instruments and environment values.
- Create crawler adapters from targets in `main.build_pipeline()`.
- Attach target metadata to adapters.
- Include target metadata in `CommunityPipeline.run_once()` result dictionaries.
- Add regression tests for target construction and result metadata.

## Out of Scope

- Backend schema or ingestion API changes.
- Admin API, admin page, or persistent target editing.
- Backoff queue, retry scheduling, or per-target source policy.
- New crawler sources.
- Public operation approval for any source.

## Verification

- Focused Docker pipeline tests for crawl targets and source policy result metadata pass.
- Full Docker Python 3.10 pipeline test suite passes with 24 tests.
- `git diff --check` passes.

## Notes

Source policy remains the upper gate. `CrawlTarget` describes what would run if the source is allowed; it does not authorize a source by itself.
