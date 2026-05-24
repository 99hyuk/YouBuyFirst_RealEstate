# 너나사 (YouBuyFirst) 작업 지도

이 문서는 다음 작업을 고르기 위한 현재 기준입니다. 완료 상세 이력은 PR, Notion 작업 로그, `docs/archive/work-units/items/`에서 찾습니다.

## 기준

너나사는 단순 ingestion MVP가 아니라 완제품을 향해 세로로 쌓아 가는 투자 참고형 시뮬레이터입니다. 완제품 기준은 `docs/product/FINAL_PRODUCT_PLAN.md`이고, 현재 구현은 그중 커뮤니티 수집/저장 기반과 일부 market/ui 기반이 먼저 깔린 상태입니다.

최종 사용 루프는 다음 순서입니다.

1. 관심종목에서 가격, 거래량, 커뮤니티 반응, 뉴스/공시 변화가 감지됩니다.
2. 사용자는 종목 상세에서 변화 원인, 근거 링크, 신뢰도/주의 배지를 확인합니다.
3. 개미 심리 지수와 커뮤니티별 반응 흐름으로 시장 분위기를 봅니다.
4. 모의 포트폴리오와 에이전트 paper trading으로 판단 결과를 복기합니다.
5. 이후 유사 상황 검색, 알림, OCR 자산 연동, 부동산 버티컬을 확장합니다.

## 운영 원칙

- 업무는 과거의 제외 목록이 아니라 `완제품을 구성하는 세로 slice` 기준으로 뽑습니다.
- 한 PR은 하나의 primary work area를 가집니다. 영역 기준은 `docs/layers/ops/WORK_AREAS.md`를 따릅니다.
- ui가 먼저 발견한 API 후보는 screen brief에 남기고, backend/pipeline은 그 계약을 실제 데이터로 채웁니다.
- 토큰 최적화 때문에 필요한 기획, 계약, 검증, PR/Notion 기록을 생략하지 않습니다. 대신 큰 로그와 archive 전문 출력을 막습니다.
- 투자 자문처럼 보이는 표현, 원문 재게시, 로그인/CAPTCHA/프록시/fingerprint 우회는 하지 않습니다.

## 지금 우선순위

아래 순서가 현재 가장 합리적인 진행 순서입니다. 프론트만 계속 다듬기보다, 화면에서 필요한 데이터 계약을 정하고 backend/pipeline을 같이 붙입니다.

- [ ] ui 화면별 Screen Brief를 최신 화면 기준으로 맞추고, 각 화면의 필수 API 후보를 `dashboard`, `stocks`, `stock-detail`, `newsroom`, `human-indicator`, `portfolio` 순서로 정리
- [ ] stock 종목 마스터를 국내 주식/ETF + 미국 주식/ETF 기준으로 확장하고, provider symbol, alias, 표시명, 시장 구분을 같은 키로 연결
- [ ] market quote/chart/investor-flow provider 계약을 안정화하고, yfinance + FinanceDataReader 기준의 delay/asOf/stale/dataStatus 표시 규칙을 고정
- [ ] community source registry를 에펨코리아, 네이버 종토방, 뽐뿌 증권포럼, 디시 미국주식/주식갤러리/국내주식 후보까지 확장하되 소스 상태와 공개 가능 범위를 분리
- [ ] indicator 개미 심리 지수 산식 v1을 확정하고, 언급량 변화, 반응 방향, 표현 강도, 인기글 확산, 소스 다양성, 표본 신뢰도, 시세 지연을 입력으로 묶기
- [ ] stock detail 이벤트 타임라인 계약을 정리하고, 뉴스/공시/리포트/영상/블로그/커뮤니티/가격 이벤트를 같은 시간축으로 표시하는 응답 shape 설계
- [ ] simulation 가상 계좌, 주문, 예약, 체결, 정산, 원장, 포지션, 손익 계산의 트랜잭션 경계를 먼저 설계
- [ ] agent 판단 key, strategy version, input window, idempotency key를 설계해 같은 통계 window에서 중복 판단/중복 주문이 나지 않게 만들기
- [ ] backend/pipeline 기존 ingestion 기반을 실제 화면 API로 연결하기 위해 readiness wait, Swagger 예시, validation 오류 응답, fixture와 실제 데이터 전환 기준 정리

