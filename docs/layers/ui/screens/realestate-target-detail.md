# 지역/단지 상세

## Route

- Parent: `realestate-dashboard`
- Route 후보: `/realestate/targets/:targetId`
- 지도 route: `/realestate/map`
- 지도 drilldown route: `/realestate/map/:regionId`
- 지도 선택 진입 query: `/realestate/map/:regionId?selectedTargetId=:targetId&selectedRegionCode=:geometryCode&period=week`
- Child screens: evidence log drawer, source link drawer, similar history panel
- Map child screens: 시군구 drilldown map, selected municipality report panel, future complex coordinate layer

## 화면 목적

사용자가 특정 지역에 대해 어떤 시장 사실이 바뀌었는지, 최근 이슈와 비슷한 과거 상황이 무엇인지 확인합니다. 단지 상세는 좌표, 실거래, 공식 provider key가 연결된 경우에만 보조 상세로 확장합니다. 공개 반응은 있으면 보조 관찰 신호로만 붙입니다.

## 현재 섹션

- target header: 지역명 또는 검증된 단지명, type, alias, 데이터 상태
- evaluation summary: 에이전트 평가, 근거 chip, caveat
- market snapshot: 실거래, 전세, 매물, 공급, 정책, confidence
- issue mix: 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책
- market fact timeline: 실거래, 전세, 매물, 정책, 공급, 뉴스
- source evidence: 제한 snippet, 제목, 링크, 작성 시각, source
- similar history: 유사 과거 시장 상황과 이후 흐름
- data quality: provider/asOf/stale, source skew, 표본 부족
- regional issue briefing: 최근 뉴스/리포트/영상/블로그/공개 커뮤니티 후보를 묶은 AI 지역 브리핑

## 지도형 탐색 화면

지역/단지 상세의 핵심 탐색 경험은 한반도 지도 기반 heat layer로 확장할 수 있습니다. 구현 자체는 가능합니다. 다만 정형화된 금융 상품처럼 모든 대상에 같은 주기의 가격이 찍히는 구조가 아니므로, 가격 색상은 항상 데이터 기준일과 표본 수를 같이 보여줘야 합니다.

- 기본 레벨: 전국/시도 경계 지도에서 기간별 변화와 관심도를 색으로 표시
- 기간 선택: 지도/지역 흐름은 최근 1주, 1개월, 3개월, 6개월, 1년을 제공하고 `asOf`와 stale badge를 같이 표시
- 색상 규칙: 국내 사용자 관습을 우선해 `빨강=상승`, `파랑=하락`, 진하기=변화 강도, 회색=표본 부족/데이터 없음
- 확대 흐름: 시도 -> 시군구 -> 읍면동/생활권 -> 단지 순서로 drilldown
- 하이브리드 기준: 전국부터 읍면동/생활권까지는 자체 도식화 heatmap을 쓰고, 특정 동 또는 단지 상세부터는 카카오맵 SDK를 사이트 내부에 내장
- 현재 구현: `/realestate/map`에서 시도를 선택하면 `/realestate/map/:regionId`로 이동하고, 해당 시도의 실제 시군구 경계와 부모 시도 EvidenceLog 리포트를 함께 렌더링
- 클릭 동작: 선택 지역의 가격 흐름, 거래 강도, 전세 압력, 공급/청약, 정책/교통 이벤트, 보조 공개 반응을 side panel에 표시
- 단지 매핑: 법정동 코드, 도로명/지번 주소, 단지명 별칭, 좌표를 묶어 `complex` target과 연결
- 지도 레이어: 가격 변화율, 거래량, 전세 압력, 매물/호가, 정책 이벤트를 별도 toggle로 분리. 공개 반응 레이어는 필요할 때만 보조 toggle로 둔다.

초기 구현은 전국 시도 단위 정적 heatmap과 시군구 drilldown까지 포함합니다. 이후 법정동/생활권 경계와 단지 좌표 매핑을 추가하는 단계가 적합합니다.

## 지도-리포트 상호작용

