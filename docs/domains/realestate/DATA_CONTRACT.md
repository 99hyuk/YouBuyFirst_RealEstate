# realestate data contract

이 문서는 부동산 프로젝트의 데이터 이름과 경계를 맞추는 기준입니다. 코드, DB, crawler, UI, agent가 모두 이 문서를 기준으로 같은 말을 쓰게 만드는 것이 목적입니다.

## 현재 확인한 공공데이터 후보

확인일: 2026-06-01

| 후보 | 공식 출처 | 활용 | 주의 |
| --- | --- | --- | --- |
| 국토교통부 아파트 매매 실거래가 자료 | https://www.data.go.kr/data/15126469/openapi.do | 아파트 매매 신고정보, 지역/기간별 실거래 market fact | 공공데이터포털에는 업데이트 주기가 `실시간`으로 표시되지만, 화면에서는 매일 공시 확정처럼 쓰지 않고 신고/공개 지연을 분리합니다. |
| 국토교통부 아파트 전월세 실거래가 자료 | https://www.data.go.kr/data/15126474/openapi.do | 전월세 실거래 market fact | 개인정보 보호로 동/호 정보는 제공되지 않습니다. 계약년월과 법정동 기준으로 조회합니다. |
| 국토교통부 건축HUB 건축물대장정보 서비스 | https://www.data.go.kr/data/15134735/openapi.do | 건물/단지 기본 속성 보강 | JSON/XML을 모두 제공하지만, 기존 건축데이터 PK 전환 규칙 확인이 필요합니다. |
| 한국부동산원 공동주택 실거래가격지수 | https://www.reb.or.kr/reb/cm/cntnts/cntntsView.do?cntntsId=1193&mi=10337 | 지역 단위 가격 흐름 참고 지표 | 개별 단지 사실값이 아니라 통계/지수입니다. 실거래 원장처럼 쓰지 않습니다. |

공공데이터는 `sourceUpdatedAt`, `asOf`, `observedAt`, `ingestedAt`, `stale`을 분리해서 저장합니다. `업데이트 주기=실시간`이라고 표시되어도 서비스 문구는 "원천 기준 최신", "확인 필요", "지연 가능"처럼 보수적으로 씁니다.

MOLIT 실거래/전월세 API 백필은 `LAWD_CD + DEAL_YMD + providerDataset` 단위로 import run을 나눕니다. API 호출은 `pageNo`/`numOfRows`를 사용해 반복 조회하며, 마지막 페이지의 결과 수가 `numOfRows`보다 적으면 해당 run 수집을 멈춥니다. 기본 `numOfRows`는 100, 기본 최대 페이지 수는 1000입니다. 실행자는 `--realestate-public-data-page-size`, `--realestate-public-data-max-pages` 또는 같은 이름의 환경변수 `REALESTATE_PUBLIC_DATA_PAGE_SIZE`, `REALESTATE_PUBLIC_DATA_MAX_PAGES`로 조절할 수 있습니다. 운영 재시도에서는 `--realestate-skip-completed-runs`로 계획된 runKey 목록을 backend에 직접 조회해 `status=completed` import run을 제외합니다. pipeline은 runKey를 100개 단위로 나눠 조회하므로 최근 목록 limit에 의존하지 않습니다.

실제 API 호출 전에는 `realestate-public-data-preflight`로 `DATA_GO_SERVICE_KEY` 준비 여부, backend target 사용 여부, 완료 run 제외 결과, 남은 run 수, page 설정, 승격 옵션을 먼저 확인합니다. 이 명령은 공공데이터 API를 호출하지 않고 secret 값을 출력하지 않습니다. 남은 run이 0개면 서비스키는 `not_required`로 처리할 수 있습니다.

대량 백필은 처음부터 전체 범위를 실행하지 않습니다. `--realestate-run-limit`으로 preflight, plan, raw-push에서 선택 run 수를 제한할 수 있으며, 첫 운영 검증은 `--realestate-run-limit 1`로 raw/staging/promote 관통을 확인한 뒤 범위를 늘립니다. limit으로 제외된 run 수는 `omittedByRunLimit`로 표시합니다.

대량 실행 전에는 `realestate-market-facts-backfill-plan --realestate-backfill-plan-output <path>`로 선택된 run 목록을 JSON manifest로 고정할 수 있습니다. 이후 `--realestate-backfill-plan-json <path>`를 preflight와 raw-push에 넘기면 사람이 다시 법정동/기간/dataset 옵션을 복사하지 않아도 같은 run 목록을 재사용합니다.

대량 manifest는 `--realestate-backfill-chunk-size <N>`으로 chunk 단위 실행 목록을 함께 출력할 수 있습니다. 출력의 `chunks[].items`는 같은 backfill task shape를 유지하므로, chunk manifest를 `--realestate-backfill-plan-json`에 다시 넣어도 pipeline은 run 목록을 평탄화해서 읽습니다. 운영에서는 전체 기간 manifest를 먼저 고정한 뒤 chunk별로 raw-push/preflight를 반복해 실패 지점을 좁힙니다.

법정동코드 CSV에서 지역 target을 import하기 전에는 `realestate-regions-inspect --legal-dong-code-csv <path> --realestate-backfill-plan-output <path>`로 `sido/sigungu/eupmyeondong` 수, 시군구 기준 MOLIT 수집대상, 실거래/전월세 run manifest를 먼저 검수합니다. 백엔드 import는 `sigungu`이고 5자리 `legalDongCode`가 있는 지역에만 `molit_apt_trade`, `molit_apt_rent` market-data-target을 생성하므로, inspect도 같은 기준을 따릅니다.

`realestate-market-facts-raw-push`는 선택 run 수가 `--realestate-large-run-threshold`를 넘으면 `--realestate-run-limit` 또는 `--realestate-confirm-large-run` 없이는 실행하지 않습니다. 기본 threshold는 50개이며, 이 가드는 공공데이터 provider를 만들기 전에 동작해야 합니다.

## 핵심 식별자

