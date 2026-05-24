# community collection

## 역할

커뮤니티 글을 안정적으로 수집하고, 어떤 소스를 어떤 조건에서 수집할지 관리합니다. 이 문서는 `community` 도메인 안에서 수집 입력과 source policy를 담당하며, 반응 방향 산식 자체는 `REACTION_GUIDE.md`와 `indicator` 도메인으로 분리합니다.

## 담당 범위

- 네이버 종토방 adapter
- 에펨코리아 adapter
- 뽐뿌 증권포럼 adapter 후보
- 디시인사이드 미국 주식 갤러리, 주식갤러리, 국내주식 계열 갤러리 adapter 후보
- 클리앙 주식한당, 팍스넷, 딴지 주식클럽, 네이버 카페형 미국주식, 오늘의유머/개드립/이토랜드/MLB파크 내 주식 글 source registry 검토 후보
- 향후 토스 종목 커뮤니티 adapter 검토
- 일반 게시판형/종목 게시판형 수집 전략
- 인기글/개념글/추천글/조회수 상위글 수집 전략
- 신뢰 블로그 whitelist 기반 source registry 후보
- `CrawlTarget` 우선순위 큐
- source/board registry: `source`, `boardId`, `displayName`, `marketScope`, `crawlPolicy`
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
- `Instrument` schema
- ingestion API request/response
- data 분석 payload contract
- `docs/product/FINAL_PRODUCT_PLAN.md`

## 현재 우선순위

1. pipeline이 backend `CrawlTarget` API를 사용하되 static target fallback을 유지하도록 연결
2. admin target pause/resume/clear-backoff API와 화면 액션 연결
3. source별 robots/약관 검토 결과 기록 방식 정리
4. 인기글/개념글/추천글을 최신 글 수집의 대체가 아니라 확산 확인 레이어로 분리
5. 신뢰 블로그 whitelist와 블로그별 수집 정책 후보 정리
6. pipeline이 backend readiness를 기다리도록 개선

현재 기준에서 source policy는 `CrawlTarget`보다 상위 게이트이고, `CrawlTarget`은 허용된 소스 안에서 어느 게시판/종목을 언제 다시 수집할지 정하는 실행 단위입니다. 과거 설계 근거가 필요할 때만 archive에서 `source-activation-state` 또는 `crawl-target-queue` 키워드로 좁혀 검색합니다.

추가 커뮤니티 후보는 바로 adapter를 만들지 않습니다. 먼저 `disabled` source 후보로 두고 robots/약관, 공개 목록 접근성, 글 빈도, 조회/추천/댓글 필드, 광고성/홍보성 노이즈, 종목 인식 난이도를 검토한 뒤 `local-research-only` 또는 구현 후보로 올립니다.

## 일반 게시판형 최신글 수집 계약

일반 게시판형 커뮤니티는 샘플링하지 않습니다. 선택한 게시판은 최신글 목록 흐름을 가능한 한 빠짐없이 따라가는 `GENERAL_BOARD_LATEST` target으로 다룹니다. 게시판별 실제 URL, board id, page/cursor parameter는 source/board registry에 두고, 코드에는 게시판 이름을 하드코딩하지 않습니다.

1차 대상:

| source | board scope | 역할 |
| --- | --- | --- |
| `FMKOREA` | 에펨코리아 주식 게시판 | 국내/미국 주식이 섞인 일반 투자 반응, 조회/댓글 확산 |
| `DCINSIDE` | 미국주식 갤러리 | 미국 종목 언급, 밈/은어 기반 단기 반응 |
| `DCINSIDE` | 주식 갤러리 | 국내 주식과 시장 전반 단기 반응 |
| `DCINSIDE` | 국내주식 갤러리 | 국내 종목 중심 반응 |
| `PPOMPPU` | 증권포럼 | 국내 투자자 일반 반응, 추천/조회 확산 |

pipeline의 `community_board_registry()`는 위 1차 대상의 최신글 URL, source 안의 `boardId`, 표시명, 시장 범위, 기본 우선순위를 한곳에서 관리합니다. 기본 최신글 target은 5개 게시판 모두 활성화합니다.

source 활성화 상태가 `enabled` 또는 허용된 로컬 환경의 `local-research-only`가 아니면 외부 요청을 보내지 않습니다. 로그인, CAPTCHA, 프록시 회전, fingerprint 위장은 하지 않고, 공개 HTTP 목록 수집을 우선합니다. Playwright는 정적 HTTP로 공개 목록을 읽을 수 없지만 정책상 허용되는 렌더링 fallback일 때만 사용합니다.

### 순회 방식

각 게시판 run은 최신 목록의 첫 page/cursor에서 시작해 오래된 방향으로 이동합니다.