- 첫 진입: 지도는 화면 중앙에 단독 배치하고 리포트 패널은 숨김
- 시도 선택: `/realestate/map/:regionId` 상세 지도 route로 이동하고, 같은 stage에서 시군구 경계와 해당 시도 최신 EvidenceLog 기반 리포트를 표시
- 시군구 선택: 지도는 왼쪽으로 이동하고 오른쪽에 지역 리포트 패널을 50:50에 가깝게 표시
- 외부 카드에서 시군구로 바로 진입: `selectedTargetId`, `selectedRegionCode`, `period` query가 있으면 해당 시도 drilldown을 열고 같은 화면에서 해당 시군구 버튼을 선택한 상태로 지도+리포트 패널을 표시
- 지역 단위: 1차 구현은 KOSTAT 2018 시도 TopoJSON 경계를 사용하며, `regionCode`/`geometryId` 계약으로 실제 지형과 데이터 target을 연결
- 시군구 단위: KOSTAT 2018 시군구 TopoJSON 경계를 asset으로 지연 로드하고, `regionCode` prefix로 하위 지역을 필터링
- 시각 방향: 단순 평면 지도보다 3D surface, dark glass, neon heat layer를 사용해 미래형 관제 지도에 가깝게 표현
- 클릭성: 지도는 화면에서 충분히 크게 보이도록 세로 stage를 키우고, 지역별 hit area를 실제 도형보다 넓게 둠
- 확대/이동: 전국 지도와 시군구 상세 지도는 모두 마우스 휠 확대/축소와 드래그 이동을 지원합니다. 경기처럼 하위 지역이 밀집된 지도를 확대해서 개별 지역을 선택할 수 있어야 합니다.
- heat 표현: 빨강=상승, 파랑=하락, 변화폭이 클수록 더 진하고 밝게 표현해 한눈에 강약을 구분
- 리포트 밀도: 선택 지역 리포트는 `/realestate/daily-briefing` 상세 화면의 narrative panel과 관련 근거 ledger 리듬을 참고하되 그대로 복제하지 않는다. 처음 보이는 오른쪽 패널은 `AI 핵심 브리핑`, `기대 지점 3줄`, `우려 지점 3줄`, `AI 분석 리포트`, `선택 기간 등락률`, `관련 뉴스·리포트`로 구성한다. 상승·하락률 숫자는 지도 위가 아니라 `AI 분석 리포트` 본문 첫머리의 큰 수치 박스로 표시하고, 본문은 박스 오른쪽에서 시작해 길어지면 박스 아래로 이어진다. 수치 박스는 선택 기간 라벨과 큰 등락률 숫자만 남기고 하단 보조 라벨을 제거해 숫자 비중을 높인다. 대표 브리핑 카드 본문 전체 폭은 대시보드의 지역·단지 반응처럼 기대/우려를 나누되, 결론이나 행동 권유가 아니라 확인 가능한 관찰 포인트로만 쓴다. 하단 `관련 뉴스·리포트`는 브리핑 본문을 반복하지 않고 가격지수, 실거래, 뉴스/리포트 원문 근거가 쌓이는 자리로 둔다.
- 단지 단위: `/realestate/targets/:targetId` 상세 화면에 카카오맵 SDK 내장 prototype을 붙이고, SDK 비활성화/key missing/test 환경에서는 도식화 fallback으로 marker와 선택 패널을 보여줌
- 내장 지도: 카카오맵 SDK key는 `front/.env.local`의 `VITE_KAKAO_JAVASCRIPT_KEY`에서만 읽고, key missing 상태에서는 `지도 SDK 대기`와 provider/asOf/stale 상태를 표시
- 단지 marker: `GET /api/realestate/targets/{targetId}/nearby-complexes`를 우선 사용하고 실패/빈 응답이면 후보 좌표로 fallback. `targetId`, 단지명, 주소, 좌표, 가격 흐름, 거래 요약, `provider/asOf/dataStatus/stale`을 함께 표시하며, seed 좌표는 `좌표 검증 전`으로 드러냄
- 닫기 동작: 하위 시군구 리포트에서는 하위 선택을 해제해 시도 리포트로 돌아가고, 시도 리포트에서는 전국 지도 단독 상태로 복귀

## 상태와 빈 화면

