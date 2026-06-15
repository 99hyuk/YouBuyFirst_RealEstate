# 부동산 데이터 구축 진행 상태

작성일: 2026-06-13

## 이번에 확정한 것

- 공공데이터 1차 provider catalog를 코드와 문서에 고정했습니다.
- `realestate-public-data-providers` pipeline 명령으로 현재 확정 provider/dataset 목록을 JSON으로 확인할 수 있습니다.
- `realestate-public-data-providers --realestate-provider-output sql`로 같은 catalog를 DB seed INSERT 형태로 출력할 수 있습니다. migration seed와 pipeline catalog가 어긋났는지 검수할 때 사용합니다.
- pipeline CLI stdout을 UTF-8로 고정해 Windows PowerShell 파이프/파일 출력에서도 provider catalog 한글이 깨지지 않도록 했습니다.
- 대량 백필을 바로 정규화 테이블에 넣지 않고 raw landing, staging, promoted fact 단계로 나누는 DB 구조를 추가했습니다.
- 단지 target과 provider별 외부키를 연결할 수 있도록 `real_estate_complexes`, `real_estate_complex_provider_keys` 테이블을 추가했습니다.
- 기존 `V21__real_estate_targets_and_region_registry.sql`의 깨진 한글 seed를 정상 한글로 복구했습니다.
- backend에 raw import run/item/staging 저장 API를 추가했습니다.
- pipeline에 MOLIT 실거래/전월세 결과를 raw/staging API로 전송하는 `realestate-market-facts-raw-push` 명령을 추가했습니다.
- backend에 staging record를 `real_estate_market_facts`로 승격하는 `POST /internal/realestate/public-data/promote-staging` API를 추가했습니다.
- pipeline에 승격 API를 호출하는 `realestate-market-facts-promote-staging` 명령을 추가했습니다.
- `realestate-market-facts-raw-push`가 단일 법정동/월뿐 아니라 법정동 목록과 기간 범위 백필을 실행할 수 있게 했고, `--realestate-promote-after-raw-push`로 저장 직후 승격까지 이어갈 수 있습니다.
- MOLIT 실거래/전월세 API 수집은 `pageNo`/`numOfRows` 기반 페이지 반복 수집을 지원합니다. 기본은 페이지당 100건, 최대 1000페이지이며, `--realestate-public-data-page-size`, `--realestate-public-data-max-pages`로 조절합니다.
- 공공데이터 API 결과가 0건이어도 import run을 저장하도록 했습니다. 이로써 실제로 거래가 없던 월과 수집 실패를 구분할 수 있습니다.
- `realestate-market-facts-raw-push`가 실행 후 `taskCount`, `publishedRuns`, `publishedItems`, `emptyRuns`, `promotedRuns`, run별 `rawItems`를 JSON manifest로 출력하도록 했습니다.
- `realestate-public-data-preflight` 명령을 추가했습니다. 실제 공공데이터 API를 호출하기 전에 백필 run 수, 완료 run 제외 결과, 서비스키 준비 여부, page/max page, 승격 옵션을 secret 값 없이 JSON으로 점검합니다.
- `realestate-market-facts-backfill-plan --realestate-backfill-plan-output <path>`로 백필 계획을 JSON manifest 파일로 저장하고, `--realestate-backfill-plan-json <path>`로 preflight/raw-push에서 같은 계획을 다시 사용할 수 있습니다.
- `realestate-regions-inspect`로 법정동코드 CSV를 백엔드에 넣기 전에 지역 계층 수, 시군구 기준 MOLIT 수집대상 수, 실거래/전월세 백필 run 요약을 확인하고 같은 backfill manifest를 파일로 저장할 수 있습니다.
- `--realestate-run-limit` 옵션을 추가했습니다. 대량 백필 전에 preflight, plan, raw-push에서 선택 run 수를 제한해 샘플 run만 먼저 검증할 수 있습니다.
- `realestate-market-facts-raw-push` 대량 실행 확인 가드를 추가했습니다. 선택 run 수가 `--realestate-large-run-threshold`를 넘으면 `--realestate-run-limit` 또는 `--realestate-confirm-large-run` 없이는 실제 provider 생성 전에 중단합니다.
- `--realestate-skip-completed-runs` 옵션으로 이미 `status=completed`인 import run을 계획/실행에서 제외할 수 있습니다. 완료 여부는 계획된 `runKey` 목록을 backend import-run API에 직접 조회해서 판단합니다. 모든 run이 완료되어 있으면 공공데이터 provider를 만들지 않고 manifest만 출력하므로 API 인증키 없이도 재실행 안전성을 확인할 수 있습니다.
- 공시가격 대용량 CSV를 실제 적재하기 전에 row 수, 유효/오류 row, batch 수, 첫/마지막 runKey를 확인하는 `realestate-official-apartment-prices-inspect` 명령을 추가했습니다.
- 한국부동산원 지수, 미분양, 인허가처럼 지역/기간/지표값으로 구성되는 통계 CSV를 위한 `realestate-regional-stat-csv-inspect` / `realestate-regional-stat-csv-raw-push` 공통 adapter를 추가했습니다.
- backend 통합 테스트에서 `지역 import -> market-data-target 생성 -> raw/staging 적재 -> promote -> target별 market fact 조회` 관통 흐름을 검증했습니다.
- 관심 지역 화면의 정본 route를 `/realestate/watchlist`로 고정하고, `/communities`, `/agents` 레거시 호환 route도 active route에서 제거했습니다.
- 지역/단지 상세 route param과 반응 랭킹 링크 식별자를 부동산 대상 `targetId` 기준으로 전환했습니다.
- `RealEstatePriceChart`/`realestate-price-chart` 테스트·fixture·컴포넌트를 부동산 가격 포인트 기준으로 전환하고, 기존 금융 차트식 막대 표현 대신 가격선과 `trade/rent/supply` 보조 흐름으로 바꿨습니다.
- 이전 프로젝트 상세 참고 이미지 자산 폴더를 active docs 자산에서 제거하고, 재유입을 막는 frontend cleanup 테스트를 추가했습니다.
- 미사용 상세 전용 fixture JSON을 active frontend source에서 제거하고, 회귀 방지 테스트를 추가했습니다.
- 미사용 레거시 fixture와 이전 관심 원장 fixture를 active frontend source에서 제거하고, cleanup 테스트 금지 목록에 추가했습니다.
- `market fact`/`target-screener`/`community-board`/`news-market` 계열 화면 class와 미사용 `market-fact-snapshots` fixture를 부동산 `market-fact`/`target-ranking`/`target-board`/`news-market` 기준으로 정리했습니다.
- 대시보드와 지역 반응 fixture의 식별자를 부동산 `targetId` 기준으로 고정하고, 부동산과 맞지 않는 식별자 필드가 다시 들어오지 않도록 회귀 테스트를 추가했습니다.
- pipeline active CLI에서 부동산에 맞지 않는 시장/차트/자금 흐름 계열 명령을 제거했습니다.
- pipeline `serve` 경로에서 부동산에 맞지 않는 시세/차트/수급 refresh job 생성 코드를 제거하고, 기본 `run-once`/`serve` crawl target을 부동산 커뮤니티 seed target으로 전환했습니다.
- backend 기본 context에서 부동산에 맞지 않는 public/internal market controller, entity, repository, seed, migration을 제거했습니다.
- backend alias 저장과 pipeline matcher가 공백/기호 차이를 제거한 정규화 키로 별칭을 비교하도록 맞췄습니다. 예를 들어 `마래푸`, `마 래-푸`는 같은 alias 키로 판단하고, 근거에는 실제 원문 매칭 문자열을 남깁니다.
- backend migration에 시연 MVP용 기본 지역 alias seed를 추가했습니다. `서울`, `경기`, `대전`, `마포구`처럼 공식명/축약명으로 자주 쓰이는 표현은 별도 JSONL 없이 backend matcher export에서 바로 조회됩니다.
- 커뮤니티 게시글에서 승인 alias 바로 뒤의 괄호형 은어를 찾아 `community_slang` alias 후보로 만들고, `realestate-alias-candidates` / `realestate-alias-candidates-push` 명령으로 출력 또는 백엔드 후보 API에 전송할 수 있게 했습니다. 후보는 `reviewState=candidate` 상태이며 운영자 승인 전에는 matcher 정본, ranking, reaction snapshot 입력에 섞지 않습니다.
- `realestate-alias-coverage` 명령을 추가했습니다. 제한 게시글 JSONL과 alias 정본을 기준으로 source별 `matchRate`, `topTargets`, `unmatchedExamples`, `candidateAliases`를 뽑아 네이버/다음 카페처럼 출처가 많은 크롤링 운영에서 alias DB가 비어 있는 구간을 확인할 수 있습니다.
- `realestate-crawl-target-manifest` 명령을 추가했습니다. source 후보 JSONL을 읽어 P0 공개 게시판형 후보만 실행 가능한 crawl target manifest로 만들고, 네이버 카페/로그인 필요/공개 목록 미확인/adapter 미지원 source는 `skipped` 사유로 분리합니다.
- SerpApi Google News 검색 결과를 최근 이슈 후보 content item으로 변환하는 `realestate-recent-issues` / `realestate-recent-issues-push` 명령을 추가했습니다. 검색 결과 수나 순위는 지표로 쓰지 않고, `content_items`와 `content_target_links`에 `candidate` 근거 링크로만 저장합니다.
- `realestate-evidence-logs` / `realestate-evidence-logs-push` 명령을 추가했습니다. reaction snapshot, market fact, timeline event, 최근 이슈 후보, 유사 과거 window 후보를 `POST /internal/realestate/evidence-logs` 요청 shape로 조립하거나 바로 전송합니다.
- SerpApi/query와 유사 과거 evidence label의 깨진 한글을 정상 한국어로 복구했습니다.
- 실거래/전월세 백필 계획에 `--realestate-backfill-chunk-size` 옵션을 추가했습니다. 큰 기간/지역 manifest를 chunk별 실행 단위로 나누고, chunk manifest도 다시 `--realestate-backfill-plan-json` 입력으로 읽어 실패한 묶음만 재실행할 수 있습니다.
- 로컬 secret 예시에 Kakao 지도 SDK 환경변수 이름을 추가했습니다. 실제 key는 root `.env`와 `front/.env.local`에만 두고, repo에는 `.env.example`과 `front/.env.example`의 placeholder만 남깁니다.
- 화면 정의서에 하이브리드 지도 기준을 반영했습니다. 전국~동 단위는 자체 도식화 heatmap, 동/단지 상세 단계는 사이트 내부에 카카오맵 SDK를 내장하는 방향입니다.
- Docker MySQL 기준으로 migration을 끝까지 적용하고, `molit_apt_trade`, `molit_apt_rent` 실제 API 샘플을 raw -> staging -> promoted fact까지 검증했습니다.
- 샘플 기준은 종로구 `legalDongCode=11110`, `dealYm=202501`입니다. raw item은 매매 26건, 전월세 184건이며, promoted market fact는 매매 25건, 전월세 168건입니다.
- `GET /api/realestate/dashboard/market-summary?legalDongCode=11110`에서 매매/전월세 요약이 `provider`, `asOf`, `stale`, `dataStatus`와 함께 조회되는 것을 확인했습니다.
- MySQL에서 `content_items.url` 직접 unique index가 길이 제한에 걸리지 않도록 `url_hash` unique 기준으로 보정했습니다.
- 공공데이터 raw-push 실행 중 HTTP client가 query string을 INFO 로그로 출력하지 않도록 `httpx`/`httpcore` 로그 레벨을 낮췄습니다. 서비스키 값은 repo와 문서에 남기지 않습니다.
- 지도/반응/상세 화면에서 쓰는 대표 fixture `targetId`를 화면 전용 대문자 임시 ID가 아니라 `real_estate_targets.id` 형식으로 통일했습니다. 예: `region-seoul-mapo`, `living-area-gyeonggi-dongtan-station`.
- 프론트 상세 화면의 화면용 ID와 API용 ID 분리를 제거하고, route `targetId`를 그대로 content/timeline/evidence 계열 API에 넘기는 기준으로 정리했습니다.
- `/realestate/targets/:targetId`의 시간대별 변화 섹션은 `GET /api/realestate/targets/{targetId}/timeline?limit=6`을 우선 조회하고, 실패하거나 빈 응답이면 기존 fixture timeline으로 fallback합니다.
- `/realestate/targets/:targetId`의 AI 근거 로그 섹션은 `GET /api/realestate/targets/{targetId}/evidence-logs?limit=3`을 우선 조회하고, 평가 요약, 버전, confidence, caveat, evidence item을 표시합니다. 저장된 로그가 없으면 근거 로그 대기 상태로 둡니다.
- EvidenceLog 응답은 `refType=content` 근거 항목에 대해 `content_items`의 URL/source/asOf/status를 보강합니다. 상세 화면은 이 값을 AI 근거 로그 안의 외부 링크 칩으로 표시하므로 SerpApi 후보가 `candidate` 상태인지 숨기지 않고 확인할 수 있습니다.
- EvidenceLog 배치는 public content API가 아니라 `GET /internal/realestate/targets/{targetId}/content?reviewState=candidate&linkType=search_candidate`를 사용합니다. 따라서 SerpApi 후보가 아직 공개 timeline 승인 전이어도 AI 근거 로그 입력으로 붙일 수 있고, 공개 `/api/realestate/targets/{targetId}/content`는 계속 approved content만 반환합니다.
- 대표 화면 target을 backend registry seed에 추가했습니다. 마포구는 `real_estate_regions`와 MOLIT `market_data_targets`까지 연결했고, 생활권/단지 후보는 `mock` 또는 `candidate` 상태로 target 정본만 먼저 확보했습니다.
- 지도 레이어용 `map_boundary_assets`, `map_features`, `map_layer_snapshots` 테이블을 추가했습니다.
- `GET /api/realestate/map/layers`를 추가해 전국/시군구 지도 화면이 DB snapshot을 우선 조회하고, 실패하거나 없는 구간은 명시적인 fixture fallback으로 내려가도록 했습니다.
- 전국 17개 시도와 서울 일부 시군구(종로구, 마포구) 지도 snapshot seed를 넣었습니다. 현재 값은 실제 batch 연결 전 기준값이므로 `provider=seed`, `dataStatus=mock`, `stale=true`로 표시합니다.
- `POST /internal/realestate/map/layer-snapshots/refresh`를 추가했습니다. 실제 `apt_trade` market fact와 최신 reaction snapshot을 묶어 기간별 상승/하락, 표본 수, 신뢰도를 `map_layer_snapshots`에 저장합니다.
- `serve --enable-realestate-daily-refresh --enable-realestate-map-layer-refresh`로 지도 레이어 snapshot 갱신을 일일 refresh step에 포함할 수 있게 했습니다.
- `/realestate/map`과 `/realestate/map/:regionId`는 지도 route에서 `region-seoul`, `region-daejeon` 같은 DB target id를 우선 사용합니다. 기존 화면용 slug 진입은 호환만 유지합니다.
- `/realestate/targets/:targetId`에 카카오맵 SDK 내장 지도 prototype을 추가했습니다. `region-seoul-mapo`, `living-area-gyeonggi-dongtan-station`, `complex-mapo-raemian-prugio`는 단지 marker와 선택 패널을 보여주며, 테스트/key missing/SDK 비활성화 상태에서는 도식화 fallback을 표시합니다.
- `real_estate_complexes`에 단지 marker용 좌표, 좌표 provider/asOf/status, marker summary/status 필드를 추가하고 `GET /api/realestate/targets/{targetId}/nearby-complexes`를 연결했습니다. 상세 화면은 이 API를 우선 사용하고 실패하거나 빈 응답이면 기존 fixture로 fallback합니다.
- `serve --enable-realestate-daily-refresh` scheduler job을 추가했습니다. 현재는 market fact refresh, reaction snapshot refresh, SerpApi 최근 이슈 후보 refresh, EvidenceLog refresh를 하루 단위 step으로 묶을 수 있으며, 각 step은 `OK`, `EMPTY`, `*_ERROR`, `PARTIAL` 상태를 남깁니다. 최근 이슈 refresh는 `--realestate-search-targets-jsonl`이 없으면 최신 backend reaction ranking TOP target을 읽어 SerpApi 검색 대상으로 사용합니다. EvidenceLog refresh는 최신 backend reaction ranking을 읽고 target별 market fact/content 후보를 붙여 `POST /internal/realestate/evidence-logs`로 전송합니다.
- `realestate-daily-refresh` one-shot 명령을 추가했습니다. `serve`처럼 계속 떠 있지 않고 `market_facts -> community_crawl -> reaction_snapshots -> recent_issues -> evidence_logs -> map_layers`를 한 번 실행한 뒤 summary JSON을 출력하므로, 발표 전 수동 갱신이나 GitHub Actions/로컬 스케줄러에서 쓰기 좋습니다.
- `realestate-daily-refresh`에서 `SERPAPI_API_KEY`가 비어 있으면 전체 배치를 중단하지 않고 `recent_issues` step을 `CONFIG_MISSING`으로 남긴 뒤 EvidenceLog와 map layer refresh를 계속 진행합니다. 이 경우 전체 summary는 `PARTIAL`로 표시되어 최근 이슈 갱신이 완전 성공처럼 보이지 않습니다. EvidenceLog는 최근 이슈 후보가 없는 target에 `search_candidate_missing` caveat을 남깁니다. 단독 `realestate-recent-issues` 명령은 실제 후보 수집용이므로 여전히 key를 요구합니다.
- `GET /internal/ingestions/community-posts/export`를 추가했습니다. 크롤러가 `community_posts`에 저장한 게시글을 source/시간 window/limit 기준으로 다시 꺼내 reaction snapshot refresh 입력으로 쓸 수 있습니다.
- `serve --enable-realestate-reaction-snapshots-refresh --realestate-use-backend-community-posts`를 켜면 JSONL 파일 없이 backend `community_posts` export를 읽어 alias 매칭, reaction observation, snapshot 생성까지 이어갑니다.
- `serve`와 `realestate-daily-refresh`의 reaction snapshot refresh가 `--realestate-use-backend-aliases`를 함께 받으면 JSONL alias 파일 없이 backend alias registry를 matcher 입력으로 사용합니다. 시연/배치 기본 경로는 backend community post export + backend alias registry 조합입니다.
- `GET /api/realestate/reactions/rankings`는 `parentTargetId`를 받을 수 있습니다. 예를 들어 `parentTargetId=region-seoul`이면 서울 target과 직접 하위 region snapshot만 ranking합니다.
- `/realestate/reactions`는 지역/단지 랭킹을 `limit=10`으로 요청하고, 전체 TOP10과 서울/경기/대전/인천 시도별 TOP10 필터를 제공합니다. 시도 필터를 누르면 지역 ranking과 단지군 ranking 모두 `parentTargetId`로 재조회합니다. API 요청이 성공했지만 특정 그룹이 비어 있으면 mock 행을 섞지 않고 수집 전/insufficient 빈 상태를 표시하며, API 실패 때만 fixture fallback을 씁니다.
- 2026-06-15 로컬 smoke에서 공개 source 2곳 기준 게시글 849건을 수집했고, backend community post export와 backend alias registry로 24시간 reaction refresh를 실행해 observation 33건, snapshot 10건을 생성했습니다. `GET /api/realestate/reactions/rankings?windowMinutes=1440&limit=10`은 실제 DB snapshot 기준 TOP10 지역 행을 반환합니다.
- 최신 reaction ranking 조회는 요청한 `windowMinutes`와 같은 window만 고르도록 보정했습니다. 60분 snapshot과 24시간 snapshot이 함께 있어도 24시간 화면이 더 짧은 최신 window를 섞어 읽지 않습니다.
- 현재 seed marker 좌표는 DB/API로 내려오지만 검증 좌표가 아니므로 `provider=front_fixture`, `dataStatus=mock`, `stale=true`로 노출합니다. 실제 단지 좌표, 법정동 코드, provider key 검증은 계속 남아 있습니다.
- GMS OpenAI-compatible chat endpoint를 쓰는 EvidenceLog summary 보강 client를 추가했습니다. `realestate-evidence-logs(-push) --evidence-use-gms-llm`을 켜면 기존 룰 기반 EvidenceLog를 만든 뒤 LLM이 `summary`, `subtitle`, `tone`만 보강합니다. 금지 문구가 포함되면 LLM 문구를 폐기하고 `skipReason=forbidden_copy_detected`와 caveat을 남깁니다.
- 2026-06-15 로컬 smoke에서 최신 24시간 reaction TOP10을 대상으로 GMS `gpt-5-mini` EvidenceLog refresh를 실행해 10건을 저장했습니다. 저장 API 응답은 `modelName`, `promptVersion`, `evaluationVersion`, `evaluatedAt`을 기준으로 확인합니다.
- 일일 EvidenceLog refresh는 `--evidence-similar-windows-jsonl`을 함께 받으면 target/window가 맞는 유사 과거 후보를 EvidenceLog `similar_window` 근거로 자동 병합합니다.
- `--similar-engine qdrant --embeddings-jsonl <path>`를 함께 주면 일일 EvidenceLog refresh가 Qdrant collection health를 먼저 확인한 뒤, 현재 target/window의 임베딩으로 유사 과거 window를 직접 검색해 EvidenceLog에 붙입니다. collection이 준비되지 않았거나 source embedding이 없으면 전체 배치를 실패시키지 않고 유사 과거 후보만 비운 상태로 진행합니다.
- 2026-06-15 지도 layer refresh smoke에서 2025-01-31 MOLIT 샘플 market fact 기준 서울 시도/시군구 snapshot을 생성했습니다. 아직 전국 실제 지표는 완성되지 않았고, 표본이 부족한 지역은 기존 seed/mock fallback이 남습니다. 특히 소표본 실거래 평균 비교는 지수형 provider로 대체하기 전까지 과도한 변화율이 나올 수 있으므로, 절대 변화율 50% 초과 구간은 값을 숨기지 않되 `dataStatus=partial`, `stale=true`, 낮은 confidence로 노출합니다.
- 2026-06-15 로컬 `.env`에 `SERPAPI_API_KEY` 값을 설정했습니다. 실제 key는 repo에 기록하지 않습니다.
- 2026-06-15 SerpApi 직접 smoke에서 Google News 검색 응답 `search_metadata.status=Success`와 검색 결과 title 존재를 확인했습니다.
- 2026-06-15 pipeline `realestate-recent-issues` smoke에서 `region-seoul-mapo` 1개 target과 `정책` 1개 keyword 기준으로 `sourceId=serpapi:google_news`, `linkType=search_candidate`, `reviewState=candidate` 후보 content item 출력까지 확인했습니다.
- 2026-06-15 최신 24시간 reaction TOP10 기반 `realestate-daily-refresh --enable-realestate-recent-issues-refresh`를 실행해 target 10개, 후보 content item 196건을 backend에 저장했습니다. 검색 결과 수나 순위는 관심도 지표로 쓰지 않고 EvidenceLog 근거 후보로만 연결합니다.
- 2026-06-15 TOP10 region target에 대해 SerpApi candidate content 196건을 붙인 뒤 GMS `gpt-5-mini` EvidenceLog refresh를 다시 실행했습니다. 결과는 target 10개, log 10건, content evidence 196건이며 market fact와 similar window가 부족한 target은 `market_fact_missing`, `similar_window_missing` caveat을 남깁니다.
- 시도별 TOP10 필터는 지역 랭킹과 단지군 랭킹 모두 `parentTargetId`를 전달합니다. backend는 parent 지역과 하위 지역 target뿐 아니라 `real_estate_complexes.region_target_id`가 scope 안에 있는 단지 snapshot도 포함해, 서울 TOP10 같은 필터에서 마포 하위 단지군을 서버 응답으로 조회할 수 있습니다.
- 지도 layer 응답은 실제 refresh snapshot과 seed/mock snapshot이 섞인 경우 top-level `dataStatus=partial`, `stale=true`로 표시합니다. 따라서 일부 지역만 실제 데이터가 붙은 MVP 상태가 전체 `ok`처럼 보이지 않습니다.
- 지역 상세 지도 footer는 시군구 snapshot이 live로 붙었을 때 `provider · dataStatus · fresh/stale · asOf`를 표시합니다. 그래서 실제 API 값이 들어와도 `DB snapshot` 같은 축약 문구만 보여 출처와 기준 시각이 가려지지 않습니다.

