# 뉴스룸 화면

> Refactor needed: 부동산 뉴스/컬럼/커뮤니티 이슈룸으로 전환해야 합니다.

## Route

- Parent: root
- Route 후보: `/newsroom`
- Query: `feed=all|news|reports|videos|links`, `page`
- Child screens: 없음. 각 항목은 외부 원문 링크로 이동합니다.

## 화면 목적

대시보드에 일부만 보이는 뉴스, 리포트, 영상, 블로그/커뮤니티 링크를 더 길게 모아봅니다. 내용 복제 없이 제목, 출처, 시간, 간단한 지표만 보여주고 원문으로 보냅니다.

## 현재 섹션

- 뉴스룸 제목 카드
- 종합 화면: 뉴스, 리포트, 영상, 블로그/커뮤니티 4개 카드
- 특정 feed 화면: 15개 단위 리스트
- 페이지네이션: 이전, 번호, 다음
- 사이트 favicon 또는 source별 icon 표시

## 상태와 빈 화면

- loading: 제목 카드와 리스트 skeleton을 보여줍니다.
- empty: 선택한 feed에 항목이 없다고 표시하고 종합으로 돌아가는 링크를 둡니다.
- error: 외부 favicon 실패는 숨기고, feed 수집 실패는 카드별로 표시합니다.
- stale/mock: 각 row의 `statusLabel` 또는 상단 badge로 표시합니다.

## API

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `feed` | layers/ui/backend | `news`, `reports`, `videos`, `links` |
| `items[].title` | community/indicator | 제목 또는 영상/글 제목 |
| `items[].source`, `items[].domain` | community/indicator | 출처와 icon domain |
| `items[].url` | community/indicator | 외부 원문 링크 |
| `items[].publishedAt`, `items[].timeAgo` | community/indicator | 최신순 정렬 기준 |
| `items[].metricLabel` | community/indicator | 조회수, 추천수, 댓글수 등 순위 근거 |
| `items[].statusLabel` | backend | `mock`, `stale`, `public-demo-only` 등 |
| `page`, `pageSize`, `totalCount` | backend/layers/ui | 페이지네이션 |

현재 구현:

- `GET /api/realestate/newsroom?feed=all&page=1&pageSize=15` 응답을 뉴스룸 feed 리스트 입력으로 사용합니다.
- `GET /api/realestate/targets/{targetId}/content?feed=&limit=` 응답을 지역/단지 상세의 관련 콘텐츠 카드 입력으로 사용합니다.
- `POST /internal/realestate/content-items`는 내부 수집/수동 등록용 upsert API입니다. `reviewState=approved` target link만 공개 target content와 timeline에 노출합니다.
- 콘텐츠 원문 전문은 저장하거나 화면에 복제하지 않고, 제목, 제한 snippet, URL, source/domain, 발행/수집 시각만 사용합니다.
- 프론트는 `front/src/lib/realestate-content.ts`에서 화면용 `reports/videos/links` query를 백엔드 content type `report/video/link`로 변환합니다.
- `/newsroom` 화면은 content API 응답이 있으면 live row를 표시합니다. API 요청이 성공했지만 응답이 비어 있으면 mock feed를 섞지 않고 `수집 전/insufficient` 빈 상태를 표시하며, API 실패는 `content API 오류`로 분리합니다.

## 기획자 확인 필요

- 영상/블로그/커뮤니티는 순위형 지표를 유지하고, 뉴스/리포트는 최신순만 쓸지.
- 각 feed를 별도 route로 분리할지, 현재처럼 query로 유지할지.
- 리포트 원문 수집 범위와 저작권 표시 기준.

## 변경 로그

- 2026-06-12: 뉴스룸 프론트가 content API 어댑터를 통해 live/fallback feed를 선택하도록 연결.
- 2026-06-15: API 빈 응답과 실패 상태에서 mock feed를 표시하지 않고 수집 전/오류 빈 상태를 표시하도록 변경.
- 2026-05-18: Screen Brief 신규 작성. 4분할 종합과 query 기반 feed 상세 구조를 기준화.