- loading: header와 snapshot skeleton 분리
- empty: target은 있으나 mention 또는 market fact 없음
- error: source/evidence/timeline 영역별 실패 표시
- stale/insufficient: provider와 `asOf`를 항상 같이 표시하고, 검증 전 좌표나 상세 데이터는 실제값처럼 표현하지 않음

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `target` | realestate | region/complex 기본 정보 |
| `aliases[]` | realestate | 별칭과 review state |
| `marketSnapshot` | realestate | target/window 시장 fact 요약 |
| `reactionSnapshot` | indicator | 보조 공개 반응 지표 |
| `issueMix[]` | indicator | 쟁점 라벨, share, direction, confidence |
| `timeline[]` | realestate/community | market fact, 뉴스/컬럼, 커뮤니티 이벤트 |
| `evidenceLogs[]` | agent | 평가와 근거 로그 |
| `similarWindows[]` | indicator/agent | 유사 과거 상황 후보 |
| `mapLayers[]` | realestate/indicator | 기간별 지역 heat layer와 표본/stale 상태 |
| `mapLayers[].features[]` | realestate | region code, geometry id, changePct, sampleCount, confidence |
| `municipalityTopologyAsset` | realestate/ui | 상세 지도 진입 시 fetch하는 시군구 경계 asset URL |
| `selectedMunicipalityReport` | realestate/indicator/content | 시군구 선택 시 오른쪽 패널에 표시할 가격 흐름, 거래 강도, 핵심 쟁점 |
| `targetGraph.items[]` | realestate/indicator | target graph로 연결된 하위/관련 target과 각 target의 market snapshot |
| `nearbyComplexes[]` | realestate | 지도 확대 시 노출할 단지 좌표와 시장 fact 요약 |
| `selectedRegionReport` | realestate/indicator/content | 지도에서 선택한 지역의 가격 흐름, 거래 강도, 전세 압력, 정책 이벤트, 보조 공개 반응 |
| `embeddedMap` | ui/realestate | 특정 동/단지 상세 단계에서 카카오맵 SDK 로딩 상태, key 상태, marker 목록, 선택 단지 상태 |
| `reportBriefing` | agent | 기존 `EvidenceLog` 확장 입력. AI 핵심 브리핑, caveat, confidence, evidence item을 제공 |
| `officialFacts[]` | realestate | 가격지수, 매매 실거래, 전월세, 공개 지연 상태를 검증 가능한 row로 표시 |
| `comparisonRows[]` | realestate | 시도->시군구, 시군구->생활권/동/단지 후보 비교. 데이터 없으면 `수집 전`으로 남김 |
| `scheduleRows[]` | realestate | 청약, 미분양, 통계 발표, 정책/교통 이벤트 후보 |

현재 구현:

