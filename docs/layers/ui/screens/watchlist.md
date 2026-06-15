# 관심 지역 화면

## Route

- Parent: root
- Route 정보: `/realestate/watchlist`
- Child screens: 관심 지역 추가 drawer, alias/source 설정 drawer 후보

## 화면 목적

사용자가 직접 추적하고 싶은 지역과 단지군을 모아 보는 화면입니다. 보유 자산이나 실거래 내역을 관리하는 화면이 아니라, 관심 지역의 지표 변화, 커뮤니티 반응, 알림 조건, 근거 링크를 관리합니다.

현재 로그인/사용자 저장 API가 열리기 전까지는 저장된 watchlist처럼 보이는 mock 목록을 두지 않고, `GET /api/realestate/reactions/rankings?type=region&windowMinutes=1440&limit=10`의 지역 반응 TOP10을 `관심 후보`로 표시합니다. API가 비거나 실패하면 `수집 전/insufficient` 또는 오류 상태를 보여줍니다.

## 현재 섹션

- 관심 후보 summary: 반응 TOP10 수, 급증 신호, 우려 우세, stale, 출처 합계, 쟁점 종류
- 관심 후보 ledger: 지역/단지명, 언급 변화, 쟁점, 기대/우려 비율, 상세 링크
- 알림 후보 panel: 언급 급증, 우려 우세, stale 상태를 사용자 저장 전 후보로 표시
- source/alias DB 연결 panel: 별칭, 커뮤니티 source, 키워드 매핑 준비 상태
- 관찰 로그: 최근 반응 snapshot 변화, source coverage, 확인해야 할 링크

## 상태와 빈 화면

- loading: summary와 관심 지역 table skeleton을 보여줍니다.
- empty: 관심 후보가 없으면 지도와 지역/단지 순위 화면으로 이동할 수 있게 하고, `수집 전/insufficient`를 표시합니다.
- error: 관심 목록, 알림 조건, source/alias DB 실패를 분리합니다.
- stale/mock: provider가 명시적으로 `mock` 또는 `stale`을 내려줄 때만 배지로 표시하고, 데이터가 없으면 `수집 전/insufficient`로 분리합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `reactionRanking` | indicator/backend | 저장 기능 전 관심 후보 TOP10, 기대/우려, mention delta, coverage |
| `watchSummary` | user/backend | 로그인 후 관심 지역 수, 알림 수, stale 수 |
| `watchTargets` | user/realestate | 로그인 후 관심 지역/단지 목록과 내부 target id |
| `alertRules` | user/indicator | 알림 조건과 threshold |
| `aliasMappings` | community/backend | 별칭, 단지명, 생활권 keyword 매핑 |
| `sourceMappings` | community/backend | 커뮤니티/source별 수집 상태 |
| `observationLogs` | indicator/community | 최근 관찰 로그와 근거 링크 |

## 기획 확인 필요

- 로그인 후 사용자별 저장 API를 어떤 시점에 열지.
- 알림 조건을 backend rule로 저장할 시점과 사용자별 권한 범위.
- 단지명 alias DB를 사용자가 직접 제보/수정할 수 있게 할지.

## 변경 로그

- 2026-06-15: 로그인/저장 전 mock watchlist를 제거하고 region reaction ranking 기반 관심 후보와 빈 상태로 전환.
- 2026-06-12: 화면 정본 route를 `/realestate/watchlist`로 고정하고 레거시 호환 route를 제거.
- 2026-06-01: 기존 원장형 화면을 관심 지역 관리 화면으로 전환.
