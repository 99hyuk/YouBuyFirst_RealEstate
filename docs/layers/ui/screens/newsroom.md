# 뉴스룸 화면

> Refactor needed: 부동산 뉴스/컬럼/커뮤니티 이슈룸으로 전환해야 합니다.

## Route

- Parent: root
- Route 후보: `/newsroom`
- Query: `feed=all|news|reports|videos|links`, `page`
- Child screens: 없음. 각 항목은 외부 원문 링크로 이동합니다.

## 화면 목적

대시보드에 일부만 보이는 부동산 속보, 정책·통계 리포트, 영상, 블로그·커뮤니티를 더 길게 모아봅니다. 특정 지역에 묶이지 않은 전국 이슈도 보여주되, 내용 복제 없이 제목, 출처, 시간, 간단한 지표만 보여주고 원문으로 보냅니다.

## 현재 섹션

- 뉴스룸 제목 카드: 영어 kicker나 `콘텐츠 반영` 같은 반복 상태 pill 없이 점 아이콘 옆에 `뉴스룸` 타이틀만 단일 행으로 표시
- 종합 화면: 뉴스, 리포트, 영상, 블로그·커뮤니티 4개 카드. 각 카드 헤더는 영어 kicker 없이 점 아이콘 옆 한글 제목으로 표시합니다. 영상과 블로그·커뮤니티도 순위가 아니라 최신 콘텐츠 목록으로 표시하며 번호를 붙이지 않음
- 특정 feed 화면: 15개 단위 리스트. 상세 feed 헤더도 `feed list` 같은 영어 라벨 없이 선택한 한글 feed명만 표시
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
| `items[].metricLabel` | community/indicator | 조회수, 추천수, 댓글수 등 보조 메타. 화면에서는 영상/블로그 순위 번호로 변환하지 않음 |
| `items[].statusLabel` | backend | `mock`, `stale`, `public-demo-only` 등 |
| `page`, `pageSize`, `totalCount` | backend/layers/ui | 페이지네이션 |

현재 구현:

- `feed=all` 종합 화면은 `news`, `report`, `video`, `link`를 각각 조회해 4개 카드가 뉴스 후보 쏠림에 밀리지 않게 합니다. 특정 feed 화면은 해당 feed만 조회합니다.
- `GET /api/realestate/targets/{targetId}/content?feed=&limit=` 응답을 지역/단지 상세의 관련 콘텐츠 카드 입력으로 사용합니다.
- `POST /internal/realestate/content-items`는 내부 수집/수동 등록용 upsert API입니다. `reviewState=approved` target link만 공개 target content와 timeline에 노출합니다.
- 콘텐츠 원문 전문은 저장하거나 화면에 복제하지 않고, 제목, 제한 snippet, URL, source/domain, 발행/수집 시각만 사용합니다.
- 프론트는 `front/src/lib/realestate-content.ts`에서 화면용 `reports/videos/links` query를 백엔드 content type `report/video/link`로 변환합니다.
- `/newsroom` 화면은 content API 응답이 있으면 live row를 표시합니다. API 요청이 성공했지만 응답이 비어 있으면 mock feed를 섞지 않고 `수집 전/insufficient` 빈 상태를 표시하며, API 실패는 `content API 오류`로 분리합니다.
- `feed=reports`는 공식/금융/연구기관 도메인에 있는 정책·통계·리서치 자료만 우선 표시합니다. 언론 기사 안에 "보고서", "KB부동산" 같은 단어가 있어도 출처 도메인이 보고서 정본이 아니면 뉴스로 분류합니다.
- `feed=videos`는 YouTube/youtu.be 직접 링크만 표시합니다. 검색 결과의 채용공고, 일반 기사, 외부 공유 래퍼는 영상 후보에서 제외합니다.
- `feed=links`는 블로그, 브런치, 티스토리, 카페처럼 원문 링크 성격이 확인되는 도메인을 표시합니다. 단순 검색어에 "블로그"가 들어간 일반 뉴스는 링크로 승격하지 않습니다.
- `feed=videos`, `feed=links`는 `1위`, `2위` 같은 순위 라벨 없이 출처 아이콘, 제목, 출처/시간/상태 메타만 보여줍니다.
- SerpApi 결과는 관심도 점수의 원천이 아니라 최근 이슈 후보입니다. 따라서 검색 잡음으로 확인되는 채용 페이지, 구인/구직 문서, 유튜브 공유 래퍼는 화면과 신규 적재 단계 모두에서 제외합니다.
- 지역 이슈 브리핑 MVP에서는 뉴스룸이 대시보드와 지역 상세의 근거 feed 역할을 한다. 지역 target이 연결된 콘텐츠는 상세 리포트로 보내고, target이 없지만 중요도가 높은 전국 이슈는 뉴스룸 종합 feed에 남긴다.

## 기획자 확인 필요

- 각 feed를 별도 route로 분리할지, 현재처럼 query로 유지할지.
- 리포트 원문 수집 범위와 저작권 표시 기준.

## 변경 로그

- 2026-06-12: 뉴스룸 프론트가 content API 어댑터를 통해 live/fallback feed를 선택하도록 연결.
- 2026-06-15: API 빈 응답과 실패 상태에서 mock feed를 표시하지 않고 수집 전/오류 빈 상태를 표시하도록 변경.
- 2026-06-15: 미사용 dashboard fixture 기반 fallback feed 생성 코드를 제거하고, 최근 이슈 후보/content API가 없는 경우에도 정적 기사 행을 만들지 않도록 보정.
- 2026-06-15: `/newsroom?feed=all`은 기존 4분할 카드 구조를 유지합니다. content API에 후보가 있지만 리포트/영상/커뮤니티 유형이 비어 있는 경우, 각 카드에는 수집 실패가 아니라 "이번 갱신에서는 해당 유형이 아직 분리되지 않았습니다"를 표시합니다.
- 2026-06-16: 리포트/영상/블로그 feed를 출처 도메인 기준으로 재분류하고, 채용공고/공유 래퍼 같은 SerpApi 검색 잡음을 제외하도록 기준화.
- 2026-06-17: SerpApi quota 소진 상황에서도 발표용 큐레이션 항목을 재주입할 수 있도록 수동 콘텐츠 payload를 두고, 종합 화면은 카테고리별 개별 fetch로 영상/블로그 카드가 뉴스 후보에 밀리지 않게 보정.
- 2026-06-22: 지역 이슈 브리핑 MVP 기준을 반영해 뉴스룸을 지역 상세와 대시보드의 근거 feed로 정의하고, 특정 지역이 없는 전국 이슈도 종합 feed에 남기는 기준을 추가.
- 2026-06-22: 뉴스룸 제목 카드의 `콘텐츠 반영/콘텐츠 확인 필요` 상태 pill을 제거하고, 데이터 상태는 카드별 빈 상태와 행 메타에서만 다룸.
- 2026-06-22: 뉴스룸 영상, 블로그·커뮤니티 feed에서 순위 번호를 제거하고 최신 콘텐츠 목록으로 표시.
- 2026-06-22: 뉴스룸 제목/종합 카드/상세 feed 헤더에서 영어 kicker를 제거하고, 기존 점 아이콘 옆에 한글 제목만 단일 행으로 표시.
- 2026-05-18: Screen Brief 신규 작성. 4분할 종합과 query 기반 feed 상세 구조를 기준화.
