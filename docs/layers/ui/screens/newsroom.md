# 뉴스룸 화면

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

## API 후보

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

## 기획자 확인 필요

- 영상/블로그/커뮤니티는 순위형 지표를 유지하고, 뉴스/리포트는 최신순만 쓸지.
- 각 feed를 별도 route로 분리할지, 현재처럼 query로 유지할지.
- 리포트 원문 수집 범위와 저작권 표시 기준.

## 변경 로그

- 2026-05-18: Screen Brief 신규 작성. 4분할 종합과 query 기반 feed 상세 구조를 기준화.
