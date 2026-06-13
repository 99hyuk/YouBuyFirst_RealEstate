# 관심 지역 화면

## Route

- Parent: root
- Route 정보: `/realestate/watchlist`
- Child screens: 관심 지역 추가 drawer, alias/source 설정 drawer 후보

## 화면 목적

사용자가 직접 추적하고 싶은 지역과 단지군을 모아 보는 화면입니다. 보유 자산이나 실거래 내역을 관리하는 화면이 아니라, 관심 지역의 지표 변화, 커뮤니티 반응, 알림 조건, 근거 링크를 관리합니다.

## 현재 섹션

- 관심 지역 summary: 등록 수, 알림 수, stale 데이터 수, 우려 증가 수
- 관심 지역 ledger: 지역/단지명, 주요 지표, 언급 변화, 최근 이슈, 상세 링크
- 알림 조건 panel: 거래량 급증, 전세가율 변화, 미분양 변화, 정책/교통 keyword
- source/alias DB 연결 panel: 별칭, 커뮤니티 source, 키워드 매핑 상태
- 관찰 로그: 최근 지표 변화, 커뮤니티 반응, 확인해야 할 링크

## 상태와 빈 화면

- loading: summary와 관심 지역 table skeleton을 보여줍니다.
- empty: 관심 지역이 없으면 지도와 지역/단지 순위 화면으로 이동할 수 있게 합니다.
- error: 관심 목록, 알림 조건, source/alias DB 실패를 분리합니다.
- stale/mock: 공공데이터 지연과 커뮤니티 수집 지연을 badge로 표시합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `watchSummary` | user/backend | 관심 지역 수, 알림 수, stale 수 |
| `watchTargets` | user/realestate | 관심 지역/단지 목록과 내부 target id |
| `alertRules` | user/indicator | 알림 조건과 threshold |
| `aliasMappings` | community/backend | 별칭, 단지명, 생활권 keyword 매핑 |
| `sourceMappings` | community/backend | 커뮤니티/source별 수집 상태 |
| `observationLogs` | indicator/community | 최근 관찰 로그와 근거 링크 |

## 기획 확인 필요

- 로그인 전 mock 관심 지역을 유지할지, 로그인 후 사용자별 저장으로만 둘지.
- 알림 조건을 로컬 mock으로 둘지, backend rule로 저장할지.
- 단지명 alias DB를 사용자가 직접 제보/수정할 수 있게 할지.

## 변경 로그

- 2026-06-12: 화면 정본 route를 `/realestate/watchlist`로 고정하고 레거시 호환 route를 제거.
- 2026-06-01: 기존 원장형 화면을 관심 지역 관리 화면으로 전환.
