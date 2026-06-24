# 뉴스룸 화면

> Refactor needed: 부동산 뉴스/컬럼/커뮤니티 이슈룸으로 전환해야 합니다.

## Route

- Parent: root
- Route 후보: `/newsroom`
- Query: `feed=all|news|reports|videos|links`, `page`
- Child screens: 없음. 각 항목은 외부 원문 링크로 이동합니다.

## 화면 목적

대시보드에 일부만 보이는 부동산 속보, 정책·통계 리포트, 영상, 블로그·커뮤니티를 더 길게 모아봅니다. 뉴스룸 자체는 지역/단지 상세 화면이 아니라 전역 콘텐츠 feed입니다. 내용 복제 없이 제목, 출처, 시간, 간단한 지표만 보여주고 원문으로 보냅니다.

## 현재 섹션

- 뉴스룸 상단 제목 박스: 다른 주요 화면의 page hero와 같은 `label + H2 + 짧은 설명` 형식으로 표시하되, 뉴스/콘텐츠 feed에 맞는 살구·로즈 계열 색을 사용합니다. 영어 kicker나 `콘텐츠 반영` 같은 반복 상태 pill은 넣지 않습니다.
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
- `/newsroom`은 `GET /api/realestate/newsroom?feed=&page=&pageSize=`만 읽는 전역 feed입니다. 지역/단지 매칭은 이 화면의 기본 요구가 아닙니다.
- `POST /internal/realestate/content-items`는 내부 수집/수동 등록용 upsert API입니다. 뉴스룸 전역 콘텐츠는 `targets: []`로 저장할 수 있습니다.
- `GET /api/realestate/targets/{targetId}/content?feed=&limit=` 응답은 지역/단지 상세의 관련 콘텐츠 카드 입력으로만 사용합니다. `reviewState=approved` target link만 공개 target content와 timeline에 노출합니다.
- `newsroomContentRefreshJob`은 RSS/XML 같은 비정형/반정형 source에서 제목, 제한 snippet, URL, 발행시각, domain만 추출해 `content_items`에 upsert합니다. 원문 전문은 저장하지 않습니다.
- `GET /api/realestate/batch-updates/stream`은 배치 완료 push 채널입니다. `newsroomContentRefreshJob`이 저장을 끝내면 `realestate-batch-update` 이벤트의 `topic=newsroom`을 발행하고, 프론트는 이벤트 본문을 화면 데이터로 쓰지 않고 `/api/realestate/newsroom`을 다시 조회합니다.
- 콘텐츠 원문 전문은 저장하거나 화면에 복제하지 않고, 제목, 제한 snippet, URL, source/domain, 발행/수집 시각만 사용합니다.
- 프론트는 `front/src/lib/realestate-content.ts`에서 화면용 `reports/videos/links` query를 백엔드 content type `report/video/link`로 변환합니다.
- `/newsroom` 화면은 content API 응답이 있으면 live row를 표시합니다. API 요청이 성공했지만 응답이 비어 있으면 mock feed를 섞지 않고 `수집 전/insufficient` 빈 상태를 표시하며, API 실패는 `content API 오류`로 분리합니다.
- `feed=reports`는 KB금융/KB Think, 하나금융연구소, 우리금융경영연구소, 주택금융연구원/HF, 한국금융연구원/KIF, 건설산업연구원, 국토연구원/K-REMAP, 한국은행, HUG, 한국부동산원처럼 금융·연구·공공기관 도메인에 있는 정책·통계·리서치 자료만 우선 표시합니다. 언론 기사 안에 "보고서", "KB부동산" 같은 단어가 있어도 출처 도메인이 보고서 정본이 아니면 뉴스로 분류합니다. 배치는 기관군별 RSS 검색 source를 나눠 한 기관 결과가 전체 리포트 쿼터를 독점하지 않게 합니다.
- `feed=videos`는 집코노미, 매부리TV, 부읽남TV, 삼프로TV, 스마트튜브, 김작가TV처럼 부동산 분석·토론·인터뷰 맥락이 있는 YouTube 채널 RSS만 수집합니다. Shorts URL은 제외하고, 공개 상세 페이지 또는 YouTube Atom의 `media:description`/`media:statistics`에서 영상 길이 600초 이상 또는 조회수 10,000회 이상 근거가 확인되는 항목만 `부동산 영상`으로 표시합니다. 제목/요약에 주제어가 부족해도 공개 YouTube 상세 메타의 `keywords`나 RSS 설명/해시태그가 부동산 주제와 맞으면 통과 후보로 볼 수 있습니다.
- `feed=links`는 단순 검색 결과가 아니라 컬럼형 원문 출처를 우선합니다. 배치 기준은 KB Think 부동산 컬럼, 빠숑 네이버 블로그 RSS, 빌딩의 정석 네이버 RSS, Tistory 시장분석 RSS처럼 공개 RSS/XML로 확인되는 출처를 두고, 주식·강의·모집공고·매물·경매물건·홍보·액션형 추천 문구 같은 잡음은 제외합니다.
- `feed=videos`, `feed=links`는 `1위`, `2위` 같은 순위 라벨 없이 출처 아이콘, 제목, 출처/시간/상태 메타만 보여줍니다.
- SerpApi 결과는 관심도 점수의 원천이 아니라 최근 이슈 후보입니다. 따라서 검색 잡음으로 확인되는 채용 페이지, 구인/구직 문서, 유튜브 공유 래퍼는 화면과 신규 적재 단계 모두에서 제외합니다.
- 뉴스룸 row의 favicon/source icon은 `items[].domain`을 기준으로 렌더링합니다. 배치가 source별 실제 article URL domain을 보존해야 관련 사이트 아이콘이 표시됩니다.

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
- 2026-06-23: 뉴스룸을 지역/단지와 무관한 전역 콘텐츠 feed로 정리하고, `newsroomContentRefreshJob`이 target link 없이 `content_items`를 채우는 기준을 추가.
- 2026-06-23: 배치 완료 후 `/api/realestate/batch-updates/stream` SSE 이벤트를 받아 현재 뉴스룸 feed를 재조회하는 push 갱신 기준을 추가.
- 2026-06-23: 뉴스룸 4종 feed(`news`, `report`, `video`, `link`)를 모두 `newsroomContentRefreshJob` 2시간 배치로 연결하고, 영상은 Shorts/짧은 영상/저조회수 컷, 리포트는 허용 기관 도메인 컷, 블로그·커뮤니티는 컬럼형 출처와 제외어 기준을 통과한 글만 적재하도록 기준화.
- 2026-06-23: 리포트 source를 기관군별로 분리해 KB 쏠림을 줄이고, 블로그·커뮤니티 feed에 공개 RSS 기반 개인 컬럼 출처를 추가. YouTube 영상은 공개 상세 메타의 키워드와 Atom RSS 설명/조회수도 부동산 주제 및 긴 영상 근거로 인정하도록 기준을 확장.
- 2026-06-24: 뉴스룸 상단 제목을 다른 주요 화면과 같은 page hero 형식으로 맞추고, 뉴스룸 전용 살구·로즈 계열 색을 적용.
- 2026-05-18: Screen Brief 신규 작성. 4분할 종합과 query 기반 feed 상세 구조를 기준화.
