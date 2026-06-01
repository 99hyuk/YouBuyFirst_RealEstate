# 반응 지표 화면

## Route

- Parent: root
- Route 정보: `/communities?view=`
- 연결 route:
  - 표준 화면: `/realestate/reactions?view=signals`
  - 지역/단지 상세: `/realestate/targets/:symbol`
  - `/agents`: 현재는 `/realestate/reactions?view=agents`로 redirect

> 이 brief는 기존 `/communities` URL의 호환 설명입니다. 새 반응 지표 UI는 `region-reactions.md`의 지역 반응 화면에 통합되었습니다.

## 화면 목적

부동산 커뮤니티 반응을 긴 글 목록이 아니라 관찰 지표로 압축합니다. 사용자는 어떤 지역의 언급량이 갑자기 늘었는지, 어떤 지역은 우려가 늘었는지, 어떤 이유로 반응이 커졌는지 빠르게 확인합니다.

## 현재 섹션

- 상단 summary: 전체 언급량, 기대/우려/중립 비율, 수집 시점
- 핵심 타일: 지금 뜨는 지역, 우려 증가 지역, 언급 많은 지역, 라이징 단지군
- 각 신호: 지역/단지명, 대표 수치, 반응 일관성, 신뢰도, 이유 keyword
- 근거 로그: 수집된 source, keyword, alias match, 중복 제거 상태

## 상태와 빈 화면

- loading: summary와 signal tile skeleton을 보여줍니다.
- empty: 수집된 반응이 없으면 수집 대상/키워드 설정을 안내합니다.
- error: 커뮤니티별 수집 실패와 파싱 실패를 분리합니다.
- stale/mock: 수집 시점, 공개 가능한 원문 링크 여부, mock 여부를 표시합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `reactionSummary` | indicator/community | 전체 언급량과 기대/우려/중립 비율 |
| `signalTiles` | indicator/community | 지금 뜨는 지역, 우려 증가 지역 등 핵심 타일 |
| `evidenceRows` | backend/community | 원문 링크, alias match, keyword, 중복 제거 상태 |
| `agentLogs` | agent/backend | 에이전트 판단 근거와 상태 |

## 기획 확인 필요

- 커뮤니티 출처 30개 후보의 우선순위와 접근 가능성.
- 별칭 DB에서 지역명과 단지명이 충돌할 때 우선순위.
- 원문 링크를 어디까지 공개하고, 유료/로그인 콘텐츠는 어떻게 처리할지.

## 변경 로그

- 2026-06-01: 사람 지표/성과 비교 성격을 부동산 커뮤니티 반응 지표 화면으로 전환.
- 2026-06-01: `/communities`를 `/realestate/reactions?view=`로 redirect하는 legacy URL로 전환.
- 2026-06-01: 지역 반응 화면에서 ranking table과 중복되던 커뮤니티별 반응 비율 표를 제거.