| 이름 | 의미 | 정본 후보 |
| --- | --- | --- |
| `regionId` | 서비스 내부 지역 id | 내부 UUID 또는 bigint |
| `legalDongCode` | 법정동 코드 | 행정표준코드 앞 5자리 또는 세부 코드 |
| `complexId` | 서비스 내부 단지 id | 내부 UUID 또는 bigint |
| `providerObjectId` | 외부 provider의 단지/건물 id | provider별 별도 테이블 |
| `targetType` | 분석 대상 종류 | `region`, `complex`, `living_area`, `policy_area` |
| `targetId` | `targetType`에 해당하는 내부 id | `regionId`, `complexId`, 생활권 id, 정책 영향권 id |

부동산 정본 식별자는 지역/단지/생활권 target 기준으로 관리합니다.

부동산은 한정된 단일 목록으로 끝나지 않습니다. region, complex, living area, policy area가 서로 계층/영향 관계를 가지므로 target graph를 별도로 둡니다.

`POST /internal/realestate/targets`는 region 외의 `complex`, `living_area`, `policy_area` 같은 공통 target을 먼저 만들기 위한 내부 upsert API입니다. 세부 region 정보는 `real_estate_regions`, 단지 상세는 이후 `real_estate_complexes` 같은 식별관계 테이블에 붙입니다.

## 모델 계약

### `real_estate_regions`

| 필드 | 타입 후보 | 기준 |
| --- | --- | --- |
| `id` | bigint/uuid | 내부 region id |
| `name` | string | 화면 표시명 |
| `type` | enum | `sido`, `sigungu`, `eupmyeondong`, `living_area` |
| `parentId` | id/null | 상위 지역 |
| `legalDongCode` | string/null | 법정동 코드 |
| `normalizedName` | string | 공백/기호/대소문자 정규화 이름 |
| `source` | string | 최초 생성 출처 |
| `reviewState` | enum | `candidate`, `approved`, `rejected`, `merged` |

### `real_estate_complexes`

| 필드 | 타입 후보 | 기준 |
| --- | --- | --- |
| `id` | bigint/uuid | 내부 complex id |
| `regionId` | id | 대표 지역 |
| `name` | string | 공식 또는 대표 단지명 |
| `normalizedName` | string | 매칭용 정규화 이름 |
| `address` | string/null | 도로명/지번 주소 후보 |
| `legalDongCode` | string/null | 법정동 코드 |
| `latitude` / `longitude` | decimal/null | 내장 지도 marker용 대표 좌표. 주소 정제 또는 provider geocoding 전에는 `null` |
| `coordinateProvider` | string/null | 좌표 출처. 예: `kakao_geocode`, `naver_geocode`, `manual`, `provider_csv` |
| `coordinateAsOf` | date/datetime/null | 좌표 기준 시각 |
| `coordinateStatus` | enum | `unknown`, `candidate`, `verified`, `stale`, `mock` |
| `builtYear` | number/null | 준공연도 |
| `householdCount` | number/null | 세대수 |
| `providerKeys` | json | provider별 외부 id 묶음 |
| `reviewState` | enum | `candidate`, `approved`, `rejected`, `merged` |

### `real_estate_target_edges`

| 필드 | 타입 후보 | 기준 |
| --- | --- | --- |
| `id` | bigint/uuid | edge id |
| `fromTargetType` / `fromTargetId` | enum/id | 상위 또는 영향 source target |
| `toTargetType` / `toTargetId` | enum/id | 하위 또는 영향 대상 target |
| `edgeType` | enum | `contains`, `nearby`, `same_living_area`, `policy_impacts`, `school_district`, `transport_area` |
| `confidence` | number | 0.0-1.0 |
| `source` | string | 공공데이터, 수동 등록, 정책 문서, 커뮤니티 후보 |
| `reviewState` | enum | `candidate`, `approved`, `rejected`, `ambiguous` |

이 edge는 단지 언급을 상위 지역 지표로 roll-up하거나, 지역/정책 이벤트를 영향권 단지로 drill-down하기 위한 기본 구조입니다.

구현된 백엔드 계약:

- `POST /internal/realestate/target-edges`는 `fromTargetId + toTargetId + edgeType` 기준으로 edge를 upsert합니다.
- `GET /api/realestate/targets/{targetId}/graph?direction=out|in|both&edgeType=`는 화면용 graph 조회이며 `approved` edge만 반환합니다.
- `GET /api/realestate/targets/{targetId}/reaction-graph?direction=out|in|both&edgeType=&windowStart=&windowMinutes=`는 graph edge와 연결 대상의 reaction snapshot을 함께 반환합니다.
- `GET /internal/realestate/target-edges?targetId=&direction=&edgeType=&reviewState=`는 운영/파이프라인 확인용 edge 목록입니다.
- 응답에는 `fromDisplayName`, `toDisplayName`, slug가 함께 들어가므로 UI가 별도 target 조회 없이 관계 리스트를 그릴 수 있습니다.
- target edge는 실제 FK로 `real_estate_targets` 양쪽을 참조합니다. 아직 상세 테이블이 없는 `living_area`, `policy_area`도 공통 target으로 먼저 만들고 edge에 연결할 수 있습니다.

pipeline roll-up 기준:

- `reviewState=approved`이고 `edgeType=contains`인 edge만 reaction snapshot roll-up에 사용합니다.
- 하위 지역/단지 관측치는 원본 target snapshot에 남기고, 상위 target 관측치를 파생으로 추가합니다.
- 다단계 `contains` 관계는 상위 방향으로 전파합니다. 예를 들어 `서울 -> 종로구 -> 사직동`이면 사직동 언급은 종로구와 서울 snapshot에 함께 반영됩니다.
- 파생 관측치의 `matchSource`는 `target_graph:contains`, `matchedText`는 `rollup:{원본 targetId}`로 남겨 직접 언급과 roll-up 언급을 구분합니다.
- 같은 게시글에서 상위 target이 이미 직접 언급된 경우 같은 상위 target의 파생 roll-up은 만들지 않습니다.
- 파생 관측치 confidence는 원본 관측치 confidence와 edge confidence를 곱해 낮춥니다.
- `nearby`, `same_living_area`, `policy_impacts`는 아직 자동 roll-up에 쓰지 않습니다. 이들은 상세 화면의 관련 대상, 정책 영향권, drill-down 후보로 별도 산식을 둡니다.

### `real_estate_aliases`

커뮤니티에서는 단지와 지역이 공식명으로만 불리지 않습니다. 크롤링과 matcher를 위해 별칭 DB는 1차 기능입니다.

