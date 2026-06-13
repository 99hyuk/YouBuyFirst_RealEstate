# 지역 반응 화면

## Route

- Parent: root
- Route 정보: `/realestate/reactions?view=`
- Child screens:
  - `region-detail`: `/realestate/targets/:targetId`

> `/communities`와 `/agents` 호환 route는 제거되었습니다. 지역 반응과 모의 에이전트 근거 로그는 `/realestate/reactions` 화면을 기준으로 둡니다.

## 화면 목적

커뮤니티, 뉴스, 블로그, 공공데이터에서 언급이 늘어난 지역과 단지군을 빠르게 비교합니다. 사용자는 같은 화면에서 순위, 급증 신호, 모의 에이전트 근거 로그를 전환하고, 관심 지역을 눌러 상세 리포트로 들어갑니다.

## 현재 섹션

- 상단 hero: 지역 반응 제목, 종합/순위/반응/근거 로그 탭, 관찰 기준 안내
- 핵심 신호 strip: 언급 증가, 우려 증가, 정책 민감, 데이터 stale
- 필터 strip: 지역, 단지군, 정책, 교통, 전세, 공급 키워드
- 지역 언급량 TOP 6: 순위, 지역, 언급량, 반응 방향, 핵심 이슈
- 단지군 관심 TOP 6: 순위, 단지군, 언급량, 반응 방향, 핵심 이슈
- 보조 console: 급증 테마, 데이터 기준, 수집 출처 후보
- 커뮤니티별 언급 급증 지역: 출처별로 뜨는 지역과 이유. 출처별 반응 비율 표는 ranking table과 중복되므로 표시하지 않습니다.
- 모의 에이전트 판단 기록: 판단 입력값, 전략 버전, 판단 key

## 상태와 빈 화면

- loading: 검색 필터와 ranking table skeleton을 먼저 보여줍니다.
- empty: 필터 조건에 맞는 지역/단지가 없다고 표시하고 필터 초기화를 제공합니다.
- error: community, news, public-data 실패를 별도 badge로 분리합니다.
- stale/mock: 공개 지표와 커뮤니티 수집 시점이 다를 수 있음을 표시합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `rankingGroups[].id` | layers/ui/backend | `regions`, `complexes` 같은 ranking 그룹 |
| `rankingGroups[].rows[].rank` | indicator/community | 현재 순위 |
| `rankingGroups[].rows[].targetId` | realestate/backend | 내부 target id 또는 화면 slug. 예: `SEOUL-MAPO` |
| `rankingGroups[].rows[].name` | realestate/backend | 지역/단지 표시명 |
| `rankingGroups[].rows[].market` | realestate/backend | 시도, 시군구, 생활권, 단지군 |
| `rankingGroups[].rows[].mentions` | indicator/community | 기간 내 언급량 |
| `rankingGroups[].rows[].mentionDelta` | indicator/community | 이전 기간 대비 언급 변화 |
| `rankingGroups[].rows[].positive`, `negative` | indicator/community | 기대/우려 반응 비율 |
| `rankingGroups[].rows[].event` | backend/content | 반응을 움직인 정책·교통·공급·전세 이벤트 |
| `filters` | layers/ui/backend | 지역/단지/이슈 필터 후보 |
| `hotThemes` | indicator/community | 급증 테마와 연결 target 수 |
| `signalTiles` | indicator/community | 지금 뜨는 지역, 우려 증가 지역 등 핵심 타일 |
| `agentLogs` | agent/backend | 에이전트 판단 근거와 상태 |

현재 구현:

- `GET /api/realestate/reactions/rankings?type=region&windowMinutes=60` 응답을 지역 언급량 랭킹에 우선 표시합니다.
- `type=complex` 응답도 같은 adapter로 받을 수 있으며, API가 비어 있거나 실패하면 기존 fixture 행을 fallback으로 둡니다.
- 응답의 `reactionDirectionRatio.expectation/concern`, `issueMix`, `confidence`, `sourceCount`, `stale`을 화면 행의 기대/우려 비율, 쟁점, 신뢰도/지연 문구로 변환합니다.
- 가격 변화가 확인되지 않은 API 행은 가격 상승률처럼 보정하지 않고 `시장 데이터 대기`, `관찰`로 표시합니다.

## 기획 확인 필요

- 별칭 DB는 시군구, 생활권, 역세권, 단지명, 커뮤니티 은어를 어느 수준까지 포함할지.
- 네이버 카페/다음 카페 등 로그인·권한이 필요한 커뮤니티 수집 범위.
- 순위 기준을 언급량, 언급 증가율, 우려 증가, 기대 증가 중 무엇으로 기본 정렬할지.

## 변경 로그

- 2026-06-01: 기존 ranking 화면을 지역·단지 반응 ranking 화면으로 전환.
- 2026-06-13: `/communities`, `/agents` 호환 route와 별도 legacy Screen Brief를 제거하고 `/realestate/reactions`를 단일 정본으로 고정.
- 2026-06-12: 레거시 반응 route를 제거하고 `/realestate/reactions` 표준 화면만 active route로 유지.
- 2026-06-01: ranking table과 중복되던 커뮤니티별 반응 비율 표와 반응/공식지표 비교 그래프를 제거.
- 2026-06-11: 지역/단지 랭킹 테이블을 `GET /api/realestate/reactions/rankings` 우선 표시와 fixture fallback 구조로 연결.
- 2026-06-12: 랭킹 행과 상세 링크의 식별자를 부동산 `targetId` 기준으로 정리.
