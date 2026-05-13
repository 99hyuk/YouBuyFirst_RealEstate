# 인간지표 MVP: 커뮤니티 크롤링/감성 수집 파이프라인

## Summary

MVP는 네이버 종토방과 에펨코리아에서 신규 글 묶음을 30분 주기로 수집하고, 국내 종목과 미국 상장 주식/ETF 언급을 인식해 종목별 언급량과 bullish/bearish/neutral 심리를 저장한다. Spring Boot가 API, 검증, 중복 제거, 저장, Swagger 조회를 담당하고 Python worker가 Playwright 기반 크롤링과 LLM 분석을 담당한다.

## Scope

포함:

- Spring ingestion API와 admin 조회 API
- MySQL schema와 sample instrument seed
- Python crawler adapter, instrument matcher, LLM provider abstraction
- Docker Compose 로컬 시연 환경

제외:

- 사용자 인증, Spring Security, 대시보드 UI
- OCR 자산 연동, 모의투자, AI 3줄 요약
- CAPTCHA 회피, 로그인 세션 활용, 차단 회피용 프록시/지문 위장

## Data Flow

1. Python worker가 30분마다 community adapter를 실행한다.
2. adapter는 공개 HTTP 요청을 우선 사용하고, 필요하면 Playwright 렌더링 fallback을 사용한다.
3. worker가 종목 마스터 CSV의 티커/한글명/영문명/별칭으로 게시글 언급 종목을 매칭한다.
4. LLM provider가 종목별 sentiment와 confidence를 만든다.
5. worker가 `POST /internal/ingestions/community-posts`로 Spring에 결과를 전송한다.
6. Spring은 source + externalId 기준으로 중복을 제거하고 제한 원문, mentions, sentiments, 30분 metric snapshots를 저장한다.

## Interfaces

- `POST /internal/ingestions/community-posts`
  - request: source, runId, batchStartedAt, batchFinishedAt, posts
  - post: externalId, url, title, contentSnippet, authorDisplayName, publishedAt, mentions, sentiments
  - response: source, runId, seenPosts, acceptedPosts, duplicatePosts
- `GET /admin/crawl-runs`
- `GET /admin/posts`
- `GET /admin/stocks/{symbol}/metrics?market=US`
- `POST /internal/ingestions/crawl-runs`
  - failed/blocked source runs are recorded without storing posts.

## Data Policy

게시글 원문은 제목, 본문 일부, URL, 작성 시각, 작성자 표시명 해시, 원문 해시만 저장한다. MVP의 원문 보관 기간은 30일이며, Spring 스케줄러가 매일 UTC 기준 만료 게시글을 삭제한다.

## Testing

- Spring ingestion integration test: idempotency, validation, metric creation
- Python matcher test: `삼전`, `삼성전자`, `TSLA`, `테슬라`, `NVDA`, `엔비디아`
- Python LLM mock test: structured sentiment schema
- Python crawler fixture test: 네이버/에펨코리아 목록 HTML parsing