- `GET /api/realestate/targets/{targetId}/market-summary?period=month` 응답을 상세 화면의 `marketSnapshot`, `issueMix`, `data quality`, `freshness` 입력으로 사용합니다.
- `GET /api/realestate/targets/{targetId}/target-graph?direction=out&edgeType=contains&period=month` 응답을 시도 -> 시군구 drill-down 목록, 하위 지역별 시장 fact/쟁점 비교, 관련 리포트 후보 입력으로 사용합니다.
- `GET /api/realestate/targets/{targetId}/market-facts?factType=&limit=` 응답을 실거래, 전세, 매물, 가격지수의 raw fact 상세/검증 입력으로 사용합니다.
- 단지 상세의 `최근 매매 거래` 박스는 `GET /api/realestate/targets/{targetId}/market-facts?factType=apt_trade&limit=5&officialOnly=true`를 사용합니다. 이 박스는 `molit_apt_trade` 같은 공식 공공데이터 fact만 표시하고, `ssafy_home_housedeals` dump를 최신 거래 fallback처럼 보여주지 않습니다. complex target의 공식 거래가 region target에 저장된 경우 backend가 법정동 코드, 단지명, 지번으로 같은 단지의 공식 거래를 찾아 내려줍니다.
- `GET /api/realestate/targets/{targetId}/nearby-complexes?limit=` 응답을 동/단지 상세 내장 지도 marker 입력으로 사용합니다. 화면은 유효한 좌표가 있는 `items[]`를 먼저 그리고, 실패하거나 빈 응답이면 후보 marker를 `좌표 검증 전`으로 표시합니다.
- 공개 원문에서 관측된 단지 후보도 `nearby-complexes` 응답에 `latitude`, `longitude`, `coordinateProvider`, `coordinateAsOf`, `coordinateStatus`가 있어야 카카오맵 marker로 표시합니다. 좌표가 없는 단지 후보는 지도 marker에서 제외하고, 화면에는 좌표 수집 대기 상태로 남깁니다.
- 2026-06-16 MVP 기준 `complex-community-*` seed 단지는 Kakao Local Search로 얻은 후보 좌표를 backend complex API에 저장하고, 화면에서는 `kakao sdk · 지도 좌표 반영` 또는 `좌표 검증 전` 상태를 함께 표시합니다. 이 좌표는 지도 표시용 후보값이며 실거래/단지 정본 좌표 검증이 끝났다는 뜻은 아닙니다.
- `GET /api/realestate/targets/{targetId}/content?feed=&limit=` 응답을 해당 지역/단지와 연결된 뉴스, 리포트, 영상, 링크 카드 입력으로 사용합니다.
- `GET /api/realestate/targets/{targetId}/timeline?eventType=&limit=` 응답을 정책, 공급, 교통, 뉴스/컬럼 맥락 이벤트, `market_fact`, `reaction`, `content` 시간축 입력으로 사용합니다. 이벤트는 가격 변화의 직접 원인처럼 쓰지 않고 함께 관찰된 맥락 또는 관측 사실로 표시합니다.
- `GET /api/realestate/targets/{targetId}/evidence-logs?limit=1` 응답을 AI 근거 로그 섹션 입력으로 사용합니다. 화면에는 평가 요약, 평가 버전, model/prompt, confidence, 한국어 주의 사항, evidence item을 보여주며 내부 추론 전문이나 행동 지시 문구는 표시하지 않습니다.
- 지도 오른쪽 리포트는 UI 우선 단계에서 `EvidenceLog`를 별도 report 테이블 대신 `reportBriefing` 입력으로 사용합니다. 화면 요청 중 AI를 호출하지 않고, batch/pipeline이 생성한 최신 EvidenceLog를 `AI 핵심 브리핑`과 `근거 로그와 한계`에 배치합니다.
- 지도 오른쪽 리포트의 1차 노출 정보 순서는 `지역 헤더 -> AI 핵심 브리핑/기대·우려 -> AI 분석 리포트/선택 기간 등락률 -> 관련 뉴스·리포트`입니다. 백엔드 후보 shape는 더 넓게 유지하되, UI 첫 화면은 많은 정보를 한 번에 담지 않습니다. `officialFacts[]`는 기대·우려 요약, AI 분석 리포트, 관련 뉴스·리포트 ledger의 출처/상태 보조문으로 우선 사용합니다.
- 지도 오른쪽 리포트 첫 화면은 `confidence`, raw caveat code, `AI 근거`, `insufficient` 같은 내부 상태어를 그대로 보여주지 않습니다. 상태가 필요하면 `분석 근거 수집 전`, `공식 데이터 없음`, `공개 지연 가능`처럼 사용자용 표현으로 바꿉니다.
- 지도 오른쪽 리포트 날짜는 선택 기간의 가격지수 `asOf`가 아니라 `리포트 업데이트` 시각입니다. 기간 탭을 `1주`, `1개월`, `1년`으로 바꿔도 리포트 본문과 업데이트 날짜는 최신 기준 하나로 유지하고, 분석 리포트 첫머리의 등락률 박스만 선택 기간 렌즈로 바뀝니다.
- `officialFacts[]`와 `comparisonRows[]`에 데이터가 없으면 임의 수치나 보정값을 만들지 않습니다. 화면은 `공식 데이터 없음`, `수집 전`, `상위 지역만 반영`, `공개 지연 가능` 같은 사용자용 상태로 남깁니다.
- 향후 EvidenceLog item은 `market_fact`, `timeline_event`, `content`, `schedule`, `similar_window`, `reaction`을 구분해 저장합니다. `reaction`은 하단 보조 반응에만 사용하고 리포트 결론이나 지도 색상 원천으로 쓰지 않습니다.
- target별 market fact가 부족하지만 전국 공식 지표가 있는 경우 EvidenceLog는 `national_market_fact` 근거를 함께 포함합니다. 화면은 이를 지역별 가격 사실처럼 단정하지 않고 `전국 지표만 반영` 주의 사항과 함께 보여줍니다.
- EvidenceLog의 `evidenceItems[]` 중 `sourceUrl`이 있는 항목은 AI 근거 로그 안에서도 외부 근거 링크로 렌더링합니다. 링크 칩에는 label, valueText, `sourceId`, `sourceDataStatus`, 발행 시각을 함께 표시해 SerpApi 후보가 `candidate`인지 숨기지 않습니다.
- 프론트 상세 화면은 route의 `targetId`를 그대로 backend API에 넘깁니다. 예시는 `region-seoul-mapo`, `living-area-gyeonggi-dongtan-station`처럼 `real_estate_targets.id`와 같은 값입니다. API 응답이 있으면 근거 링크 후보를 승인된 content row로 교체하고, 없거나 실패하면 `원문 확인 필요` 또는 `수집 전` 상태로 둡니다.
- TOP10에 오른 `region-seoul` 같은 target이 아직 상세 fixture에 없더라도, route `targetId`로 `evidence-logs` API를 조회해 AI 근거 로그를 먼저 보여줍니다. 로그가 있으면 unsupported가 아니라 `실시간 근거 리포트` 상태로 전환하고, 잘못된 지역 mock 리포트로 대체하지 않습니다.
- 단지 위치 레이어 1차 구현은 `region-seoul-mapo`, `living-area-gyeonggi-dongtan-station`, `complex-mapo-raemian-prugio`에서 후보 marker를 사용합니다. 실제 좌표 DB/API 연결 전까지 marker `dataStatus`는 `좌표 검증 전`으로 표시합니다.
- content row는 원문 전문을 복제하지 않고 제목, 출처, URL, 발행일/metric label만 근거 링크 카드에 표시합니다.
- `eventType=market_fact` 항목은 `sourceRefType=market_fact`, `sourceRefId=real_estate_market_facts.id`를 가지며, 제목은 `매매 실거래`, `전월세 실거래`, `매물 수`, `가격지수`처럼 사용자용 라벨로 표시합니다.
- `eventType=reaction` 항목은 `sourceRefType=reaction_snapshot`, `sourceRefId=real_estate_reaction_snapshots.id`를 가지며, 제목은 `커뮤니티 기대 우세`, `커뮤니티 우려 우세`처럼 dominant reaction 중심으로 표시합니다.
- `eventType=news|report|video|link|column` 항목은 `sourceRefType=content`, `sourceRefId=content_items.id`를 가지며, 제목과 제한 snippet만 표시하고 원문 전문은 외부 URL로 보냅니다.
- 응답의 `dominantDirection`, `reactionDirectionRatio`, `mentionDeltaPct`는 보조 공개 반응 영역에만 사용합니다.
- `quality.coverageStatus`, `quality.sourceSkew`, `quality.stale`은 표본 부족, 출처 편중, 수집 지연 배지로 표시합니다.
- snapshot이 없는 target은 `quality.coverageStatus=empty`로 처리하고, 값을 0으로 표시하되 실제 반응이 0이라고 단정하지 않습니다.

