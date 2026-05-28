# agent

## 역할

AI 전략 에이전트를 담당합니다. `community`의 반응 데이터, `indicator`의 지표 snapshot, `market`의 가격 snapshot, `simulation`의 포트폴리오 상태를 읽고 매수, 매도, 관망 판단과 근거 로그를 만듭니다.

이 도메인은 판단을 만들지만 체결 장부를 직접 수정하지 않습니다. 주문 실행은 `simulation` contract를 통해 요청합니다.

에이전트는 사용자의 즉시 주문 명령을 대신 결제하는 주체가 아니라, 30분 집계와 가격 snapshot 같은 통계 윈도우를 보고 paper trading 결정을 남기는 전략 평가 주체입니다. 같은 에이전트가 같은 윈도우, 종목, 전략 버전으로 판단을 두 번 만들지 않도록 판단 key와 scheduler idempotency를 명확히 둡니다.

## 담당 범위

- 에이전트 페르소나
- 역발상 매매 판단
- 통합 커뮤니티 지표 기반 paper trading 에이전트
- 백테스팅 기반 모의 전략 성과 비교
- 매매 판단 입력 데이터 조합
- `agentId + windowStart + symbol + strategyVersion` 기준 판단 중복 방지
- 사용자용 결정 근거 로그
- 에이전트별 성과 리더보드 입력
- 판단 실패 fallback과 disabled default 정책
- 종목 상세 팩트폭격 헤드라인의 `headlineTone`, `headline`, `subtitle` 생성 또는 선택 규칙

추천 브랜치 예시:

- `codex/agent-personas`
- `codex/agent-contrarian-decision-log`
- `codex/agent-community-performance-selector`

## 파일 소유권

주로 담당:

- agent strategy domain
- agent decision log
- agent runtime scheduler
- agent evaluation fixture
- agent decision idempotency test

공유 전 협의:

- indicator schema
- community performance snapshot schema
- quote snapshot contract
- stock detail roast headline API contract
- simulation order request contract
- dashboard API contract

## 현재 우선순위

1. 에이전트 입력 contract 설계
2. 판단 key와 scheduler 중복 실행 방지 규칙 문서화
3. 역발상 페르소나 최소 판단 규칙 문서화
4. 통합 지표 기반 성과 비교 에이전트의 데이터 의존성 분리
5. 결정 근거 로그 schema 설계
6. 종목 상세 팩트폭격 헤드라인의 evidence 기반 tone 선택 규칙 설계

## 통합 커뮤니티 에이전트 기준

에이전트는 source별 판단 주체로 나누지 않습니다. `FMKOREA 에이전트`, `DC 에이전트`처럼 특정 커뮤니티 이름을 가진 전략 주체를 만들면 crawler source가 제품 전면에 드러나고, 특정 커뮤니티의 반응을 투자법처럼 보이게 만들 위험이 큽니다.

허용하는 구조:

- 하나의 통합 커뮤니티 에이전트가 `StockReactionWindow`, `개미 심리 지수`, `issueMix`, 가격/거래량 snapshot을 읽습니다.
- 같은 전략 rule을 source-only slice에 적용하는 실험은 내부 검증으로만 둡니다.
- 사용자 화면에는 source별 우열 대신 `반응 일관성`, `표본 신뢰도`, `coverage`, `과거 유사 상황`을 표시합니다.

백테스팅과 나만의 모의 전략은 agent와 simulation의 접점입니다. agent는 strategy rule, 판단 key, 근거 로그를 소유하고, 수익률 계산과 원장/체결 정합성은 simulation contract를 따릅니다. RAG는 판단 계산기가 아니라 과거 유사 window와 백테스트 결과를 설명하는 보조 레이어로만 사용합니다.

## 하지 않는 일

- 커뮤니티 크롤링
- 종목 인식과 반응 방향 분류
- quote provider 직접 호출
- 주문/체결 장부 수정
- 실제 결제 또는 실거래 지시
- UI 레이아웃 구현
