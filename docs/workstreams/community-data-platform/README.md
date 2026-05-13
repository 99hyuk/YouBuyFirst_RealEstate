# community-data-platform

## 역할

커뮤니티 글을 안정적으로 수집하고, 어떤 소스를 어떤 조건에서 수집할지 관리합니다. 이 트랙은 감성 분석 자체보다 "좋은 입력 데이터를 안전하게 가져오는 일"에 집중합니다.

## 담당 범위

- 네이버 종토방 adapter
- 에펨코리아 adapter
- 향후 디시인사이드, 토스 종목 커뮤니티 adapter 검토
- 일반 게시판형/종목 게시판형 수집 전략
- `CrawlTarget` 우선순위 큐
- source run 상태, 실패 사유, backoff
- robots.txt, 약관, 차단 상태 기록
- 제한 원문 저장 정책

## 파일 소유권

주로 담당:

- `worker/src/youbuyfirst_worker/crawlers/`
- `worker/src/youbuyfirst_worker/scheduler.py`
- `worker/tests/fixtures/`
- crawler 관련 backend ingestion payload contract
- `docs/LEGAL_RISK_CASES.md`

공유 전 협의:

- DB migration
- `Instrument` schema
- ingestion API request/response
- `docs/FINAL_PRODUCT_PLAN.md`

## 현재 우선순위

1. 실제 네이버 종토방 HTML 구조에 맞춘 parser 보강
2. 실제 에펨코리아 주식 게시판 구조에 맞춘 parser 보강
3. 종목 게시판형 소스를 위한 `CrawlTarget` 설계
4. 소스별 `enabled`, `public-demo-only`, `local-research-only`, `disabled` 상태 도입

## 하지 않는 일

- LLM 감성 산식 변경
- 사용자 대시보드 UI
- 모의투자 체결 엔진
- 로그인, CAPTCHA, 프록시, fingerprint 우회
