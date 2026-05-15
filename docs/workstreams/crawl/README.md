# crawl

## 역할

커뮤니티 글을 안정적으로 수집하고, 어떤 소스를 어떤 조건에서 수집할지 관리합니다. 이 트랙은 반응 방향 분석 자체보다 "좋은 입력 데이터를 안전하게 가져오는 일"에 집중합니다.

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

- `pipeline/src/youbuyfirst_pipeline/crawlers/`
- `pipeline/src/youbuyfirst_pipeline/scheduler.py`
- `pipeline/tests/fixtures/`
- crawler 관련 backend ingestion payload contract
- `docs/LEGAL_RISK_CASES.md`

공유 전 협의:

- DB migration
- `Instrument` schema
- ingestion API request/response
- data 분석 payload contract
- `docs/FINAL_PRODUCT_PLAN.md`

## 현재 우선순위

1. 게시판 parser 견고화 PR #33 리뷰와 merge 여부 결정
2. 종목 게시판형 소스를 위한 `CrawlTarget` 설계
3. source policy skip 상태와 crawl run 기록의 운영 표시 방식 정리
4. crawl run 실패/차단 원인별 backoff 정책 세분화

소스별 활성화 상태의 의미와 트랙별 책임은 `docs/superpowers/specs/2026-05-15-source-activation-state-design.md`를 기준으로 봅니다. source policy registry와 scheduler gate는 구현되어 있으며, `CrawlTarget`은 이 상태값보다 아래 단계의 실행 단위입니다.

## 하지 않는 일

- LLM 반응 방향 산식 변경
- 종목별 반응 지표/열기 지수 집계
- 사용자 대시보드 UI
- 모의투자 체결 엔진
- 로그인, CAPTCHA, 프록시, fingerprint 우회
