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

## 핵심 식별자

| 이름 | 의미 | 정본 후보 |
| --- | --- | --- |
| `regionId` | 서비스 내부 지역 id | 내부 UUID 또는 bigint |
| `legalDongCode` | 법정동 코드 | 행정표준코드 앞 5자리 또는 세부 코드 |
| `complexId` | 서비스 내부 단지 id | 내부 UUID 또는 bigint |
| `providerObjectId` | 외부 provider의 단지/건물 id | provider별 별도 테이블 |
| `targetType` | 분석 대상 종류 | `region`, `complex`, `living_area`, `policy_area` |
| `targetId` | `targetType`에 해당하는 내부 id | `regionId`, `complexId`, 생활권 id, 정책 영향권 id |

주식 프로젝트의 `symbol`, `ticker`, `instrumentId`는 부동산 정본 식별자로 쓰지 않습니다.

부동산은 주식 종목처럼 한정된 목록으로 끝나지 않습니다. region, complex, living area, policy area가 서로 계층/영향 관계를 가지므로 target graph를 별도로 둡니다.

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
| `createdBy` | string | `system`, `operator`, `import` |

별칭 매칭 규칙:

- 한 글자 alias는 기본적으로 금지합니다.
- 일반명, 브랜드명, 동명이 많은 alias는 `ambiguous`로 둡니다.
- 제목과 snippet에서 모두 발견되거나 지역 문맥이 함께 있을 때 confidence를 올립니다.
- alias 후보는 자동 생성할 수 있지만, `approved` 전에는 ranking과 지표 정본에 섞지 않습니다.

### `crawl_sources`

부동산은 주식보다 source가 분산되어 있으므로 처음부터 30개 내외 후보를 source registry로 관리합니다. adapter 구현보다 registry 검토가 먼저입니다.

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

### `real_estate_policy_events`

| 필드 | 기준 |
| --- | --- |
| `id` | event id |
| `eventType` | `policy`, `transport`, `supply`, `loan`, `subscription`, `education`, `redevelopment` |
| `title` | 사용자에게 보여줄 짧은 제목 |
| `summary` | 제한 요약 |
| `sourceUrl` | 원천 링크 |
| `publishedAt` | 원천 게시 시각 |
| `effectiveFrom` / `effectiveTo` | 시행 또는 영향 기간 |
| `targetScope` | `national`, `sido`, `sigungu`, `dong`, `living_area`, `complex` |
| `targetEdges` | 영향을 받는 target edge 후보 |
| `dataStatus` | `ok`, `partial`, `unknown`, `stale`, `error` |

정책 이벤트는 원인 단정이 아니라 "함께 관찰된 맥락"으로 표시합니다. 지역 단위 상승/하락과 같은 market fact 변화에 붙일 수 있지만, 이벤트 하나를 가격 변화의 직접 원인처럼 쓰지 않습니다.

### `real_estate_reaction_snapshots`

| 필드 | 기준 |
| --- | --- |
| `targetType` / `targetId` | 지역 또는 단지 |
| `windowStart` / `windowEnd` | 집계 구간 |
| `mentionCount` | 언급 수 |
| `expectationScore` | 기대 반응 점수 |
| `concernScore` | 우려 반응 점수 |
| `neutralCount` | 중립/정보성 언급 수 |
| `issueMixJson` | 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책 등 |
| `sourceCount` | 참여 source 수 |
| `sourceSkew` | 특정 source 편중도 |
| `confidence` | 표본과 source 다양성 기반 신뢰도 |
| `coverageStatus` | `complete`, `partial`, `blocked`, `failed`, `skipped` |

## API 후보

```text
GET /api/realestate/targets/search?q=
GET /api/realestate/targets/{targetId}
GET /api/realestate/targets/{targetId}/aliases
GET /api/realestate/targets/{targetId}/reaction-snapshot?window=1d
GET /api/realestate/targets/{targetId}/market-facts
GET /api/realestate/sources
POST /internal/realestate/aliases/candidates
POST /internal/realestate/market-facts
POST /internal/community/crawl-sources
```

## 남은 확인

- 공공데이터 API별 실제 응답 필드와 서비스키/트래픽 제한
- 매물 수와 호가성 listing 데이터를 어떤 provider에서 합법적으로 받을지
- 네이버 카페/다음 카페 중 공개 목록 접근이 가능한 source와 로그인 필요 source 구분
- alias 후보를 운영자가 검수하는 최소 UI 또는 admin workflow
- 30개 내외 source를 매번 전부 도는 대신 우선순위와 backoff를 적용하는 scheduler 정책