| 필드 | 타입 후보 | 기준 |
| --- | --- | --- |
| `id` | bigint/uuid | alias id |
| `targetType` | enum | `region`, `complex`, `living_area`, `policy_area` |
| `targetId` | id | 내부 target id |
| `alias` | string | 원문 별칭 |
| `normalizedAlias` | string | 매칭용 정규화 별칭 |
| `aliasType` | enum | `official`, `short_name`, `nickname`, `typo`, `nearby_area`, `community_slang` |
| `source` | string | 공공데이터, 수동 등록, 커뮤니티 후보 등 |
| `evidenceUrl` | string/null | 별칭 근거 URL |
| `confidence` | number | 0.0-1.0 |
| `reviewState` | enum | `candidate`, `approved`, `rejected`, `ambiguous` |
| `ambiguous` | boolean | 동명이거나 일반명이라 자동 matcher 정본에 쓰면 위험한지 여부 |
| `createdBy` | string | `system`, `operator`, `import` |

별칭 매칭 규칙:

- 한 글자 alias는 기본적으로 금지합니다.
- 일반명, 브랜드명, 동명이 많은 alias는 `ambiguous`로 둡니다.
- 저장과 매칭 모두 공백과 기호를 제거하고 글자/숫자만 남긴 `normalizedAlias`를 사용합니다. 예를 들어 `종로 재건축`, `종로-재건축`은 같은 alias 후보로 upsert됩니다.
- matcher는 정규화된 alias로 찾되 `matchedText`에는 게시글 원문에서 실제 잡힌 문자열을 저장합니다.
- 제목과 snippet에서 모두 발견되거나 지역 문맥이 함께 있을 때 confidence를 올립니다.
- alias 후보는 자동 생성할 수 있지만, `approved` 전에는 ranking과 지표 정본에 섞지 않습니다.
- pipeline의 `realestate-alias-candidates` 명령은 승인된 alias가 게시글 제목에서 발견되고 바로 뒤 괄호에 `MRP` 같은 커뮤니티식 은어가 붙은 경우 `aliasType=community_slang`, `reviewState=candidate`, `source=community:auto-candidate:<source>` 후보를 만듭니다.
- pipeline의 `realestate-target-matches` 명령은 `reviewState=approved`이고 `ambiguous=false`인 alias만 정식 mention으로 내보냅니다.
- pipeline의 `realestate-alias-coverage` 명령은 source별 매칭률, 미매칭 예시, 많이 잡힌 target, 자동 후보 alias를 보여주는 운영 진단용 리포트입니다. 이 값 자체를 지역 관심도나 시장 지표로 쓰지 않습니다.
- `candidate`, `needs-review`, `rejected`, `ambiguous=true`, 한 글자 alias는 matcher 입력에 있어도 ranking이나 reaction snapshot 전 단계에 섞지 않습니다.
- 같은 게시글에서 제목과 snippet에 같은 target alias가 반복되면 제목 match를 우선합니다.

구현된 백엔드 계약:

- `POST /internal/realestate/aliases`와 `POST /internal/realestate/aliases/candidates`는 같은 upsert API입니다. `targetId + normalizedAlias`가 같으면 기존 alias를 갱신합니다.
- `GET /api/realestate/targets/{targetId}/aliases`는 화면/공개 조회용으로 `approved`이고 `ambiguous=false`인 별칭만 반환합니다.
- `GET /internal/realestate/aliases?reviewState=approved&ambiguous=false&targetType=region`은 pipeline matcher JSONL export 후보입니다.
- 한 글자 alias는 내부 저장 요청에서 건너뜁니다. 운영자 검수 UI가 붙기 전까지는 `candidate`를 ranking/snapshot 입력으로 쓰지 않습니다.

### `crawl_sources`

부동산은 일반 금융 커뮤니티보다 source가 분산되어 있으므로 처음부터 30개 내외 후보를 source registry로 관리합니다. adapter 구현보다 registry 검토가 먼저입니다.

| 필드 | 타입 후보 | 기준 |
| --- | --- | --- |
| `id` | string | `naver-cafe-foo`, `public-api-molit-apt-trade` 같은 안정 id |
| `displayName` | string | 운영자가 보는 이름 |
| `sourceType` | enum | `public_api`, `public_board`, `cafe`, `regional_cafe`, `app_community`, `news`, `blog`, `column`, `official_notice` |
| `sourceCategory` | enum | `national_investment`, `local_living`, `general_board`, `proptech_review`, `news_content`, `official_data` |
| `rootUrl` | string | source root |
| `accessMode` | enum | `public_http`, `rendered_public`, `login_required`, `blocked` |
| `status` | enum | `disabled`, `local-research-only`, `public-demo-only`, `enabled` |
| `robotsStatus` | enum | `unknown`, `allowed`, `restricted`, `blocked` |
| `termsStatus` | enum | `unknown`, `reviewed`, `restricted`, `blocked` |
| `targetScope` | enum | `general_market`, `region`, `complex`, `policy`, `news` |
| `geoScope` | enum | `national`, `sido`, `sigungu`, `eupmyeondong`, `complex`, `unknown` |
| `topicScope` | string[] | 전세, 매매, 청약, 재건축, 교통, 학군, 정책, 경매 등 source가 강한 주제 |
| `expectedVolume` | enum | `low`, `medium`, `high` |
| `parserStatus` | enum | `none`, `candidate`, `implemented`, `failing` |
| `coverageCaveat` | string/null | 로그인 필요, robots 제한, 앱 의존, 특정 지역 편중 같은 해석 주의점 |
| `rateLimitPolicy` | string | 요청 간격과 일일 한도 |
| `lastReviewedAt` | datetime/null | 정책 검토 시각 |

초기 source inventory 목표:

| 그룹 | 후보 수 | 상태 기준 |
| --- | --- | --- |
| 공공데이터 API | 5-8 | 공식 API부터 `local-research-only` 또는 `enabled` 후보 |
| 공개 부동산 커뮤니티/게시판 | 6-8 | robots/약관 확인 전 `disabled` |
| 네이버 카페 공개 게시판 | 8-12 | 로그인 필요 시 `disabled`, 공개 목록만 검토 |
| 다음 카페 공개 게시판 | 4-6 | 로그인 필요 시 `disabled`, 공개 목록만 검토 |
| 뉴스/컬럼/공식 공지 | 6-8 | 원문 전문 저장 금지, 링크/제목/snippet 중심 |