- `page` 또는 `cursor` 기반으로 목록을 순회합니다.
- 이미 저장된 `source + boardId + externalId`를 만나면 중단합니다.
- `cutoffAt` 이전 글을 만나면 중단합니다.
- 한 페이지 안에서 일부 중복을 만나도 남은 새 글이 있을 수 있으면 같은 페이지 파싱은 끝까지 처리합니다.
- 목록 정렬이 고정 최신순이 아니거나 공지/광고가 섞이면 일반 글만 분리하고, 고정글은 coverage 통계의 `ignoredPinnedCount`로 남깁니다.
- 중단 조건을 만나지 못하면 board별 `maxPagesPerRun`, `maxPostsPerRun`, `maxRunSeconds` 같은 안전 한도에서 멈추고 `coverageStatus=partial`로 기록합니다.

### 속도 제한과 차단 대응

운영 crawler는 빠짐없는 최신글 흐름을 목표로 하지만, 공개 게시판에 과도한 요청을 보내지 않습니다.

- 기본 실행 주기는 `CRAWL_INTERVAL_MINUTES=30`입니다.
- community crawl scheduler는 `max_instances=1`, `coalesce=true`로 겹쳐 실행하지 않습니다.
- 일반 게시판 목록은 페이지 요청 사이에 기본 `CRAWLER_PAGE_DELAY_MIN_SECONDS=1.5`, `CRAWLER_PAGE_DELAY_MAX_SECONDS=4.0` 범위의 랜덤 지연을 둡니다.
- 한 run의 기본 상한은 `CRAWLER_MAX_PAGES_PER_RUN=20`, `CRAWLER_MAX_POSTS_PER_RUN=500`입니다.
- 403, 429, CAPTCHA, human verification 페이지는 차단 신호로 보고 브라우저 fallback을 시도하지 않습니다.
- 차단 신호는 `blocked` backoff로 기록하고 기본 6시간 동안 같은 source/board 재시도를 건너뜁니다.
- timeout 또는 일시 네트워크 오류는 `transient-error` backoff로 기록하고 기본 15분 뒤 재시도합니다.

게시판별 watermark는 최소한 아래 값을 둡니다.

| 필드 | 의미 |
| --- | --- |
| `lastSeenExternalId` | 이전 완료 run에서 확인한 최신 일반 글 id |
| `lastSeenPublishedAt` | 이전 완료 run에서 확인한 최신 일반 글 작성 시각 |
| `lastCompleteCursor` | 마지막으로 완전 순회에 성공한 page/cursor |
| `cutoffAt` | 이번 run에서 더 오래된 글을 볼 필요가 없는 기준 시각 |
| `lastCoverageStatus` | `complete`, `partial`, `blocked`, `failed`, `skipped` |

watermark는 run이 성공적으로 끝났거나 partial이라도 저장된 새 글과 coverage가 일관될 때만 전진시킵니다. 차단, 파싱 실패, 시간 초과로 게시판 앞부분을 확인하지 못한 run은 최신 watermark를 전진시키지 않습니다.

현재 MVP 구현은 간단 버전 watermark를 사용합니다. crawler가 시작할 때 backend가 `community_posts`에서 `source + boardId`별 최신 저장 글을 조회해 `lastSeenExternalId`와 `lastSeenPublishedAt`을 돌려주고, crawler는 해당 글을 만나거나 `lastSeenPublishedAt`보다 오래된 글을 만나면 다음 page/cursor로 넘어가지 않습니다. DB watermark가 없거나 너무 오래됐을 때는 기본 24시간 lookback(`CRAWLER_LATEST_LOOKBACK_HOURS`)을 cutoff로 사용합니다. 별도 watermark 테이블은 아직 두지 않습니다.

운영 버전 후속 과제:

- 별도 `crawl_watermarks` 테이블을 둡니다.
- `source`, `boardId`, `targetKind`, `lastSeenExternalId`, `lastSeenPublishedAt`, `lastCompleteCursor`, `lastCoverageStatus`, `lastSuccessAt`, `updatedAt`을 저장합니다.
- `coverageStatus=complete`일 때만 최신 watermark를 전진시킵니다.
- `partial`, `blocked`, `failed` run은 게시글 일부가 저장됐더라도 watermark 전진을 보류하거나 별도 검토 상태로 둡니다.
- 일반 최신글, 확산 레이어, 제한 댓글은 서로 다른 cursor/watermark를 가질 수 있게 분리합니다.