## 1차 provider

| dataset id | 역할 | 상태 |
| --- | --- | --- |
| `molit_apt_trade` | 아파트 매매 실거래가 | 백필 대상 |
| `molit_apt_rent` | 아파트 전월세 실거래가 | 백필 대상 |
| `molit_official_apartment_price_csv` | 공동주택 호별 공시가격 대용량 CSV | 백필 대상 |
| `reb_real_estate_statistics` | 한국부동산원 가격지수/거래현황 | 백필 대상 |
| `molit_unsold_housing_stat` | 미분양/준공 후 미분양 | 백필 대상 |
| `molit_housing_permit_stat` | 주택 인허가 실적 | 백필 대상 |
| `molit_buildinghub_housing_approval` | 주택건설사업계획승인/공급 이벤트 후보 | 보조/검증 대상 |

## DB 구조

새 migration:

- `V27__real_estate_public_data_catalog_and_raw_ingestion.sql`
- `V28__real_estate_complex_registry.sql`

흐름:

```text
공공데이터 API/CSV
-> real_estate_public_data_import_runs
-> real_estate_public_data_raw_items
-> real_estate_market_fact_staging
-> real_estate_market_facts
```

단지 매핑:

```text
real_estate_targets
-> real_estate_complexes
-> real_estate_complex_provider_keys
```