로그인 세션 크롤링, CAPTCHA 우회, 프록시 회전, fingerprint 위장은 source registry 상태와 무관하게 금지합니다.

### `community_posts`

| 필드 | 기준 |
| --- | --- |
| `sourceId` | `crawl_sources.id` |
| `boardId` | source 내부 게시판 id |
| `externalId` | 원천 게시글 id 또는 canonical URL hash |
| `url` | canonical URL |
| `title` | 제목 |
| `contentSnippet` | 제한 길이 본문 일부 |
| `publishedAt` | 작성 시각, 모르면 `null`과 `timeConfidence=unknown` |
| `authorHash` | 원문 작성자 대신 source별 salt/hash |
| `viewCount` | 없으면 `null` |
| `recommendCount` | 없으면 `null` |
| `commentCount` | 없으면 `null` |
| `contentHash` | 중복 감지 hash |

### `content_items`, `content_target_links`

`content_items`는 뉴스, 리포트, 영상, 블로그/커뮤니티 링크처럼 외부 원문으로 보내야 하는 콘텐츠 카드의 정본입니다. 원문 전문을 복제하지 않고 제목, 제한 snippet, URL, 발행/수집 시각, 상태 라벨만 저장합니다. `content_target_links`는 콘텐츠와 지역/단지 target의 다대다 연결입니다. `reviewState=approved`인 연결만 target 상세 content 목록과 timeline에 노출합니다.

SerpApi 같은 검색 API로 발견한 최근 이슈 후보도 공개 원문 링크 후보라면 `content_items` 또는 후속 `recent_issue_candidates` 계열로 관리합니다. 검색 결과 수, 검색 순위, 노출량은 관심도 지표나 반응 방향의 원천으로 쓰지 않습니다. 저장 범위는 제목, 출처, 날짜, 링크, 관련 키워드, 검색 provider/query, target 후보 confidence 정도로 제한합니다.

현재 MVP 구현은 별도 `recent_issue_candidates` 테이블을 만들기 전 단계로, SerpApi 후보를 `content_items`에 저장합니다. `sourceId=serpapi:google_news`, `metricLabel=query: ...`, `statusLabel=search_candidate`, `dataStatus=candidate`, `content_target_links.linkType=search_candidate`, `reviewState=candidate`를 사용합니다. 후보 링크는 운영자 검수로 `approved`가 되기 전까지 target timeline 정본으로 보지 않습니다.

`content_items` 필드:

| 필드 | 기준 |
| --- | --- |
| `id` | 내부 content id. 외부 id 또는 안정 key |
| `sourceId` | source registry id 또는 수동 입력 source |
| `contentType` | `news`, `report`, `video`, `link`, `column`, `official_notice` |
| `title` | 사용자에게 보일 제목 |
| `snippet` | 제한 요약. 원문 전문 저장 금지 |
| `url` | canonical URL. 중복 방지 기준 |
| `domain` | favicon/source 표시 후보 |
| `publishedAt` | 원천 발행 시각. 알 수 없으면 `null` |
| `metricLabel` | 조회수, 댓글수, 리포트 종류 등 카드 보조 지표 |
| `statusLabel` | `stale`, `public-demo-only`, `링크 확인` 같은 표시 라벨 |
| `ingestedAt` | 우리 시스템 저장 시각 |
| `dataStatus` | `ok`, `partial`, `unknown`, `stale`, `error`, `candidate` |

후속 검색 API metadata 후보:

| 필드 | 기준 |
| --- | --- |
| `searchProvider` | `serpapi`, `manual`, `naver_search` 등 |
| `searchQuery` | 이슈 후보를 찾는 데 사용한 query |
| `keywordTags` | 정책, 교통, 금리, 대출, 청약, 전세 같은 관련 키워드 |
| `searchObservedAt` | 검색 결과를 관측한 시각 |

`content_target_links` 필드:

| 필드 | 기준 |
| --- | --- |
| `contentItemId` | `content_items.id` |
| `targetId` | 연결 target |
| `linkType` | `mentioned`, `context`, `source_focus`, `search_candidate`, `excluded` |
| `confidence` | 0.0-1.0 |
| `reviewState` | `candidate`, `approved`, `rejected`, `ambiguous` |

### `real_estate_mentions`

| 필드 | 기준 |
| --- | --- |
| `postId` | community post id |
| `targetType` | `region`, `complex`, `living_area`, `policy_area` |
| `targetId` | 내부 target id |
| `matchedText` | 원문에서 발견된 표현 |
| `matchedAliasId` | alias id |
| `matchSource` | `title`, `snippet`, `comment_snippet` |
| `confidence` | 0.0-1.0 |
| `reviewState` | `auto`, `needs-review`, `approved`, `rejected` |

### `real_estate_market_facts`

| 필드 | 기준 |
| --- | --- |
| `targetType` / `targetId` | 지역 또는 단지 |
| `factType` | `apt_trade`, `apt_rent`, `listing_count`, `price_index`, `policy_event`, `supply_event`, `transport_event` |
| `provider` | `molit`, `reb`, `kapt`, `naver`, `manual` 등 |
| `providerDataset` | 원천 API/데이터셋 이름 |
| `providerObjectId` | 외부 id |
| `observedAt` | 원천에서 관찰한 이벤트 시각 |
| `asOf` | 원천 데이터 기준 시각 |
| `ingestedAt` | 우리 시스템 저장 시각 |
| `sourceUpdatedAt` | provider가 제공하면 저장 |
| `valueJson` | 가격, 거래량, 건수, 지수 등 값 |
| `dataStatus` | `ok`, `empty`, `stale`, `partial`, `mock`, `error`, `unknown` |
| `stale` | UI 경고 필요 여부 |

`observedAt`, `asOf`, `ingestedAt`은 서로 다릅니다. 예를 들어 실거래 계약일, 공공데이터 조회 기준월, 우리 시스템 수집 시각을 같은 값으로 덮어쓰지 않습니다.

### `policy_events`, `policy_event_targets`, `timeline_events`