### 저장 payload

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
| `recommendCount` | 추천수/개념 추천수, 빈칸은 `0`, 필드 자체가 확인되지 않으면 `null` |
| `commentCount` | 댓글수, 댓글 표시가 없으면 `0`, 필드 자체가 확인되지 않으면 `null` |
| `authorHash` | 작성자 원문 대신 source별 salt/hash |
| `contentHash` | 제목+snippet+작성시각 등으로 만든 중복 감지 hash |
| `crawlRunId` | 어떤 run에서 확인했는지 추적 |

`source + boardId + externalId`를 게시글의 natural key 후보로 둡니다. 같은 글이 최신글 목록과 인기글 목록에서 모두 발견되면 게시글은 하나로 합치고, 인기글/개념글 정보는 확산 레이어에 별도로 붙입니다.

### 종목 매칭

일반 게시판형 글은 반드시 종목명, 티커, 별칭 매칭을 수행합니다. 매칭 대상은 제목과 `contentSnippet`이며, 댓글은 제한 댓글 수집 대상일 때만 보조 근거로 씁니다.

- 종목 alias와 symbol 정본은 `stock` 도메인의 registry를 참조합니다.
- 매칭 결과가 없더라도 `matched=false` 상태로 처리해 "매칭을 생략한 글"과 구분합니다.
- 매칭 후보가 있으면 `market`, `symbol`, `matchedText`, `matchSource`, `confidence`를 남깁니다.
- 애매한 별칭은 LLM 보정이나 룰 보정을 거칠 수 있지만, embedding/clustering을 종목 식별의 정본으로 쓰지 않습니다.
- 종목이 확인된 글만 종목별 `reactionDirection` 분류 입력으로 넘깁니다.

## 확산 레이어와 제한 댓글

인기글, 개념글, 추천글, 조회수 상위글은 최신글 수집의 대체가 아니라 `GENERAL_BOARD_DIFFUSION` 레이어입니다. 같은 게시판의 최신글 run과 별도 target/run으로 운영하고, 확산 여부와 확산 강도를 관찰 데이터로 저장합니다.

확산 레이어는 아래 정보를 기록합니다.

- `diffusionType`: `popular`, `recommended`, `concept`, `top-viewed` 등 source별 원천 라벨
- `listPosition`: 인기 순위가 아니라 해당 source 목록에서 노출된 줄 위치
- `observedAt`
- `viewCount`, `recommendCount`, `commentCount`
- 원 최신글 게시물과 연결되는 `postKey`
- 최신글 run에서 보지 못한 글이면 `diffusionOnly=true`

현재 구현은 backend `community_post_diffusion_events` 저장소와 ingestion `diffusionEvents` payload를 제공합니다. Python pipeline은 `general-board-diffusion` target의 목록 노출 위치를 `listPosition`으로 변환해 같은 ingestion run에 전달할 수 있습니다. 확산 target은 최신글 watermark를 쓰지 않고 매 run마다 정해진 목록을 다시 관측하되, 기본적으로 작성 후 24시간(`CRAWLER_DIFFUSION_MAX_AGE_HOURS`)을 넘긴 글은 현재 분위기 입력에서 제외합니다. `popular`, `concept`, `recommended`는 우리가 순위를 계산했다는 뜻이 아니라 source가 정한 조건을 만족해 별도 목록에 노출됐다는 관찰 라벨입니다. 같은 글의 목록 노출 여부, 조회수, 추천수, 댓글수 변화는 `observedAt`별로 남깁니다.

기본 확산 target 활성화 기준:

| source | boardId | diffusionType | 기본 상태 | 기준 |
| --- | --- | --- | --- | --- |
| `DCINSIDE` | `nyse` | `concept` | enabled | 공개 목록에서 `exception_mode=recommend` 개념글 목록 확인 |
| `DCINSIDE` | `neostock` | `concept` | enabled | 공개 목록에서 `exception_mode=recommend` 개념글 목록 확인 |
| `DCINSIDE` | `koreastock` | `concept` | enabled | 공개 목록에서 `exception_mode=recommend` 개념글 목록 확인 |
| `FMKOREA` | `stock` | `popular` | disabled | 인기글 URL과 공개 HTTP 접근성을 별도 확인한 뒤 활성화 |
| `PPOMPPU` | `stock` | `popular` | disabled | 핫/인기 category URL과 공개 HTTP 접근성을 별도 확인한 뒤 활성화 |

disabled 확산 후보는 registry에 남기지만 `default_crawl_targets()`에서는 target으로 만들지 않습니다. URL이 불확실하거나 공개 HTTP 접근이 불안정한 상태에서 crawler가 임의 요청을 보내지 않게 하기 위한 기준입니다.

댓글은 처음부터 전체 수집하지 않습니다. 아래 조건 중 하나 이상을 만족하는 글만 제한적으로 수집합니다.