## 아직 안 한 것

- 실제 공공데이터 대용량 CSV 다운로드/백필 실행
- 실제 MOLIT 실거래/전월세 API의 전체 지역/기간 운영 백필 실행
- 공시가격 CSV 실제 원본 다운로드 후 대량 백필 실행
- 한국부동산원 통계, 미분양, 인허가 실제 원본 파일의 컬럼명/다운로드 경로 검증과 정규화 매핑
- 네이버/다음 카페를 포함한 실제 공개 source별 adapter 활성화
- alias 후보 운영자 검수 화면
- SerpApi 후보 링크 운영 검수와 승인 workflow
- LLM provider 기반 평가의 재시도/품질평가/Langfuse 관측 고도화
- 실제 단지 좌표/주소/법정동 코드 provider 검증과 단지 marker API의 market fact/reaction snapshot 요약 연결

## 다음 작업

1. 공시가격 CSV inspect 명령으로 row 수, 오류 샘플, batch 수를 먼저 확인하고, streaming parser와 batch raw-push 명령으로 샘플 파일 백필을 검증합니다.
2. 한국부동산원 통계, 미분양, 인허가 실제 원본 파일을 내려받아 regional stat CSV adapter에 맞는 컬럼 매핑을 검증합니다.
3. 종로구 샘플과 같은 방식으로 실거래/전월세 백필 범위를 `run-limit`이 있는 소규모 묶음에서 시군구/기간 단위로 확장합니다.
4. 레거시 제거 이후 남은 작업은 실제 공공데이터 전체 백필, 공개 source adapter 활성화, alias 후보 운영자 검수, SerpApi 후보 링크 승인 workflow, LLM provider/guardrail 기반 평가 고도화입니다.