`policy_events`는 정책, 공급, 교통, 뉴스/컬럼처럼 지역/단지 반응과 함께 볼 맥락 이벤트의 원천 정본입니다. `policy_event_targets`는 이벤트와 target의 다대다 영향 연결이며, `reviewState=approved`인 연결만 공개 timeline으로 materialize합니다. `real_estate_market_facts`, `real_estate_reaction_snapshots`, `content_items`도 target이 확인된 레코드는 상세 리포트 시간축에서 함께 볼 수 있도록 `timeline_events`에 각각 `market_fact`, `reaction`, `news/report/link` 이벤트로 materialize합니다.

`policy_events` 필드:

| 필드 | 기준 |
| --- | --- |
| `id` | event id |
| `eventType` | `policy`, `transport`, `supply`, `loan`, `subscription`, `education`, `redevelopment`, `news`, `column` |
| `title` | 사용자에게 보여줄 짧은 제목 |
| `summary` | 제한 요약 |
| `sourceUrl` | 원천 링크 |
| `publishedAt` | 원천 게시 시각 |
| `effectiveFrom` / `effectiveTo` | 시행 또는 영향 기간 |
| `targetScope` | `national`, `sido`, `sigungu`, `dong`, `living_area`, `complex` |
| `dataStatus` | `ok`, `partial`, `unknown`, `stale`, `error` |

`policy_event_targets` 필드:

| 필드 | 기준 |
| --- | --- |
| `policyEventId` | `policy_events.id` |
| `targetId` | 영향을 받는 target |
| `impactType` | `direct`, `context`, `watch`, `excluded` |
| `confidence` | 0.0-1.0 |
| `reviewState` | `candidate`, `approved`, `rejected`, `ambiguous` |

`timeline_events` 필드:

| 필드 | 기준 |
| --- | --- |
| `targetId` | 상세 화면의 기준 target |
| `eventType` | `policy`, `supply`, `transport`, `news`, `market_fact`, `reaction` 등 |
| `sourceRefType` / `sourceRefId` | `policy_event`, `market_fact`, `content`, `reaction_snapshot` 같은 원천 참조 |
| `title` / `summary` | 사용자에게 보일 제한 요약 |
| `occurredAt` | 화면 정렬 기준 시각 |
| `asOf` | 이벤트 기준 시각 |
| `dataStatus` | `ok`, `partial`, `unknown`, `stale`, `error` |

정책 이벤트는 원인 단정이 아니라 "함께 관찰된 맥락"으로 표시합니다. 지역 단위 상승/하락과 같은 market fact 변화에 붙일 수 있지만, 이벤트 하나를 가격 변화의 직접 원인처럼 쓰지 않습니다. market fact timeline은 실거래, 전월세, 매물 수, 가격지수 같은 관측값을 시간축에 얹는 용도이며, 원천 레코드는 `sourceRefType=market_fact`, `sourceRefId=real_estate_market_facts.id`로 추적합니다. reaction timeline은 언급량 변화, 기대/우려 우세, 주요 쟁점 변화를 시간축에 얹는 용도이며, 원천 레코드는 `sourceRefType=reaction_snapshot`, `sourceRefId=real_estate_reaction_snapshots.id`로 추적합니다. content timeline은 외부 뉴스/리포트/링크 근거를 시간축에 얹는 용도이며, 원천 레코드는 `sourceRefType=content`, `sourceRefId=content_items.id`로 추적합니다.

### `real_estate_reaction_snapshots`

| 필드 | 기준 |
| --- | --- |
| `targetType` / `targetId` | 지역 또는 단지 |
| `windowStart` / `windowEnd` | 집계 구간 |
| `mentionCount` | 언급 수 |
| `expectationScore` | 기대 반응 점수 |
| `concernScore` | 우려 반응 점수 |
| `neutralScore` | 중립/정보성 반응 점수 |
| `heatScore` | 화면 정렬과 급증 감지를 위한 0-100 열기 점수 |
| `sourceCount` | 참여 source 수 |
| `sourceSkew` | 특정 source 편중도 |
| `confidence` | 표본과 source 다양성 기반 신뢰도 |
| `coverageStatus` | `partial`, `low_sample`, `source_skewed`, `stale` |
| `stale` | UI 경고 필요 여부 |

pipeline 입력 관측치:

| 필드 | 기준 |
| --- | --- |
| `targetType` / `targetId` | 이미 matcher가 식별한 분석 대상 |
| `publishedAt` | 게시글 또는 댓글 관측 시각 |
| `source` | source registry id 또는 source:board 형태 |
| `reactionDirection` | `expectation`, `concern`, `neutral` |
| `issues` | `issueKey`, `label`, `direction`, `summary`, `confidence`를 가진 쟁점 후보 배열 |
| `externalId` | 원천 게시글 id. 추적용이며 집계 key는 아닙니다. |
| `matchedText` / `matchSource` | 어떤 별칭이 제목 또는 snippet에서 매칭됐는지 |
| `confidence` | 단일 관측치의 분류 신뢰도 |

초기 pipeline 명령:

- `realestate-aliases-fetch`: 백엔드의 승인된 비모호 alias registry를 matcher 입력 shape로 출력합니다.
- `realestate-target-edges-fetch`: 백엔드의 승인된 `contains` edge registry를 pipeline roll-up 입력 shape로 출력합니다.
- `realestate-reaction-observations`: 별칭 JSONL 또는 백엔드 alias export와 제한 게시글 JSONL을 읽어 지역/단지 매칭, 반응 방향, 쟁점 후보가 포함된 observation payload를 만듭니다.
- `realestate-reaction-snapshots`: 관측치 JSONL을 window snapshot JSON payload로 변환합니다.
- `realestate-reaction-snapshots-push`: 같은 payload를 `POST /internal/realestate/reaction-snapshots`로 전송합니다.
- `realestate-reaction-snapshots-from-posts`: 별칭 JSONL과 제한 게시글 JSONL에서 observation 생성과 snapshot 집계를 한 번에 수행합니다.
- `realestate-reaction-snapshots-from-posts-push`: 같은 흐름의 결과를 내부 snapshot API로 전송합니다.

`--realestate-target-edges-jsonl` 또는 `--realestate-use-backend-target-edges`를 함께 주면 snapshot 생성 전에 `contains` edge 기반 상위 target roll-up을 적용합니다.

