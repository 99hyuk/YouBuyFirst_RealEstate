# community collection

## 역할

커뮤니티 글을 안정적으로 수집하고, 어떤 소스를 어떤 조건에서 수집할지 관리합니다. 이 문서는 `community` 도메인 안에서 수집 입력과 source policy를 담당하며, 반응 방향 산식 자체는 `REACTION_GUIDE.md`와 `indicator` 도메인으로 분리합니다.

## 담당 범위

- 부동산 커뮤니티/게시판 adapter 후보
- 뉴스/컬럼 링크 source 후보
- 지역/단지별 게시판 또는 댓글 영역 adapter 후보
- 일반 게시판형/대상 게시판형 수집 전략
- 인기글/댓글/조회수 상위글 수집 전략
- `CrawlTarget` 우선순위 큐
- source/board registry: `source`, `boardId`, `displayName`, `targetScope`, `crawlPolicy`
- source run 상태, 실패 사유, backoff
- robots.txt, 약관, 차단 상태 기록
- 제한 원문 저장 정책

## 파일 소유권

주로 담당:

- `pipeline/src/youbuyfirst_pipeline/crawlers/`
- `pipeline/src/youbuyfirst_pipeline/scheduler.py`
- `pipeline/tests/fixtures/`
- crawler 관련 backend ingestion payload contract
- `docs/governance/LEGAL_RISK_CASES.md`

공유 전 협의:

- DB migration
- `RealEstateRegion`, `RealEstateComplex`, alias schema
- ingestion API request/response
- analysis payload contract
- `docs/product/FINAL_PRODUCT_PLAN.md`

## 현재 우선순위

1. 부동산 source registry 후보 30개 내외를 `disabled` 상태로 정리
2. 공개 HTTP 우선, Playwright fallback, 금지 행위 기준을 source policy에 반영
3. 지역/단지 alias matcher가 필요한 입력 필드 정리
4. 인기글/댓글/조회수 상위글을 최신 글 수집의 대체가 아니라 확산 확인 레이어로 분리
5. pipeline이 backend readiness를 기다리도록 개선

source policy는 `CrawlTarget`보다 상위 게이트이고, `CrawlTarget`은 허용된 소스 안에서 어느 게시판/target을 언제 다시 수집할지 정하는 실행 단위입니다.

추가 커뮤니티 후보는 바로 adapter를 만들지 않습니다. 먼저 `disabled` source 후보로 두고 robots/약관, 공개 목록 접근성, 글 빈도, 조회/댓글 필드, 광고성/홍보성 노이즈, 지역/단지 인식 난이도를 검토한 뒤 `local-research-only` 또는 구현 후보로 올립니다.

## 부동산 source inventory

부동산은 주식보다 정보가 흩어져 있으므로 초기부터 source discovery를 별도 작업으로 봅니다. 목표는 adapter 30개를 바로 만드는 것이 아니라, 30개 내외 후보를 registry에 넣고 공개 접근 가능성, 정책 리스크, 신호 품질을 비교하는 것입니다.

| 그룹 | 후보 수 | 초기 상태 | 확인 기준 |
| --- | --- | --- | --- |
| 공공데이터 API | 5-8 | `local-research-only` 또는 `enabled` 후보 | 공식 API, 트래픽, 응답 필드, 갱신 단서 |
| 공개 부동산 커뮤니티/게시판 | 6-8 | `disabled` | robots/약관, 공개 목록, 글 빈도 |
| 네이버 카페 공개 게시판 | 8-12 | `disabled` | 비로그인 공개 목록만 검토, 로그인 필요 시 제외 |
| 다음 카페 공개 게시판 | 4-6 | `disabled` | 비로그인 공개 목록만 검토, 로그인 필요 시 제외 |
| 뉴스/컬럼/공식 공지 | 6-8 | `disabled` | 제목/link/snippet 저장 가능성, 원문 재게시 금지 |

source registry 필수 필드는 `docs/domains/realestate/DATA_CONTRACT.md`의 `crawl_sources` 계약을 따릅니다.

## 일반 게시판형 최신글 수집 계약

일반 게시판형 커뮤니티는 선택한 게시판의 최신글 목록 흐름을 가능한 한 빠짐없이 따라가는 `GENERAL_BOARD_LATEST` target으로 다룹니다. 게시판별 실제 URL, board id, page/cursor parameter는 source/board registry에 두고, 코드에는 게시판 이름을 하드코딩하지 않습니다.