## 현재 실행 가능한 명령

GMS Gemini 임베딩 생성:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:GMS_KEY="로컬 GMS 키"
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-embeddings --reaction-snapshots-jsonl C:\data\ybf-realestate\reaction-snapshots.jsonl
```

이 명령은 reaction snapshot window를 임베딩용 텍스트로 요약하고 `gemini-embedding-2` 벡터를 출력합니다.

Qdrant vector store 적재:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:QDRANT_URL="http://localhost:6333"
$env:QDRANT_API_KEY="필요한 경우에만"
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-vector-upsert --embeddings-jsonl C:\data\ybf-realestate\embeddings.json
```

Qdrant collection health check:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:QDRANT_URL="http://localhost:6333"
$env:QDRANT_API_KEY="필요한 경우에만"
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-vector-health
```

이 명령은 `collection`, `ready`, `status`, `pointsCount`, `vectorsCount`, `message`만 출력합니다. Qdrant API key는 요청 헤더에만 사용하고 출력 JSON에는 포함하지 않습니다. `status=missing`이면 먼저 `realestate-vector-upsert`로 collection을 만들고 임베딩 포인트를 적재해야 합니다.

Qdrant 유사 window 검색:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:QDRANT_URL="http://localhost:6333"
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-similar-windows --similar-engine qdrant --embeddings-jsonl C:\data\ybf-realestate\embeddings.json --vector-source-input-id reaction-window:region-seoul-mapo:2026-06-14T00:00:00Z:2026-06-14T01:00:00Z --similar-top-n 5 --similar-market-facts-jsonl C:\data\ybf-realestate\market-facts.jsonl --similar-horizon-days 90
```