`--reaction-stale-after-minutes`는 최신 관측치와 `asOf` 사이의 허용 지연 시간입니다. 기본값은 360분이며, 이 값을 넘기면 `coverageStatus=stale`, `stale=true`로 내려가고 confidence에 패널티가 들어갑니다.

이 명령들은 원문을 새로 크롤링하지 않습니다. 이미 수집된 제한 게시글 또는 제한 관측치만 읽어 indicator snapshot으로 집계합니다.

`serve` 모드 주기 refresh:

```bash
youbuyfirst-pipeline serve --enable-realestate-reaction-snapshots-refresh --realestate-aliases-jsonl aliases.jsonl --realestate-target-edges-jsonl target_edges.jsonl --community-posts-jsonl posts.jsonl --reaction-window-minutes 60 --reaction-stale-after-minutes 360 --realestate-reaction-snapshots-refresh-interval-minutes 30
```

주기 refresh는 실행 시각 기준 완료된 직전 window를 집계합니다. 예를 들어 01:02에 실행되고 `--reaction-window-minutes=60`이면 00:00-01:00 구간을 만들고, 01:00 이후 글은 다음 window로 넘깁니다.

### `real_estate_reaction_snapshot_issues`

| 필드 | 기준 |
| --- | --- |
| `snapshotId` | `real_estate_reaction_snapshots.id` |
| `issueKey` | `jeonse`, `school`, `policy`, `supply`, `transport` 같은 안정 key |
| `label` | 사용자에게 보여줄 쟁점명 |
| `share` | 해당 window 안에서 쟁점 비중 |
| `direction` | `expectation`, `concern`, `neutral` |
| `summary` | 짧은 근거 요약. 원문 전문을 저장하지 않습니다. |
| `confidence` | 쟁점 분류 신뢰도 |

### `evidence_logs`, `evidence_log_items`

`evidence_logs`는 지역/단지 평가가 어떤 입력을 보고 만들어졌는지 남기는 DB 정본입니다. Langfuse 같은 관측 도구는 LLM 호출 추적용이고, 서비스 화면과 검수에서 참조하는 판단 기록은 이 테이블을 기준으로 합니다.

`evidence_logs` 필드:

| 필드 | 기준 |
| --- | --- |
| `id` | `evidenceLogId`. 같은 평가 실행의 upsert key |
| `targetId` | 평가 대상 지역/단지/생활권 target |
| `snapshotId` | 대표 반응 snapshot id. 없으면 `null` |
| `evaluationVersion` | 평가 로직 버전. 예: `realestate-eval-v1` |
| `promptVersion` | 프롬프트 버전. 룰 기반 평가면 `null` 가능 |
| `modelName` | 사용 모델명. 룰 기반 평가면 `null` 가능 |
| `tone` | `watch`, `mixed`, `caution`, `info` 같은 사용자 표시 톤 |
| `summary` | 사용자에게 보여줄 관찰형 평가 요약 |
| `subtitle` | 보조 설명. 없으면 `null` |
| `caveats` | stale, partial, source skew, 검색 후보 미검수 같은 주의점 배열 |
| `dataQuality` | `ok`, `partial`, `low_sample`, `stale`, `skipped` |
| `confidence` | 0.0-1.0. 산출 불가하면 `null` |
| `skipReason` | 평가를 만들지 못했거나 제한한 이유. 없으면 `null` |
| `evaluatedAt` | 평가 실행 시각 |
| `asOf` | 평가 입력 데이터 기준 시각 |

`evidence_log_items` 필드:

| 필드 | 기준 |
| --- | --- |
| `id` | `evidenceItemId`. 같은 근거 조각의 upsert key |
| `evidenceLogId` | 부모 evidence log |
| `evidenceType` | `reaction`, `market_fact`, `timeline`, `content`, `search_candidate`, `similar_window` |
| `refType` | 참조 대상 종류. 예: `reaction_snapshot`, `market_fact`, `content`, `similar_window` |
| `refId` | 참조 대상 id 또는 외부 안정 key |
| `label` | 화면/검수에 보일 근거명 |
| `valueText` | `+38%`, `전세 우려 증가` 같은 짧은 값 |
| `severity` | `watch`, `caution`, `info`, `positive`, `negative` |

구현된 백엔드 계약:

- `POST /internal/realestate/evidence-logs`는 `logs[]`를 받아 `evidenceLogId` 기준으로 평가 로그와 근거 항목을 upsert합니다.
- `GET /api/realestate/targets/{targetId}/evidence-logs?limit=10`은 최신 평가 로그를 `evaluatedAt desc` 기준으로 반환합니다.
- API는 내부 추론 전문을 받지 않습니다. 반응 snapshot, market fact, timeline event, content, 검색 후보, 후속 유사 과거 결과의 참조 id와 요약만 저장합니다.
- `skipReason`이 빈 문자열이면 `null`로 저장해 "정상 평가"와 "건너뜀"을 구분합니다.

pipeline 유사 과거 후보:

- `realestate-similar-windows`는 reaction snapshot payload를 읽어 현재 window와 과거 window의 유사 후보를 출력합니다.
- 출력의 `items[].evidenceItem`은 EvidenceLog API의 `evidenceItems[]`에 그대로 넣을 수 있는 후보 shape입니다.
- `afterMarketSummary.items[]`는 matched window 이후 지정 horizon 안에서 같은 target의 market fact 첫 값/마지막 값과 `deltaPct`를 기록합니다.
- market fact가 부족하면 `caveat=market_fact_missing`으로 남기고, 유사도 후보 자체는 삭제하지 않습니다.
- 유사도는 분석 보조 근거이며 관심도 점수, 가격 예측, 행동 지시로 쓰지 않습니다.

pipeline EvidenceLog 조립:

- `realestate-evidence-logs`는 `--reaction-snapshots-jsonl`, `--evidence-target-id`, `--evidence-window-start`를 필수 입력으로 받습니다.
- 선택 입력인 `--evidence-market-facts-jsonl`, `--evidence-content-items-jsonl`, `--evidence-similar-windows-jsonl`을 함께 주면 각각 `market_fact`, `search_candidate`, `similar_window` evidence item으로 병합합니다.
- `realestate-evidence-logs-push`는 생성된 `logs[]`를 `POST /internal/realestate/evidence-logs`로 전송합니다.
- 현재 baseline은 룰 기반 요약이며, LLM provider가 붙어도 DB 저장 shape와 `evidenceItems[]` 참조 구조는 유지합니다.

