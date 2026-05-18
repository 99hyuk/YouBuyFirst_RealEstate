# crawl

## 역할

커뮤니티 글을 안정적으로 수집하고, 어떤 소스를 어떤 조건에서 수집할지 관리합니다. 이 트랙은 반응 방향 분석 자체보다 "좋은 입력 데이터를 안전하게 가져오는 일"에 집중합니다.

## 담당 범위

- 네이버 종토방 adapter
- 에펨코리아 adapter
- 뽐뿌 증권포럼 adapter 후보
- 디시인사이드 미국 주식 갤러리, 주식갤러리, 국내주식 계열 갤러리 adapter 후보
- 클리앙 주식한당, 팍스넷, 딴지 주식클럽, 네이버 카페형 미국주식, 오늘의유머/개드립/이토랜드/MLB파크 내 주식 글 source registry 검토 후보
- 향후 토스 종목 커뮤니티 adapter 검토
- 일반 게시판형/종목 게시판형 수집 전략
- 인기글/개념글/추천글/조회수 상위글 수집 전략
- 신뢰 블로그 whitelist 기반 source registry 후보
- `CrawlTarget` 우선순위 큐
- source/board registry: `source`, `boardId`, `displayName`, `marketScope`, `crawlPolicy`
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

1. pipeline이 backend `CrawlTarget` API를 사용하되 static target fallback을 유지하도록 연결
2. admin target pause/resume/clear-backoff API와 화면 액션 연결
3. source별 robots/약관 검토 결과 기록 방식 정리
4. 인기글/개념글/추천글을 최신 글 수집의 대체가 아니라 확산 확인 레이어로 분리
5. 신뢰 블로그 whitelist와 블로그별 수집 정책 후보 정리
6. pipeline이 backend readiness를 기다리도록 개선

소스별 활성화 상태의 의미와 트랙별 책임은 `docs/superpowers/specs/2026-05-15-source-activation-state-design.md`를 기준으로 봅니다. persistent `CrawlTarget` queue와 DB 기반 backoff 상태 설계는 `docs/superpowers/specs/2026-05-15-crawl-target-queue-design.md`를 기준으로 봅니다. source policy는 `CrawlTarget`보다 상위 게이트이고, `CrawlTarget`은 허용된 소스 안에서 어느 게시판/종목을 언제 다시 수집할지 정하는 실행 단위입니다.

추가 커뮤니티 후보는 바로 adapter를 만들지 않습니다. 먼저 `disabled` source 후보로 두고 robots/약관, 공개 목록 접근성, 글 빈도, 조회/추천/댓글 필드, 광고성/홍보성 노이즈, 종목 인식 난이도를 검토한 뒤 `local-research-only` 또는 구현 후보로 올립니다.

## 하지 않는 일

- LLM 반응 방향 산식 변경
- 종목별 반응 지표/열기 지수 집계
- 사용자 대시보드 UI
- 모의투자 체결 엔진
- 로그인, CAPTCHA, 프록시, fingerprint 우회