검색 출력은 `engine=qdrant`와 `similar_window` evidence item shape를 포함하므로 `realestate-evidence-logs --evidence-similar-windows-jsonl <vector-search-output>` 입력으로 이어 붙일 수 있습니다. `--similar-market-facts-jsonl`을 함께 주면 matched window 이후 지정 horizon 안의 market fact 흐름을 `afterMarketSummary`로 붙이고, evidence label에도 대표 흐름을 반영합니다. 기존 별도 명령인 `realestate-vector-search`도 남아 있지만, 운영자가 쓰는 유사 과거 검색 정본은 `realestate-similar-windows --similar-engine <batch|qdrant>`입니다.

GMS LLM EvidenceLog summary 보강:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:GMS_KEY="로컬 GMS 키"
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-evidence-logs --reaction-snapshots-jsonl C:\data\ybf-realestate\reaction-snapshots.jsonl --evidence-target-id region-seoul-mapo --evidence-window-start 2026-06-14T00:00:00Z --evidence-use-gms-llm --evidence-llm-model gpt-5-mini
```

이 명령은 먼저 룰 기반 EvidenceLog를 만들고, GMS OpenAI-compatible chat endpoint로 `summary`, `subtitle`, `tone`만 보강합니다. `사라`, `청약 넣어라`, `오른다`, `수익 보장`처럼 행동 지시나 단정처럼 보이는 문구가 나오면 LLM 결과를 폐기하고 `forbidden_copy_detected` caveat을 남깁니다.

Provider catalog 확인:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-public-data-providers
```

DB seed INSERT 검수용 출력:

```powershell
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-public-data-providers --realestate-provider-output sql
```

MOLIT 실거래/전월세 백필 계획 생성:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-backfill-plan --realestate-lawd-codes 11110 26000 --realestate-start-ym 202401 --realestate-end-ym 202406 --realestate-datasets trade rent
```

이 명령은 실제 API 호출을 하지 않고, 월/법정동/데이터셋 단위의 재시도 가능한 작업 목록만 만듭니다.

법정동 CSV에서 지역 target과 시군구별 백필 계획을 먼저 검수:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-regions-inspect --legal-dong-code-csv C:\data\molit_legal_dong_codes.csv --realestate-start-ym 202605 --realestate-end-ym 202606 --realestate-datasets trade rent --realestate-backfill-plan-output C:\data\ybf-realestate\molit-region-plan-202605-202606.json
```