## 제품 세로 Slice

### Slice A. 관심종목 브리핑

- [ ] 관심종목 source를 사용자가 등록한 종목, 모의 포트폴리오 보유 종목, 최근 본 종목으로 나누기
- [ ] 관심종목별 가격/거래량/언급량/개미 심리 지수 변화 요약 API 설계
- [ ] 신뢰도/주의 배지: 표본 부족, 특정 커뮤니티 편중, 시세 지연, 기사 없음, 원문 확인 필요
- [ ] dashboard와 portfolio에서 같은 briefing contract를 재사용

### Slice B. 종목 상세

- [ ] quote snapshot, chart candles, 국내 수급, 커뮤니티 반응 추이를 한 화면에서 분리 표시
- [ ] 팩트폭격 배너는 커뮤니티 요약이 아니라 시황/기술지표/재무/뉴스 기반으로 생성
- [ ] 뉴스/공시/리포트/영상/블로그/커뮤니티 링크 카드와 이벤트 타임라인 연결
- [ ] 데이터 실패 시 0값처럼 보이지 않게 영역별 empty/stale/error 상태 표시

### Slice C. 인간 지표

- [ ] 개미 심리 지수 ranking, 급변 종목, 공포/과열/무관심 구간 표시
- [ ] 커뮤니티별 반응 분포와 확산 레이어를 같은 종목 키로 연결
- [ ] 커뮤니티별 paper 성과 비교: 추종/역추종, 1시간/6시간/24시간/3일/7일 기준
- [ ] 인기글/개념글/추천글 기준을 source별로 다르게 정의

### Slice D. 모의 포트폴리오와 원장

- [ ] 가상 예수금과 주문 예약을 원장 기준으로 기록
- [ ] 체결/정산/포지션/손익 갱신을 하나의 트랜잭션 경계로 묶기
- [ ] batch 재시도와 부분 실패에도 원장과 포지션을 재계산 가능하게 만들기
- [ ] 체결 이후 커뮤니티 반응, 뉴스, 가격 변화를 복기 strip으로 연결

### Slice E. AI 에이전트 실험

- [ ] 역발상, 모멘텀, 리스크 관리형, 관망형 persona의 입력값과 판단 결과 필드 정의
- [ ] agent decision log에 input window, strategy version, decision key, skip reason 저장
- [ ] agent는 주문/체결을 직접 수정하지 않고 simulation contract를 통해서만 요청
- [ ] 사용자 화면에는 내부 추론 전문이 아니라 짧은 판단 근거와 데이터 상태만 표시

### Slice F. 데이터 확장

- [ ] 뉴스/공시 provider 후보와 링크 표시 정책 정리
- [ ] 증권 유튜브 영상, 신뢰 블로그 whitelist, 인기글/개념글 링크 수집 정책 정리
- [ ] 임베딩/클러스터링은 수집 데이터가 쌓인 뒤 토픽 묶음과 과거 유사 상황 검색으로 도입
- [ ] 벡터DB는 RAG/유사 상황 검색/질문형 분석이 제품 기능이 될 때 도입 후보로 검토

## 작업 영역별 백로그

### stock

- [ ] 국내/미국 종목 master seed와 provider symbol 매핑
- [x] alias registry와 은어 후보 관리: 확정 alias와 후보 alias를 분리하고, 후보는 집계에 바로 넣지 않고 `instrument_alias_candidates`로 누적
- [ ] 커뮤니티 종목 후보와 market provider symbol을 같은 canonical key로 연결: 전체 국내/미국 master 확장과 provider suffix 정렬은 후속 작업

### community

- [ ] source/board registry와 `CrawlTarget` 우선순위 기준 정리
- [ ] 일반 게시판형과 종목 게시판형 수집 정책 분리
- [x] 인기글/개념글/조회수/추천수 확산 이벤트 저장/전달 계약 추가
- [x] source별 인기글/개념글/추천글 URL registry와 기본 target 활성화 기준 정리
- [ ] 확산/급증/고영향 글 기준 댓글 제한 수집 트리거 구현
- [ ] 제목, 제한 snippet, URL, 작성자 hash, 작성 시각, 원문 hash 저장 정책 점검