## API 후보

```text
GET /api/realestate/targets/search?q=
GET /api/realestate/targets/{targetId}
GET /api/realestate/targets/{targetId}/aliases
GET /api/realestate/targets/{targetId}/graph?direction=&edgeType=
GET /api/realestate/targets/{targetId}/reaction-graph?direction=&edgeType=&windowStart=&windowMinutes=
GET /api/realestate/targets/{targetId}/reaction-snapshot?windowStart=&windowMinutes=
GET /api/realestate/targets/{targetId}/market-facts
GET /api/realestate/targets/{targetId}/nearby-complexes?limit=
GET /api/realestate/targets/{targetId}/content?feed=&limit=
GET /api/realestate/targets/{targetId}/evidence-logs?limit=
GET /api/realestate/targets/{targetId}/timeline?eventType=&limit=
GET /api/realestate/market-facts?legalDongCode=&factType=
GET /api/realestate/dashboard/market-summary?legalDongCode=
GET /api/realestate/map/layers?layerType=sido
GET /api/realestate/map/layers?layerType=sigungu&parentTargetId=
GET /api/realestate/newsroom?feed=&page=&pageSize=
GET /api/realestate/reactions/rankings?type=region&windowStart=&windowMinutes=
GET /api/realestate/reactions/rankings?type=complex&windowMinutes=
GET /internal/realestate/market-data-targets?enabled=true
GET /internal/realestate/aliases?reviewState=&ambiguous=&targetType=
GET /internal/realestate/target-edges?targetId=&direction=&edgeType=&reviewState=
GET /internal/realestate/public-data/import-runs?providerDataset=
POST /internal/realestate/targets
POST /internal/realestate/regions
GET /api/realestate/sources
POST /internal/realestate/aliases
POST /internal/realestate/aliases/candidates
POST /internal/realestate/target-edges
POST /internal/realestate/policy-events
POST /internal/realestate/content-items
POST /internal/realestate/evidence-logs
POST /internal/realestate/market-facts
POST /internal/realestate/public-data/raw-ingestions
POST /internal/realestate/public-data/promote-staging
POST /internal/realestate/reaction-snapshots
POST /internal/community/crawl-sources
```

`GET /api/realestate/dashboard/market-summary`는 원천 `real_estate_market_facts`를 대시보드 카드용으로 얇게 요약합니다. 현재는 최신 `apt_trade`, 최신 `apt_rent`를 우선 노출하며, 변동률이 확인되지 않은 값은 `changePct=null`로 둡니다.

`GET /api/realestate/map/layers`는 자체 도식화 지도 heat layer 입력입니다. `layerType=sido`는 전국 시도, `layerType=sigungu&parentTargetId=region-seoul`은 특정 시도 하위 시군구를 반환합니다. 응답은 `targets[].targetId`를 정본 식별자로 쓰고, 각 기간 값에 `provider`, `asOf`, `dataStatus`, `stale`, `changePct`, `sampleCount`, `confidence`를 포함합니다. 실제 데이터 집계 전 seed 값은 `dataStatus=mock`, `stale=true`로 표시합니다.

동/단지 상세의 내장 지도는 `GET /api/realestate/targets/{targetId}/nearby-complexes`를 우선 조회합니다. 응답은 `items[]`에 `targetId`, `name`, `address`, `region`, `latitude`, `longitude`, `tone`, `price`, `change`, `reaction`, `provider`, `asOf`, `dataStatus`, `stale`, `note`, `legalDongCode`, `coordinateProvider`, `coordinateStatus`를 포함합니다. API가 실패하거나 좌표가 없는 row만 내려오면 front fixture marker로 fallback하되, 좌표가 검증 전이면 값을 숨기지 않고 `dataStatus=mock|candidate|unknown`, `stale=true`로 표시합니다.

`GET /api/realestate/reactions/rankings`는 `real_estate_reaction_snapshots`를 지역/단지 랭킹 화면용으로 반환합니다. `windowStart`가 없으면 해당 target type의 최신 window를 반환하고, 없으면 빈 `items`와 `coverageStatus=empty`를 반환합니다.

`GET /api/realestate/targets/{targetId}/reaction-snapshot`는 지역/단지 상세와 지도 리포트 패널용 단일 snapshot 응답입니다. `windowStart`가 없으면 해당 target의 최신 window를 사용합니다.

`GET /api/realestate/targets/{targetId}/reaction-graph`는 상세 지도 drill-down과 관련 영향권 패널용 응답입니다. `graph` API의 승인된 edge를 기준으로 연결 대상을 찾고, 각 연결 대상에 `reaction-snapshot` 응답을 붙입니다. `windowStart`가 없으면 root target과 연결 대상 중 최신 window를 사용합니다. 예를 들어 서울 target에서 `direction=out&edgeType=contains`를 조회하면 종로구, 강남구 같은 하위 target edge와 각 구의 언급량, 기대/우려 비율, 쟁점 mix가 함께 내려갑니다.

`GET /api/realestate/targets/{targetId}/market-facts`는 지역/단지 상세 raw fact 입력입니다. 기존 `real_estate_market_facts.targetId` 기준으로 실거래, 전월세, 매물 수, 가격지수, 공급/정책 후보 fact를 내려주며 `factType`과 `limit`으로 좁힐 수 있습니다. 응답은 `GET /api/realestate/market-facts`와 같은 `items[]` shape를 씁니다.

`GET /api/realestate/targets/{targetId}/content`는 승인된 content-target link 기준으로 해당 지역/단지에 연결된 뉴스, 리포트, 영상, 링크를 반환합니다. `feed=all|news|report|video|link|column`으로 좁힐 수 있습니다.

`GET /api/realestate/newsroom`은 target과 무관하게 최신 content item을 feed별로 반환합니다. 외부 원문으로 보내기 위한 카드 입력이며, 원문 전문은 응답하지 않습니다.

`POST /internal/realestate/market-facts`는 공공데이터/수동 수집 market fact를 upsert합니다. 저장된 fact에 `targetId`가 있으면 같은 레코드를 `timeline_events`에 `eventType=market_fact`, `sourceRefType=market_fact`로 materialize합니다. `occurredAt`은 `observedAt`의 UTC 시작 시각, `asOf`는 fact의 기준일 UTC 시작 시각을 사용합니다.