이 명령은 `sido`, `sigungu`, `eupmyeondong` 지역 수와 `sigungu` 기준 `molit_apt_trade`, `molit_apt_rent` 수집대상 수를 보여줍니다. 저장된 manifest는 바로 `realestate-public-data-preflight --realestate-backfill-plan-json ...`와 `realestate-market-facts-raw-push --realestate-backfill-plan-json ...`에 재사용합니다.

백필 계획을 파일로 고정:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-backfill-plan --realestate-use-backend-targets --realestate-start-ym 202605 --realestate-end-ym 202606 --realestate-skip-completed-runs --realestate-backfill-plan-output C:\data\ybf-realestate\molit-plan-202605-202606.json
```

백필 계획을 chunk 단위로 고정:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-backfill-plan --realestate-use-backend-targets --realestate-start-ym 202401 --realestate-end-ym 202606 --realestate-skip-completed-runs --realestate-backfill-chunk-size 100 --realestate-backfill-plan-output C:\data\ybf-realestate\molit-plan-202401-202606-chunks.json
```

저장된 계획으로 preflight:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-public-data-preflight --realestate-backfill-plan-json C:\data\ybf-realestate\molit-plan-202605-202606.json --realestate-run-limit 1
```

저장된 계획으로 raw-push:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:DATA_GO_SERVICE_KEY="..."
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-raw-push --realestate-backfill-plan-json C:\data\ybf-realestate\molit-plan-202605-202606.json --realestate-run-limit 1 --realestate-promote-after-raw-push --realestate-validation-status valid --realestate-promote-limit 1000
```

manifest 입력도 `--realestate-large-run-threshold` 확인 가드를 그대로 탑니다. 따라서 전체 run 실행 전에는 `--realestate-run-limit`으로 샘플을 검증하고, 전체 실행 시에만 `--realestate-confirm-large-run`을 명시합니다.

완료된 import run을 제외한 백필 계획 생성:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-backfill-plan --realestate-use-backend-targets --realestate-start-ym 202605 --realestate-end-ym 202606 --realestate-skip-completed-runs
```

이 명령은 backend의 `GET /internal/realestate/public-data/import-runs?runKey=...&status=completed` 결과를 보고 이미 완료된 `runKey`를 제외합니다. pipeline은 계획된 runKey를 100개 단위로 나눠 조회하므로 dataset별 최근 500개 목록 한도에 기대지 않습니다.

실제 API 호출 전 preflight 점검:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-public-data-preflight --realestate-use-backend-targets --realestate-start-ym 202605 --realestate-end-ym 202606 --realestate-skip-completed-runs --realestate-run-limit 1 --realestate-promote-after-raw-push --realestate-public-data-page-size 100 --realestate-public-data-max-pages 1000
```

이 명령은 공공데이터 API를 호출하지 않습니다. `DATA_GO_SERVICE_KEY` 값은 출력하지 않고 `configured`, `missing`, `not_required` 상태만 보여줍니다. `remainingRuns`가 0이면 실제 호출할 run이 없으므로 서비스키가 없어도 `ready=true`가 될 수 있습니다. `runLimit`이 있으면 `omittedByRunLimit`로 이번 샘플에서 일부러 제외한 run 수를 확인합니다. `largeRunRequiresConfirmation=true`이면 raw-push 전체 실행 전에 limit을 낮추거나 `--realestate-confirm-large-run`을 명시해야 합니다.

MOLIT 실거래/전월세를 raw/staging API로 전송:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:DATA_GO_SERVICE_KEY="..."
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-raw-push --realestate-lawd-code 11110 --realestate-deal-ym 202606 --realestate-datasets trade rent --realestate-public-data-page-size 100 --realestate-public-data-max-pages 1000
```

이 명령은 `POST /internal/realestate/public-data/raw-ingestions`로 import run, raw item, staging item을 저장합니다. 실행 후 출력되는 JSON manifest에서 `publishedRuns`, `publishedItems`, `emptyRuns`, run별 `rawItems`를 확인합니다. 한 페이지가 꽉 차면 다음 페이지를 조회하고, 마지막 페이지가 `pageSize`보다 적으면 멈춥니다.

여러 법정동과 기간 범위를 한 번에 raw/staging API로 전송하고, 저장 직후 market fact로 승격:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:DATA_GO_SERVICE_KEY="..."
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-raw-push --realestate-lawd-codes 11110 11680 --realestate-start-ym 202605 --realestate-end-ym 202606 --realestate-datasets trade rent --realestate-public-data-page-size 100 --realestate-public-data-max-pages 1000 --realestate-skip-completed-runs --realestate-promote-after-raw-push --realestate-validation-status valid --realestate-promote-limit 1000
```

이 명령은 월/법정동/데이터셋 단위로 import run을 나누므로 실패한 단위만 다시 실행하기 쉽습니다. 조회 결과가 0건이어도 `items=[]`인 import run을 남기고, 실행 manifest의 `emptyRuns`로 집계됩니다.

백엔드에 등록된 지역 수집 대상(`real_estate_market_data_targets`)을 기준으로 백필 계획 확인:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-backfill-plan --realestate-use-backend-targets --realestate-start-ym 202605 --realestate-end-ym 202606
```

지역 import가 만든 `molit_apt_trade`, `molit_apt_rent` 대상만 골라 중복을 제거한 뒤 `월/법정동/데이터셋` 단위의 import run 계획을 출력합니다.

백엔드에 등록된 지역 수집 대상을 기준으로 실거래/전월세 raw/staging 적재:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:DATA_GO_SERVICE_KEY="..."
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-raw-push --realestate-use-backend-targets --realestate-start-ym 202605 --realestate-end-ym 202606 --realestate-public-data-page-size 100 --realestate-public-data-max-pages 1000 --realestate-skip-completed-runs --realestate-run-limit 1 --realestate-promote-after-raw-push --realestate-validation-status valid --realestate-promote-limit 1000
```

이 명령은 사람이 `--realestate-lawd-codes`를 다시 복사하지 않고 `GET /internal/realestate/market-data-targets?enabled=true` 결과를 기준으로 실제 백필을 수행합니다. 운영 첫 실행은 `--realestate-run-limit 1`로 1개 run만 검증하고, raw/staging/promote 결과가 정상인 것을 확인한 뒤 limit을 늘립니다.

