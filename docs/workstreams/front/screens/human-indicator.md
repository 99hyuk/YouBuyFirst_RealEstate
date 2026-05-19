# 인간 지표 화면

## Route

- Parent: root
- Route 후보: `/communities`
- Child screens: 커뮤니티 인기글 상세는 `stock-community-post` 후보와 공유 가능

## 화면 목적

커뮤니티별 언급 급증, 반응 비율, 수집 상태, 관심 테마, 성과 실험을 한 화면에서 비교합니다. 특정 커뮤니티가 맞춘다고 단정하지 않고 최근 반응 흐름을 관찰합니다.

## 현재 섹션

- 인간 지표 제목과 KPI
- 커뮤니티별 언급 급증과 반응 비율 matrix
- 커뮤니티별 언급 급증 종목
- 수집 상태: enabled, public-demo-only, local-research-only, disabled 후보
- 커뮤니티별 관심 테마
- 인기글/개념글 레이어
- 커뮤니티별 성과 실험: 추종/역추종, 적중률, 최대 낙폭
- 하위 탭: 커뮤니티 반응, 성과 실험, 모의 에이전트
- 모의 에이전트 판단 기록: 커뮤니티 반응 기반 페르소나 성과, 판단 입력값, 최근 판단 로그, 판단 key

## 상태와 빈 화면

- loading: KPI와 matrix skeleton을 보여줍니다.
- empty: 수집 가능한 커뮤니티가 없으면 소스 상태를 먼저 보여줍니다.
- error: 커뮤니티별 실패/skip 사유를 row 단위로 표시합니다.
- stale/mock: source state와 마지막 수집 시각에 표시합니다.

## API 후보

| 필드 | 소유 트랙 | 설명 |
| --- | --- | --- |
| `communities` | crawl/data | 커뮤니티 목록과 반응 비율 |
| `humanStats` | data | 화면 상단 KPI |
| `surgeStocks` | data | 커뮤니티별 언급 급증 종목 |
| `sourceStates` | crawl/backend | enabled, disabled, skip 사유, 마지막 수집 |
| `themeRows` | data | 커뮤니티별 관심 테마 |
| `topPosts` | crawl/data | 내부 상위 N% 인기글 |
| `experiments` | agent/data | 추종/역추종 성과 실험 |
| `agentPersonas` | agent | 인간 지표를 해석하는 모의 에이전트 페르소나 |
| `agentPipeline` | agent/data/market | 판단 입력값, 신뢰도, 중복 판단 key, paper 후보 수 |
| `agentDecisionLogs` | agent/trade | 관찰, 스킵, paper 후보, 스킵 사유 기록 |
| `strategyVersions` | agent | 전략 버전과 판단 key 규칙 |

## 기획자 확인 필요

- `커뮤니티별 성과` 표현을 어떻게 제한해서 투자 자문처럼 보이지 않게 할지.
- 인기글 원문 snippet 범위와 저작권/출처 표시 기준.
- 수집 불가 커뮤니티를 화면에 노출할지, 내부 admin으로만 둘지.
- `/agents` redirect를 언제까지 유지할지.

## 변경 로그

- 2026-05-19: 에이전트 화면을 인간 지표 하위 탭과 모의 판단 섹션으로 흡수.
- 2026-05-18: Screen Brief 신규 작성. `커뮤니티` 탭을 `인간 지표` 화면 기준으로 정리.