## 기획자 확인 필요

- 지역과 단지를 같은 상세 화면에서 처리하되, 단지 상세의 내장 지도/선택 패널이 커질 경우 type별 하위 섹션을 분리할지
- 유사 과거 상황을 기본 노출할지 하위 panel로 둘지
- 평가 문구의 톤을 neutral/dry/watch/sharp 중 어디까지 허용할지
- 지도 경계 데이터의 기준을 행정구역, 법정동, 생활권 중 어디까지 둘지
- 매물/호가 데이터를 공공데이터로만 갈지, 포털/제휴/크롤링 후보를 별도 계약으로 둘지

## 변경 로그

- 2026-06-14: 지역/단지 상세에 `evidence-logs` API 우선 AI 근거 로그 섹션을 연결하고, 비어 있으면 대기 상태를 보여주는 기준 추가.
- 2026-06-22: 시연 MVP 기준을 지역 상세 리포트 우선으로 조정하고, 단지 상세는 좌표/실거래/언급이 검증된 경우 보조 상세로 확장하도록 목적을 갱신.
- 2026-06-15: 상세 fixture가 없는 TOP10 region target도 route `targetId` 기준 EvidenceLog를 조회하고, 로그가 있으면 `실시간 근거 리포트` 상태로 표시하는 기준 추가.
- 2026-06-15: 사용자 화면에 `mock 좌표`, `fixture fallback`을 노출하지 않고 `좌표 검증 전`, `timeline 수집 전`, `지도 SDK 대기` 상태로 표시하도록 보정.
- 2026-06-15: 로컬 상세 fixture의 headline, metric, reaction, timeline, evidence, marker를 화면 fallback으로 쓰지 않고 EvidenceLog/content/timeline/nearby-complex API가 있을 때만 표시하도록 보정. API가 비면 `수집 전/insufficient`로 남깁니다.
- 2026-06-16: 상세/지도 리포트의 EvidenceLog 조회를 최신 1건으로 고정하고, raw caveat code를 한국어 주의 사항으로 변환하도록 기준화.
- 2026-06-16: 지도 drilldown 진입 시 부모 시도 EvidenceLog 리포트를 기본 표시하고, 하위 시군구 클릭 시 같은 패널이 선택 지역 리포트로 교체되도록 상호작용 기준을 갱신.
- 2026-06-24: 대시보드 주간 상승/하락 카드처럼 외부 카드에서 들어오는 `/realestate/map/:regionId?selectedTargetId=:targetId&selectedRegionCode=:geometryCode&period=week` query를 지원해 해당 시군구 지도+리포트 패널을 바로 열도록 기준 추가.
- 2026-06-24: 지도 오른쪽 리포트는 새 report 테이블 없이 기존 EvidenceLog를 확장 입력으로 쓰며, 상승·하락률을 `AI 분석 리포트` 본문 첫머리의 큰 수치 박스로 표시한다. 변화율 라벨은 선택 기간만 한 번 노출하고, 하단 보조 라벨 없이 큰 숫자 중심으로 둔다. 본문은 박스 오른쪽에서 시작해 박스 아래로 자연스럽게 이어지게 둔다. 대표 카드 본문 전체 폭에는 기대 지점/우려 지점을 각각 3줄로 둔다. 본문은 최신 기준 `AI 분석 리포트`로 고정하고, 하단은 `관련 뉴스·리포트` 근거 적재소로 둔다.
- 2026-06-24: 기대/우려와 AI 분석 리포트 본문 글씨를 키워 오른쪽 50% 패널에서도 읽기 편하게 조정한다.
- 2026-06-24: 지도 오른쪽 리포트 첫 화면에서 raw confidence, 내부 근거 상태어, `insufficient` 노출을 제거하고, 날짜는 선택 기간별 기준일이 아니라 `리포트 업데이트` 시각으로 통합한다.
- 2026-06-16: 지역별 market fact가 부족한 target은 한국부동산원 전국 지표를 배경 근거로 붙이되 `전국 지표만 반영` 상태를 표시하는 기준 추가.
- 2026-06-16: 커뮤니티 관측 단지 후보의 `nearby-complexes` 좌표 필드를 backend/pipeline 기준에 추가하고, 카카오맵 marker 표시 조건과 후보 좌표 caveat를 명시.
- 2026-06-14: 단지 내장 지도 marker를 `nearby-complexes` API 우선 구조로 연결하고, 실패 시 후보 marker를 검증 전 상태로 표시하는 기준 추가.
- 2026-06-13: 동/단지 상세 카카오맵 SDK 내장 prototype, marker 선택 패널, mock 좌표 fallback 표시 기준 추가.
- 2026-06-13: 전국~동은 자체 도식화 heatmap, 동/단지 상세부터는 카카오맵 SDK 내장 지도로 보는 하이브리드 기준 추가.
- 2026-06-12: 지역/단지 상세 근거 링크 후보를 target content API 우선 live/fallback 구조로 연결.
- 2026-06-01: `/realestate/map` 1차 구현 방향과 지도-리포트 split interaction 추가, 실제 시도 TopoJSON 기반 3D 지도 방향 반영
- 2026-06-01: `/realestate/map/:regionId` 시군구 drilldown route와 지연 로드되는 시군구 경계 asset 계약 추가
- 2026-06-01: 지도 stage 확대, heat 색상 대비 강화, 커뮤니티 언급량/핵심 쟁점 리포트 강화
- 2026-06-01: 지도형 heat layer와 drilldown 구현 방향 추가
- 2026-06-01: 지역/단지 상세 Screen Brief 생성

## 추가 변경 메모

- 2026-06-15: EvidenceLog item의 `sourceUrl`이 있으면 AI 근거 로그 안에서 SerpApi/content 후보 링크와 candidate/source 상태를 함께 표시합니다.
- 2026-06-22: 경북 상세 지도는 울릉군을 화면용 인셋처럼 본토 가까이 배치합니다. 실제 TopoJSON 원본을 바꾸지 않고 렌더링 좌표만 보정해 본토가 지도 중앙을 더 넓게 쓰도록 합니다.
- 2026-06-22: 시군구 상세 지도는 본토와 섬의 3D 그림자가 서로 겹치지 않도록 전국 지도보다 얕은 extrusion과 drop-shadow를 사용합니다. 지형 구조는 유지하고 그림자 깊이만 줄입니다.
- 2026-06-22: 전국/시군구 지도 stage에 휠 확대/축소, 드래그 이동, 1:1 초기화 컨트롤을 추가합니다. 밀집 지역은 확대 후 라벨과 도형을 선택할 수 있어야 합니다.
- 2026-06-23: 전국/시군구 지도 확대 시 지도 도형 surface만 확대하고 지역명 버튼은 별도 overlay 좌표로 이동해 글씨가 흐릿해지지 않도록 렌더링합니다.
