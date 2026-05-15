# agent

## 역할

AI 전략 에이전트를 담당합니다. `data`의 커뮤니티 신호, `market`의 가격 snapshot, `trade`의 포트폴리오 상태를 읽고 매수, 매도, 관망 판단과 근거 로그를 만듭니다.

이 트랙은 판단을 만들지만 체결 장부를 직접 수정하지 않습니다. 주문 실행은 `trade` contract를 통해 요청합니다.

## 담당 범위

- 에이전트 페르소나
- 역발상 매매 판단
- 커뮤니티별 성과 비교 에이전트
- 매매 판단 입력 데이터 조합
- 사용자용 결정 근거 로그
- 에이전트별 성과 리더보드 입력
- 판단 실패 fallback과 disabled default 정책

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

공유 전 협의:

- analysis/indicator schema
- community performance snapshot schema
- quote snapshot contract
- trade order request contract
- dashboard API contract

## 현재 우선순위

1. 에이전트 입력 contract 설계
2. 역발상 페르소나 최소 판단 규칙 문서화
3. 커뮤니티별 성과 비교 에이전트의 데이터 의존성 분리
4. 결정 근거 로그 schema 설계

## 하지 않는 일

- 커뮤니티 크롤링
- 종목 인식과 반응 방향 분류
- quote provider 직접 호출
- 주문/체결 장부 수정
- UI 레이아웃 구현