source 활성화 상태가 `enabled` 또는 허용된 로컬 환경의 `local-research-only`가 아니면 외부 요청을 보내지 않습니다. 로그인, CAPTCHA, 프록시 회전, fingerprint 위장은 하지 않고, 공개 HTTP 목록 수집을 우선합니다. Playwright는 정적 HTTP로 공개 목록을 읽을 수 없지만 정책상 허용되는 렌더링 수집일 때만 사용합니다.

### 순회 방식

- `page` 또는 `cursor` 기반으로 목록을 순회합니다.
- 이미 저장된 `source + boardId + externalId`를 만나면 중단합니다.
- `cutoffAt` 이전 글을 만나면 중단합니다.
- 한 페이지 안에서 일부 중복을 만나도 남은 새 글이 있을 수 있으면 같은 페이지 파싱은 끝까지 처리합니다.
- 공지/광고가 섞이면 일반 글만 분리하고, 고정글은 coverage 통계의 `ignoredPinnedCount`로 남깁니다.
- 중단 조건을 만나지 못하면 board별 안전 한도에서 멈추고 `coverageStatus=partial`로 기록합니다.

### 속도 제한과 차단 대응

- 기본 실행 주기는 `CRAWL_INTERVAL_MINUTES=30` 후보로 둡니다.
- community crawl scheduler는 `max_instances=1`, `coalesce=true`로 겹쳐 실행하지 않습니다.
- 페이지 요청 사이에는 랜덤 지연을 둡니다.
- 403, 429, CAPTCHA, human verification 페이지는 차단 신호로 보고 기본적으로 브라우저 fallback을 시도하지 않습니다.
- 차단 신호는 `blocked` backoff로 기록합니다.
- timeout 또는 일시 네트워크 오류는 `transient-error` backoff로 기록합니다.

게시판별 watermark 후보:

| 필드 | 의미 |
| --- | --- |
| `lastSeenExternalId` | 이전 완료 run에서 확인한 최신 일반 글 id |
| `lastSeenPublishedAt` | 이전 완료 run에서 확인한 최신 일반 글 작성 시각 |
| `lastCompleteCursor` | 마지막으로 완전 순회에 성공한 page/cursor |
| `cutoffAt` | 이번 run에서 더 오래된 글을 볼 필요가 없는 기준 시각 |
| `lastCoverageStatus` | `complete`, `partial`, `blocked`, `failed`, `skipped` |

watermark는 run이 성공적으로 끝났거나 partial이라도 저장된 새 글과 coverage가 일관될 때만 전진시킵니다. 차단, 파싱 실패, 시간 초과로 게시판 앞부분을 확인하지 못한 run은 최신 watermark를 전진시키지 않습니다.

## 저장 payload

새 글은 원문 전문이 아니라 제품 분석에 필요한 제한 필드만 저장합니다.

| 필드 | 기준 |
| --- | --- |
| `source` | source registry 값 |
| `boardId` | source 안에서 게시판을 구분하는 안정 id |
| `externalId` | 원천 게시글 id, 없으면 canonical URL에서 만든 안정 id |
| `url` | canonical URL |
| `title` | 제목 |
| `contentSnippet` | 제한 길이 본문 일부, 전문 저장 금지 |
| `publishedAt` | 작성 시각, 알 수 없으면 `unknown` 처리 후 신뢰도 낮춤 |
| `viewCount` | 조회수, 없거나 숫자로 파싱할 수 없으면 `null` |
| `recommendCount` | 추천수/좋아요 수, 필드 자체가 확인되지 않으면 `null` |
| `commentCount` | 댓글수, 댓글 표시가 없으면 `0`, 필드 자체가 확인되지 않으면 `null` |
| `authorHash` | 작성자 원문 대신 source별 salt/hash |
| `contentHash` | 제목+snippet+작성시각 등으로 만든 중복 감지 hash |
| `crawlRunId` | 어떤 run에서 확인했는지 추적 |

`source + boardId + externalId`를 게시글의 natural key 후보로 둡니다. 같은 글이 최신글 목록과 확산 목록에서 모두 발견되면 게시글은 하나로 합치고, 확산 정보는 별도로 붙입니다.

## 지역/단지 매칭