대량 범위를 의도적으로 실행할 때:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:DATA_GO_SERVICE_KEY="..."
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-raw-push --realestate-use-backend-targets --realestate-start-ym 202401 --realestate-end-ym 202606 --realestate-public-data-page-size 100 --realestate-public-data-max-pages 1000 --realestate-skip-completed-runs --realestate-confirm-large-run --realestate-promote-after-raw-push --realestate-validation-status valid --realestate-promote-limit 1000
```

이 명령은 샘플 검증이 끝난 뒤에만 사용합니다. 선택 run 수가 기본 threshold 50개를 넘으면 `--realestate-confirm-large-run` 없이는 provider 생성 전에 중단됩니다.

저장된 staging record를 정규화 market fact로 승격:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-market-facts-promote-staging --realestate-provider-dataset molit_apt_trade --realestate-run-key molit_apt_trade:11110:202606 --realestate-validation-status valid --realestate-promote-limit 1000
```

이 명령은 `POST /internal/realestate/public-data/promote-staging`를 호출하고, 검증 상태가 `valid`인 staging record를 `real_estate_market_facts`로 upsert합니다.

MOLIT 공동주택 호별 공시가격 대용량 CSV를 적재 전 점검:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-official-apartment-prices-inspect --realestate-official-apartment-price-csv C:\data\molit_official_apartment_price_2025.csv --realestate-official-apartment-price-base-date 2025-01-01 --realestate-official-apartment-price-batch-size 1000
```

이 명령은 DB에 쓰지 않고 `totalRows`, `validRows`, `invalidRows`, `batchCount`, 첫/마지막 `runKey`, 일부 `providerObjectId`, 오류 샘플을 출력합니다. 대량 적재 전 이 결과로 배치 수와 오류율을 먼저 확인합니다.

MOLIT 공동주택 호별 공시가격 대용량 CSV를 raw/staging API로 전송:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-official-apartment-prices-raw-push --realestate-official-apartment-price-csv C:\data\molit_official_apartment_price_2025.csv --realestate-official-apartment-price-base-date 2025-01-01 --realestate-official-apartment-price-batch-size 1000 --realestate-promote-after-raw-push --realestate-validation-status valid --realestate-promote-limit 1000
```

이 명령은 공공데이터포털의 1,500만 건 이상 CSV를 한 번에 메모리에 올리지 않고 streaming으로 읽어서 `molit_official_apartment_price_csv:YYYYMMDD:000001` 같은 import run 단위로 나눠 저장합니다. `sourceLabel`에는 입력 CSV 경로가 남고, 각 row는 `factType=official_apartment_price`, `targetType=complex_unit`, `providerDataset=molit_official_apartment_price_csv`로 staging 됩니다.

지역 통계 CSV를 적재 전 점검:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-regional-stat-csv-inspect --realestate-stat-csv C:\data\molit_unsold_202604.csv --realestate-provider molit_stat --realestate-provider-dataset molit_unsold_housing_stat --realestate-fact-type unsold_housing --realestate-stat-batch-size 1000
```

지역 통계 CSV를 raw/staging API로 전송:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-regional-stat-csv-raw-push --realestate-stat-csv C:\data\molit_unsold_202604.csv --realestate-provider molit_stat --realestate-provider-dataset molit_unsold_housing_stat --realestate-fact-type unsold_housing --realestate-stat-batch-size 1000 --realestate-promote-after-raw-push
```

이 명령은 `기준월`, `지역코드`, `지역명`, `항목`, `값`, `단위` 중심의 정규화 CSV를 읽어 `targetType=region` market fact staging record로 저장합니다. 미분양은 `providerDataset=molit_unsold_housing_stat`, 인허가는 `molit_housing_permit_stat`, 한국부동산원 지수는 `reb_real_estate_statistics`처럼 dataset만 바꿔 같은 경로를 사용할 수 있습니다.

Backend 확인 API:

```text
GET /internal/realestate/public-data/import-runs?providerDataset=molit_apt_trade
POST /internal/realestate/public-data/raw-ingestions
POST /internal/realestate/public-data/promote-staging
```

커뮤니티 게시글에서 alias 후보 추출:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-alias-candidates --realestate-aliases-jsonl C:\data\realestate_aliases.jsonl --community-posts-jsonl C:\data\community_posts.jsonl
```

source별 alias coverage 확인:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-alias-coverage --realestate-use-backend-aliases --community-posts-jsonl C:\data\community_posts.jsonl
```

alias 후보를 backend 후보 API로 전송:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-alias-candidates-push --realestate-use-backend-aliases --community-posts-jsonl C:\data\community_posts.jsonl
```

두 명령은 승인된 alias 주변에서 발견된 괄호형 은어를 `reviewState=candidate`로만 다룹니다. 운영자 승인 전까지 이 후보는 정식 matcher export, ranking, reaction snapshot 입력에 섞이지 않습니다.

SerpApi 최근 이슈 후보 생성:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:SERPAPI_API_KEY="..."
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-recent-issues --realestate-search-targets-jsonl C:\data\realestate_search_targets.jsonl --realestate-issue-keywords 교통 정책 개발 금리 --realestate-search-as-of 2026-06-12T01:30:00Z --serpapi-result-limit 5
```

SerpApi 최근 이슈 후보를 backend content API로 전송:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:SERPAPI_API_KEY="..."
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-recent-issues-push --realestate-search-targets-jsonl C:\data\realestate_search_targets.jsonl --realestate-issue-keywords 교통 정책 개발 금리
```

`realestate-recent-issues-push`는 `POST /internal/realestate/content-items`로 `sourceId=serpapi:google_news`, `linkType=search_candidate`, `reviewState=candidate`, `dataStatus=candidate` payload를 전송합니다. 이 후보는 승인 전까지 timeline 정본에 노출되지 않습니다.

시연 MVP용 전체 일일 refresh:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:CRAWL_RUNTIME_ENV="local"
$env:SERPAPI_API_KEY="..."
$env:GMS_KEY="..."
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-daily-refresh --enable-realestate-market-facts-refresh --realestate-deal-ym 202606 --enable-realestate-daily-crawl-refresh --enable-realestate-reaction-snapshots-refresh --realestate-use-backend-community-posts --realestate-use-backend-aliases --enable-realestate-recent-issues-refresh --realestate-recent-issues-ranking-limit 10 --enable-realestate-evidence-logs-refresh --evidence-use-gms-llm --enable-realestate-map-layer-refresh --realestate-map-layer-types sido sigungu --realestate-map-layer-periods week month halfYear
```

