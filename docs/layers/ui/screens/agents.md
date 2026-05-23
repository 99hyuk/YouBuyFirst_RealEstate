# 에이전트 하위 화면

## Route

- Parent: 인간 지표
- Route 후보: `/agents`는 `/communities?view=agents`로 redirect합니다.
- Child screens: 판단 로그 상세 drawer는 후보입니다.

## 화면 목적

에이전트를 독립 탭으로 두지 않고, 커뮤니티 반응을 해석한 모의 실험 레이어로 보여줍니다. 사용자는 인간 지표 화면 안에서 커뮤니티 반응, 성과 실험, 모의 에이전트 판단을 같은 맥락으로 확인합니다.

## 현재 섹션

- 인간 지표 하위 탭: 커뮤니티 반응, 성과 실험, 모의 에이전트
- 모의 에이전트 판단 기록
- 페르소나별 모의 성과
- 판단 입력값: 커뮤니티 반응, 가격 snapshot, 신뢰도, 원문 확인
- 최근 판단 로그: 시간, 종목, 에이전트, 상태, 입력값, 판단 key
- 전략 버전과 판단 key 기준

## 상태와 빈 화면

- loading: 인간 지표 KPI와 에이전트 요약 skeleton을 함께 보여줍니다.
- empty: 판단 로그가 없으면 커뮤니티 입력값 수집 상태를 먼저 보여줍니다.
- error: 판단 생성 실패와 입력 데이터 실패를 분리합니다.
- stale/mock: mock, stale, 실거래 아님 상태를 상단 badge와 log row에 표시합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `agentPersonas` | agent | 모멘텀, 역발상, 리스크 회피, 커뮤니티 추종 등 |
| `agentPipeline` | agent/indicator/market | 판단 입력값, 신뢰도, 중복 판단 key, paper 후보 수 |
| `agentDecisionLogs` | agent/simulation | 관찰, 스킵, paper 후보, 스킵 사유 기록 |
| `agentDecisionLogs[].input` | agent/indicator/market | 커뮤니티 반응, 가격 snapshot, 신뢰도, 뉴스 이벤트 |
| `agentDecisionLogs[].key` | agent/backend | 중복 판단 방지 key |
| `strategyVersions` | agent | 전략 버전과 규칙 |

## 기획자 확인 필요

- `/agents` redirect를 유지할지, 배포 후 한두 버전 뒤 route를 완전히 제거할지.
- 판단 로그 상세를 drawer로 둘지 별도 상세 route로 둘지.
- 리더보드의 수익률 표현 범위와 경고 문구 수준.

## 변경 로그

- 2026-05-19: 독립 에이전트 탭을 인간 지표 하위 화면으로 흡수. `/agents`는 `/communities?view=agents` redirect로 유지.