`POST /internal/realestate/policy-events`는 정책/공급/교통/뉴스 이벤트와 target 영향 연결을 저장합니다. target link가 `reviewState=approved`이면 같은 이벤트를 `timeline_events`에 공개 화면용으로 materialize하고, `candidate`나 `rejected`는 저장만 하거나 기존 timeline 캐시를 제거합니다.

`POST /internal/realestate/content-items`는 뉴스/리포트/영상/링크 content item과 target link를 upsert합니다. target link가 `reviewState=approved`이면 `timeline_events`에 `sourceRefType=content`, `sourceRefId=content_items.id`로 materialize합니다. `occurredAt`은 `publishedAt`이 있으면 그 값, 없으면 `ingestedAt`을 사용하고, `asOf`는 `ingestedAt`을 사용합니다.

`POST /internal/realestate/reaction-snapshots`는 window 단위 커뮤니티 반응 snapshot을 upsert합니다. 저장된 snapshot은 `timeline_events`에 `eventType=reaction`, `sourceRefType=reaction_snapshot`으로 materialize합니다. `occurredAt`은 `windowEnd`, `asOf`는 snapshot의 `asOf`를 사용합니다.

`GET /api/realestate/targets/{targetId}/timeline`은 상세 리포트의 시간축 입력입니다. 현재는 승인된 policy event 계열, target이 확인된 market fact 계열, reaction snapshot 계열, 승인된 content link 계열 timeline을 반환합니다.

`GET /api/realestate/targets/{targetId}/evidence-logs`는 상세 리포트의 AI/에이전트 평가 입력입니다. 현재는 저장된 평가 로그와 근거 항목을 그대로 반환하며, 유사 과거 검색 결과는 후속 `similar_window` evidence item으로 연결할 예정입니다.

```json
{
  "targetId": "region-seoul-jongno",
  "targetType": "region",
  "displayName": "서울 종로구",
  "window": "60m",
  "windowStart": "2026-06-11T00:00:00Z",
  "windowEnd": "2026-06-11T01:00:00Z",
  "mentionCount": 128,
  "previousMentionCount": 88,
  "mentionDeltaPct": 45.5,
  "dominantDirection": "expectation",
  "reactionDirectionRatio": {
    "expectation": 0.57,
    "concern": 0.25,
    "neutral": 0.18
  },
  "heatScore": 82,
  "quality": {
    "confidence": 0.78,
    "sourceCount": 4,
    "sourceSkew": 0.42,
    "coverageStatus": "partial",
    "stale": false
  },
  "freshness": {
    "source": "real_estate_reaction_snapshots",
    "asOf": "2026-06-11T01:02:00Z",
    "staleCount": 0,
    "sourceCount": 4,
    "coverageStatus": "partial"
  },
  "issueMix": [
    {
      "issueKey": "jeonse",
      "label": "전세",
      "share": 0.41,
      "direction": "concern",
      "summary": "전세 매물과 가격 부담 언급이 같이 늘었습니다.",
      "confidence": 0.82
    }
  ]
}
```

pipeline 중간 명령:

```bash
youbuyfirst-pipeline realestate-target-matches --realestate-aliases-jsonl aliases.jsonl --community-posts-jsonl posts.jsonl
youbuyfirst-pipeline realestate-target-matches --realestate-use-backend-aliases --community-posts-jsonl posts.jsonl
youbuyfirst-pipeline realestate-aliases-fetch
youbuyfirst-pipeline realestate-alias-coverage --realestate-use-backend-aliases --community-posts-jsonl posts.jsonl
youbuyfirst-pipeline realestate-alias-candidates --realestate-aliases-jsonl aliases.jsonl --community-posts-jsonl posts.jsonl
youbuyfirst-pipeline realestate-alias-candidates-push --realestate-use-backend-aliases --community-posts-jsonl posts.jsonl
youbuyfirst-pipeline realestate-target-edges-fetch
youbuyfirst-pipeline realestate-reaction-observations --realestate-aliases-jsonl aliases.jsonl --community-posts-jsonl posts.jsonl
youbuyfirst-pipeline realestate-reaction-observations --realestate-use-backend-aliases --realestate-use-backend-target-edges --community-posts-jsonl posts.jsonl
youbuyfirst-pipeline realestate-reaction-snapshots --reaction-observations-jsonl observations.jsonl --reaction-window-start 2026-06-11T00:00:00Z --reaction-stale-after-minutes 360
youbuyfirst-pipeline realestate-reaction-snapshots-push --reaction-observations-jsonl observations.jsonl --reaction-window-start 2026-06-11T00:00:00Z
youbuyfirst-pipeline realestate-reaction-snapshots-from-posts --realestate-aliases-jsonl aliases.jsonl --realestate-target-edges-jsonl target_edges.jsonl --community-posts-jsonl posts.jsonl --reaction-window-start 2026-06-11T00:00:00Z
youbuyfirst-pipeline realestate-reaction-snapshots-from-posts-push --realestate-aliases-jsonl aliases.jsonl --realestate-target-edges-jsonl target_edges.jsonl --community-posts-jsonl posts.jsonl --reaction-window-start 2026-06-11T00:00:00Z
youbuyfirst-pipeline realestate-similar-windows --reaction-snapshots-jsonl snapshots.jsonl --similar-source-target-id region-daejeon --similar-source-window-start 2026-06-11T00:00:00Z --similar-market-facts-jsonl market_facts.jsonl
```

`realestate-target-matches`는 지역/단지 식별만 수행합니다. `realestate-reaction-observations`는 현재 룰 기반 1차 분류로 `reactionDirection`과 `issues`를 붙입니다. 이후 OpenAI provider가 붙더라도 같은 observation shape를 유지합니다.

## 남은 확인

- 공공데이터 API별 실제 응답 필드와 서비스키/트래픽 제한
- 매물 수와 호가성 listing 데이터를 어떤 provider에서 합법적으로 받을지
- 네이버 카페/다음 카페 중 공개 목록 접근이 가능한 source와 로그인 필요 source 구분
- alias 후보를 운영자가 검수하는 최소 UI 또는 admin workflow
- 30개 내외 source를 매번 전부 도는 대신 우선순위와 backoff를 적용하는 scheduler 정책