- 확산 레이어에 잡힌 인기글/개념글/추천글
- 30분 window에서 언급량이 급증한 종목 관련 글
- source 내부 조회/추천/댓글 상위 percentile 글
- 다수 종목을 동시에 움직일 수 있는 시장 전반 고영향 글

제한 댓글 수집은 글당 최근 댓글 1 page 또는 source별 `maxCommentsPerPost` 안에서 시작합니다. 댓글도 작성자 hash, 작성 시각, 제한 snippet, 원문 hash 중심으로 저장하고, 전체 원문 보관이나 작성자 원문 식별은 하지 않습니다.

현재 구현은 댓글 본문을 바로 저장하지 않고, 먼저 `community_comment_collection_targets` 큐에 제한 수집 대상을 기록합니다. Pipeline ingestion payload의 `commentCollectionTargets`는 `source + externalId` 기준으로 중복 저장하지 않으며, `triggerReason`, `triggeredAt`, `maxComments`, `priority`, 조회/추천/댓글 관찰값, `crawlRunId`를 남깁니다.
같은 글이 나중에 더 강한 trigger로 다시 관찰되면 기존 큐 row를 낮은 priority 번호, 더 큰 maxComments, 최신 engagement 값, 최신 crawlRunId로 갱신합니다.

기본 trigger:

| triggerReason | 생성 기준 | maxComments | priority |
| --- | --- | --- | --- |
| `diffusion` | 확산 target 또는 확산 event에 잡혔고 댓글수가 1개 이상인 글 | 50 | 50 |
| `high-engagement` | 최신글 run에서 댓글수 30 이상, 추천수 30 이상, 조회수 5000 이상 중 하나를 만족하고 댓글수가 1개 이상인 글 | 30 | 80 |

기본값은 env로 조정할 수 있습니다: `CRAWLER_COMMENT_TRIGGER_MIN_COMMENTS`, `CRAWLER_COMMENT_TRIGGER_MIN_RECOMMENDS`, `CRAWLER_COMMENT_TRIGGER_MIN_VIEWS`, `CRAWLER_HIGH_ENGAGEMENT_MAX_COMMENTS`, `CRAWLER_DIFFUSION_MAX_COMMENTS`.

30분 window의 언급 급증 종목 trigger는 indicator 집계가 실제 target 후보를 내보내는 단계에서 `triggerReason=surging-mention`으로 같은 큐에 붙입니다. 이번 단계에서는 큐와 확산/고영향 게시글 기본 trigger까지만 구현합니다.

## 종목 게시판형 깊이 수집

네이버 종토방 같은 종목형 게시판은 전체 종목을 매번 순회하지 않습니다. `STOCK_BOARD_DEEP_DIVE` target으로 분리하고, `CrawlTarget` 큐 우선순위에 따라 제한적으로 수집합니다.

우선순위 입력:

- 일반 게시판형에서 최근 언급이 급증한 종목
- 사용자가 등록한 관심종목
- 대형주와 대표 ETF
- 포트폴리오 보유 종목
- 시세/거래대금/변동률 기준으로 시장 영향이 큰 종목
- 최근 수집 실패 backoff가 풀린 종목

종목형 게시판은 일반 게시판형에서 발견한 후보를 검증하고, 종목별 보유자 불안, 기대, 이슈 반응을 보강하는 역할입니다. 시장 전체 분위기와 신규 급증 종목 발견의 1차 입력은 일반 게시판형 최신글 run입니다.

## coverage와 30분 집계 입력

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

30분 집계는 `indicator` 도메인이 소유하지만, community는 아래 입력을 안정적으로 넘깁니다.

- market mood: 전체 일반 게시판의 `bullish`, `bearish`, `neutral` 분포
- source mood: source/board별 반응 방향 분포
- stock mention count: 종목별 언급량과 직전 window 대비 변화
- stock reaction count: 종목별 `bullish`, `bearish`, `neutral` count
- top keywords: 전체/source/종목별 대표 키워드
- diffusion input: 인기글/개념글/추천글 편입과 조회/추천/댓글 증가
- coverage input: source별 `coverageStatus`, stale 여부, partial 여부

조회수, 추천수, 댓글수는 source마다 의미가 다르므로 raw 수치를 서로 직접 비교하지 않습니다. 확산 강도는 source 내부 percentile, 시간 대비 증가율, 종목 관련도, source 다양성을 함께 보고 계산합니다.

## 하지 않는 일

- LLM 반응 방향 산식 변경
- 종목별 반응 지표/열기 지수 집계
- 사용자 대시보드 UI
- 모의투자 체결 엔진
- 로그인, CAPTCHA, 프록시, fingerprint 우회