### indicator

- [ ] `CommunityMetricSnapshot`와 `RetailSentimentIndex` 응답 shape 설계
- [ ] 30분/1일/1주 window 집계 테스트 추가
- [ ] 소스 다양성, 표본 수, 신뢰도 배지 산식 분리
- [ ] 과거 유사 반응 상황 검색 후보 데이터 모델 정리

### market

- [ ] quote snapshot, chart candle, investor flow API 계약과 화면 표시 규칙 유지
- [ ] yfinance + FinanceDataReader provider 실패, 빈 배열, stale 처리 테스트
- [ ] 국내 수급은 quote와 분리하고, 전 거래일 기준/derived 여부를 명확히 표시
- [ ] Redis quote cache와 WebSocket은 실제 갱신량이 생긴 뒤 도입

### simulation

- [ ] `Account`, `Order`, `Execution`, `LedgerEntry`, `Position` 최소 모델 설계
- [ ] 주문 예약, 체결, 취소, 정산의 상태 전이와 idempotency 규칙 설계
- [ ] 리더보드는 원장과 가격 snapshot으로 재계산 가능하게 설계

### agent

- [ ] `AgentDecision` key와 strategy version 관리
- [ ] 종목 상태 팩트폭격 헤드라인 생성 입력과 금지 표현 검사
- [ ] 커뮤니티별 성과 비교 실험의 추종/역추종 규칙과 기준 수익률 정의
- [ ] 판단 로그를 Notion/포트폴리오 기술 경험으로 설명 가능한 문제 해결 사례로 남기기

### ui

- [ ] `front/`의 실제 화면과 `docs/layers/ui/screens/`를 항상 동기화
- [ ] 디자인 시스템 토큰과 공통 컴포넌트 후보를 새 화면에 적용
- [ ] stock detail, newsroom, human indicator, portfolio의 empty/loading/stale/error 상태 구현
- [ ] 브라우저 QA는 최종 화면 단위로 실행하고 결과만 짧게 기록

### ops

- [ ] 열린 branch/worktree를 active, review, blocked, stale, close-candidate로 주기 점검
- [ ] PR/Notion 라벨은 작업 영역 값으로 맞추되 기존 형식은 유지
- [ ] 문서가 MVP-only 표현으로 돌아가면 product/current/domain 정본 기준으로 정리
- [ ] 완료 이력은 TASKS에 길게 누적하지 않고 PR/Notion/archive로 보냄

## 후순위

- [ ] OCR 자산 연동과 S3 Presigned URL 업로드
- [ ] Telegram 또는 앱 알림
- [ ] Spring Security 인증/인가
- [ ] 운영 배포와 모니터링
- [ ] 사용자 반응방/게시판/채팅
- [ ] 벡터DB 기반 질문형 분석
- [ ] 부동산 버티컬

## 현재 완료 기반

- ingestion MVP: 커뮤니티 글 수집, 종목 언급 인식, 반응 방향 분석, backend 저장
- backend: ingestion/admin API, crawl run/posts/stock metrics 조회, `CrawlTarget` queue API
- pipeline: source policy gate, skip run 기록, crawl backoff, AI mention resolver/mock provider
- market: quote snapshot, chart candle, investor flow public API 기반
- ui: Vue 3 + Vite + TypeScript mock shell과 주요 Screen Brief
- ops: domain/layer 문서 구조, PR/라벨/branch/worktree 기준

## 작업 메모

- 작업 단위는 하나의 체크박스 또는 강하게 묶인 2-3개 체크박스로 제한합니다.
- 작업을 시작하면 `codex/<task-name>` 브랜치에서 진행합니다.
- 구현 전에 관련 테스트를 먼저 추가하거나 기존 테스트를 확장합니다.
- PR 설명에는 변경 범위, 사람이 읽기 쉬운 검증 결과, 남은 리스크를 포함합니다.
- 병렬 작업은 관련 도메인/layer `AGENTS.md`의 관련 섹션을 먼저 확인하고, 세부 색인이 필요할 때만 README를 봅니다.