일반 게시판형 글은 지역명, 단지명, 별칭 매칭을 수행합니다. 매칭 대상은 제목과 `contentSnippet`이며, 댓글은 제한 댓글 수집 대상일 때만 보조 근거로 씁니다.

- 지역/단지 alias 정본은 `realestate` 도메인의 registry를 참조합니다.
- 매칭 결과가 없더라도 `matched=false` 상태로 처리해 "매칭을 생략한 글"과 구분합니다.
- 매칭 후보가 있으면 `targetType`, `targetId`, `matchedText`, `matchSource`, `confidence`를 남깁니다.
- 애매한 별칭은 LLM 보정이나 룰 보정을 거칠 수 있지만, embedding/clustering을 지역/단지 식별의 정본으로 쓰지 않습니다.
- target이 확인된 글만 `reactionDirection` 분류 입력으로 넘깁니다.

별칭 DB는 크롤링의 필수 입력입니다. 공식 단지명, 줄임말, 커뮤니티식 별칭, 오타, 인근 생활권 표현을 모두 후보로 받을 수 있지만, `approved` 전에는 ranking과 정식 snapshot에 섞지 않습니다.

## 확산 레이어와 제한 댓글

인기글, 댓글 많은 글, 조회수 상위글은 최신글 수집의 대체가 아니라 `GENERAL_BOARD_DIFFUSION` 레이어입니다. 같은 게시판의 최신글 run과 별도 target/run으로 운영하고, 확산 여부와 확산 강도를 관찰 데이터로 저장합니다.

확산 레이어는 아래 정보를 기록합니다.

- `diffusionType`: `popular`, `top-viewed`, `high-comment` 등 source별 원천 라벨
- `listPosition`: 인기 순위가 아니라 해당 source 목록에서 노출된 줄 위치
- `observedAt`
- `viewCount`, `recommendCount`, `commentCount`
- 원 최신글 게시물과 연결되는 `postKey`
- 최신글 run에서 보지 못한 글이면 `diffusionOnly=true`

댓글은 처음부터 전체 수집하지 않습니다. 아래 조건 중 하나 이상을 만족하는 글만 제한적으로 수집합니다.

- 확산 레이어에 잡힌 글
- 특정 지역/단지 window에서 언급량이 급증한 관련 글
- source 내부 조회/추천/댓글 상위 percentile 글
- 여러 지역/단지에 영향을 줄 수 있는 정책/시장 전반 고영향 글

댓글도 작성자 hash, 작성 시각, 제한 snippet, 원문 hash 중심으로 저장하고, 전체 원문 보관이나 작성자 원문 식별은 하지 않습니다.

## coverage와 window 집계 입력

모든 board run은 성공 여부와 별개로 coverage를 남깁니다. coverage는 제품 화면에서 데이터 신뢰도를 설명하고, 운영자가 차단/누락/파싱 실패를 구분하는 기준입니다.

coverage 필드 후보:

| 필드 | 의미 |
| --- | --- |
| `pagesFetched` | 실제 읽은 page/cursor 수 |
| `rowsSeen` | 목록에서 본 일반 글 수 |
| `newPostsStored` | 새로 저장한 글 수 |
| `duplicateStop` | 이미 본 글을 만나 정상 중단했는지 |
| `cutoffStop` | 기준 시간 이전 글을 만나 정상 중단했는지 |
| `oldestSeenAt` / `newestSeenAt` | 이번 run에서 확인한 작성 시각 범위 |
| `lastCursor` | 마지막으로 읽은 page/cursor |
| `ignoredPinnedCount` | 공지/광고/고정글 제외 수 |
| `blocked` | 403/429/CAPTCHA/정책 차단 여부 |
| `failedReason` | 파싱 실패, 네트워크 실패, timeout 등 |
| `coverageStatus` | `complete`, `partial`, `blocked`, `failed`, `skipped` |

indicator 입력:

- 전체 반응 방향 분포
- source/board별 반응 방향 분포
- target별 언급량과 직전 window 대비 변화
- target별 기대/우려/중립 count
- top keywords
- diffusion input
- coverage input

## 하지 않는 일

- LLM 반응 방향 산식 변경
- 지역/단지 반응 지표 최종 산식
- 사용자 대시보드 UI
- 매수, 매도, 청약, 대출 행동 판단
- 로그인, CAPTCHA, 프록시, fingerprint 우회