이 명령은 `market_facts -> community_crawl -> reaction_snapshots -> recent_issues -> evidence_logs -> map_layers` 순서로 한 번 실행하고 summary JSON을 출력한 뒤 종료합니다. `CRAWL_RUNTIME_ENV=local`은 정책 검토 전 공개 게시판 source를 로컬 연구/시연 범위에서만 실행하기 위한 값입니다. public runtime에서는 해당 source가 skip될 수 있습니다. 서버처럼 계속 켜 둘 때만 같은 옵션에 `serve --enable-realestate-daily-refresh`를 사용합니다.

최신 backend reaction ranking TOP10 기반 SerpApi 최근 이슈 후보 일일 refresh:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:SERPAPI_API_KEY="..."
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main serve --enable-realestate-daily-refresh --enable-realestate-recent-issues-refresh --reaction-window-minutes 1440 --realestate-recent-issues-target-type region --realestate-recent-issues-ranking-limit 10 --serpapi-result-limit 5
```

이 daily step은 `GET /api/realestate/reactions/rankings`의 최신 TOP target을 읽어 target display name과 `issueMix` label로 검색 query를 만들고, 결과를 `content_items` 후보로 전송합니다. 검색 결과 수나 순위는 관심도 지표로 쓰지 않고, 이후 EvidenceLog가 참고할 근거 후보 링크로만 저장합니다. `--realestate-search-targets-jsonl`을 함께 주면 ranking 대신 파일에 정의된 검색 대상을 사용합니다.

EvidenceLog payload 생성:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-evidence-logs --reaction-snapshots-jsonl C:\data\reaction_snapshots.jsonl --evidence-target-id region-daejeon --evidence-window-start 2026-06-11T00:00:00Z --evidence-evaluated-at 2026-06-12T02:00:00Z --evidence-market-facts-jsonl C:\data\market_facts.jsonl --evidence-timeline-events-jsonl C:\data\timeline_events.jsonl --evidence-content-items-jsonl C:\data\recent_issues.jsonl --evidence-similar-windows-jsonl C:\data\similar_windows.jsonl
```

EvidenceLog를 backend로 전송:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main realestate-evidence-logs-push --reaction-snapshots-jsonl C:\data\reaction_snapshots.jsonl --evidence-target-id region-daejeon --evidence-window-start 2026-06-11T00:00:00Z
```

`realestate-evidence-logs(-push)`는 `market_fact`, `timeline_event`, `similar_window`, `search_candidate` 입력이 없으면 해당 근거 부족 caveat을 남깁니다. 기본 summary/tone은 룰 기반 baseline이며, `--evidence-use-gms-llm`을 켜도 EvidenceLog 저장 shape는 유지합니다.

최신 backend snapshot 기반 EvidenceLog 일일 refresh:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main serve --enable-realestate-daily-refresh --enable-realestate-evidence-logs-refresh --reaction-window-minutes 1440 --realestate-evidence-ranking-limit 20 --realestate-evidence-market-fact-limit 20 --realestate-evidence-timeline-limit 20 --realestate-evidence-content-limit 20
```

이 step은 `GET /api/realestate/reactions/rankings`, `GET /api/realestate/targets/{targetId}/market-facts`, `GET /api/realestate/targets/{targetId}/timeline`, `GET /api/realestate/targets/{targetId}/content`를 읽어 룰 기반 EvidenceLog를 만들고, 결과를 `POST /internal/realestate/evidence-logs`에 저장합니다. 최신 ranking이 비어 있으면 target별 market/timeline/content 조회나 추가 provider 호출 없이 `EMPTY` 상태로 끝납니다.

유사 과거 후보까지 매일 EvidenceLog에 붙이는 방법은 두 가지입니다. 이미 만들어 둔 batch/Qdrant 결과 JSON이 있으면 같은 명령에 `--evidence-similar-windows-jsonl <similar-window-output>`을 추가합니다. Qdrant collection과 임베딩 JSON이 준비되어 있으면 `--similar-engine qdrant --embeddings-jsonl <embeddings-output>`을 추가해 daily step 안에서 직접 검색할 수도 있습니다. 두 방식 모두 현재 ranking의 target/window와 맞는 후보만 병합하고, step detail의 `similar_window_count`로 병합 건수를 남깁니다.

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
$env:QDRANT_URL="http://localhost:6333"
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main serve --enable-realestate-daily-refresh --enable-realestate-evidence-logs-refresh --similar-engine qdrant --embeddings-jsonl C:\data\ybf-realestate\embeddings.json --similar-top-n 5 --similar-market-facts-jsonl C:\data\ybf-realestate\market-facts.jsonl
```

이 경로는 daily step 안에서 새 임베딩을 생성하거나 Qdrant에 upsert하지 않습니다. 먼저 `realestate-embeddings`, `realestate-vector-upsert`, `realestate-vector-health`로 임베딩과 collection 상태를 준비해야 합니다.

GMS LLM으로 일일 EvidenceLog summary를 보강하려면 같은 명령에 `--evidence-use-gms-llm --evidence-llm-model gpt-5-mini`를 붙입니다. 이 경우에도 먼저 룰 기반 EvidenceLog를 만들고, LLM 결과는 `summary`, `subtitle`, `tone`만 보강합니다. forbidden copy guardrail에 걸리면 룰 기반 문구를 유지하고 `skipReason=forbidden_copy_detected`를 남깁니다.

지도 레이어 snapshot 일일 refresh:

```powershell
cd C:\agents\YouBuyFirst_RealEstate\pipeline
C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m youbuyfirst_pipeline.main serve --enable-realestate-daily-refresh --enable-realestate-map-layer-refresh --realestate-map-layer-types sido sigungu --realestate-map-layer-periods week month halfYear
```

이 step은 backend의 `POST /internal/realestate/map/layer-snapshots/refresh`를 호출합니다. backend는 `map_features`에 연결된 target별 `apt_trade` market fact를 기간 안에서 첫 관측일/마지막 관측일 평균으로 비교하고, 최신 reaction snapshot의 confidence를 함께 넣어 `map_layer_snapshots`를 생성합니다. 거래 표본이 부족한 target/기간은 새 snapshot을 만들지 않으므로 기존 seed/mock fallback이 명시적으로 남습니다.
