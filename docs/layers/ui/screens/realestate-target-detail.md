# 지역/단지 상세

## Route

- Parent: `realestate-dashboard`
- Route 후보: `/realestate/targets/:targetId`
- 지도 route: `/realestate/map`
- 지도 drilldown route: `/realestate/map/:regionId`
- Child screens: evidence log drawer, source link drawer, similar history panel
- Map child screens: 시군구 drilldown map, selected municipality report panel, future complex coordinate layer

## 화면 목적

사용자가 특정 지역/단지에 대해 사람들이 무엇을 기대하고 걱정하는지, 어떤 시장 사실이 함께 관찰되는지, 비슷한 과거 상황과 이후 흐름이 어땠는지 확인합니다.

## 현재 섹션

- target header: 지역/단지명, type, alias, 데이터 상태
- evaluation summary: 에이전트 평가, 근거 chip, caveat
- reaction snapshot: 기대/우려/중립, mention count, confidence
- issue mix: 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책
- market fact timeline: 실거래, 전세, 매물, 정책, 공급, 뉴스
- source evidence: 제한 snippet, 제목, 링크, 작성 시각, source
- similar history: 유사 과거 반응과 이후 시장 흐름
- data quality: provider/asOf/stale, source skew, 표본 부족

## 지도형 탐색 화면

지역/단지 상세의 핵심 탐색 경험은 한반도 지도 기반 heat layer로 확장할 수 있습니다. 구현 자체는 가능합니다. 다만 정형화된 금융 상품처럼 모든 대상에 같은 주기의 가격이 찍히는 구조가 아니므로, 가격 색상은 항상 데이터 기준일과 표본 수를 같이 보여줘야 합니다.

- 기본 레벨: 전국/시도 경계 지도에서 기간별 변화와 관심도를 색으로 표시
- 기간 선택: 최근 1주, 1개월, 6개월, 1년을 토글로 제공하고 `asOf`와 stale badge를 같이 표시
- 색상 규칙: 국내 사용자 관습을 우선해 `빨강=상승`, `파랑=하락`, 진하기=변화 강도, 회색=표본 부족/데이터 없음
- 확대 흐름: 시도 -> 시군구 -> 읍면동/생활권 -> 단지 순서로 drilldown
- 하이브리드 기준: 전국부터 읍면동/생활권까지는 자체 도식화 heatmap을 쓰고, 특정 동 또는 단지 상세부터는 카카오맵 SDK를 사이트 내부에 내장
- 현재 구현: `/realestate/map`에서 시도를 선택하면 `/realestate/map/:regionId`로 이동하고, 해당 시도의 실제 시군구 경계를 렌더링
- 클릭 동작: 선택 지역의 가격 흐름, 거래 강도, 전세 압력, 공급/청약, 정책/교통 이벤트, 커뮤니티 반응을 side panel에 표시
- 단지 매핑: 법정동 코드, 도로명/지번 주소, 단지명 별칭, 좌표를 묶어 `complex` target과 연결
- 지도 레이어: 가격 변화율, 거래량, 전세 압력, 매물/호가, 커뮤니티 언급량, 정책 이벤트를 별도 toggle로 분리

초기 구현은 전국 시도 단위 정적 heatmap과 시군구 drilldown까지 포함합니다. 이후 법정동/생활권 경계와 단지 좌표 매핑을 추가하는 단계가 적합합니다.

## 지도-리포트 상호작용

- 첫 진입: 지도는 화면 중앙에 단독 배치하고 리포트 패널은 숨김
- 시도 선택: `/realestate/map/:regionId` 상세 지도 route로 이동하고, 같은 stage에서 시군구 경계를 표시
- 시군구 선택: 지도는 왼쪽으로 이동하고 오른쪽에 지역 리포트 패널을 50:50에 가깝게 표시
- 지역 단위: 1차 구현은 KOSTAT 2018 시도 TopoJSON 경계를 사용하며, `regionCode`/`geometryId` 계약으로 실제 지형과 데이터 target을 연결
- 시군구 단위: KOSTAT 2018 시군구 TopoJSON 경계를 asset으로 지연 로드하고, `regionCode` prefix로 하위 지역을 필터링
- 시각 방향: 단순 평면 지도보다 3D surface, dark glass, neon heat layer를 사용해 미래형 관제 지도에 가깝게 표현
- 클릭성: 지도는 화면에서 충분히 크게 보이도록 세로 stage를 키우고, 지역별 hit area를 실제 도형보다 넓게 둠
- heat 표현: 빨강=상승, 파랑=하락, 변화폭이 클수록 더 진하고 밝게 표현해 한눈에 강약을 구분
- 리포트 밀도: 선택 지역 리포트는 언급량 급증, 커뮤니티 source mix, 핵심 쟁점, metric card, 후속 단지 후보까지 세로형 보고서로 제공
- 단지 단위: `/realestate/targets/:targetId` 상세 화면에 카카오맵 SDK 내장 prototype을 붙이고, SDK 비활성화/key missing/test 환경에서는 도식화 fallback으로 marker와 선택 패널을 보여줌
- 내장 지도: 카카오맵 SDK key는 `front/.env.local`의 `VITE_KAKAO_JAVASCRIPT_KEY`에서만 읽고, key missing 상태에서는 mock/stale 배지를 표시
- 단지 marker: `GET /api/realestate/targets/{targetId}/nearby-complexes`를 우선 사용하고 실패/빈 응답이면 fixture로 fallback. `targetId`, 단지명, 주소, 좌표, 가격 흐름, 반응 요약, `provider/asOf/dataStatus/stale`을 함께 표시하며, seed 좌표는 `mock/stale`로 드러냄
- 닫기 동작: 리포트 패널을 닫으면 지도 단독 중앙 상태로 복귀

## 상태와 빈 화면

- loading: header와 snapshot skeleton 분리
- empty: target은 있으나 mention 또는 market fact 없음
- error: source/evidence/timeline 영역별 실패 표시
- stale/mock: provider와 `asOf`를 항상 같이 표시

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `target` | realestate | region/complex 기본 정보 |
| `aliases[]` | realestate | 별칭과 review state |
| `reactionSnapshot` | indicator | target/window 반응 지표 |
| `issueMix[]` | indicator | 쟁점 라벨, share, direction, confidence |
| `timeline[]` | realestate/community | market fact, 뉴스/컬럼, 커뮤니티 이벤트 |
| `evidenceLogs[]` | agent | 평가와 근거 로그 |
| `similarWindows[]` | indicator/agent | 유사 과거 상황 후보 |
| `mapLayers[]` | realestate/indicator | 기간별 지역 heat layer와 표본/stale 상태 |
| `mapLayers[].features[]` | realestate | region code, geometry id, changePct, sampleCount, confidence |
| `municipalityTopologyAsset` | realestate/ui | 상세 지도 진입 시 fetch하는 시군구 경계 asset URL |
| `selectedMunicipalityReport` | realestate/indicator/community | 시군구 선택 시 오른쪽 패널에 표시할 가격 흐름, 커뮤니티 언급, 핵심 쟁점 |
| `reactionGraph.items[]` | indicator/realestate | target graph로 연결된 하위/관련 target과 각 target의 reaction snapshot |
| `nearbyComplexes[]` | realestate | 지도 확대 시 노출할 단지 좌표와 시장 fact 요약 |
| `selectedRegionReport` | realestate/indicator/community | 지도에서 선택한 지역의 가격 흐름, 거래 강도, 전세 압력, 정책 이벤트, 커뮤니티 반응 |
| `embeddedMap` | ui/realestate | 특정 동/단지 상세 단계에서 카카오맵 SDK 로딩 상태, key 상태, marker 목록, 선택 단지 상태 |

현재 구현:

- `GET /api/realestate/targets/{targetId}/reaction-snapshot?windowMinutes=60` 응답을 상세 화면의 `reactionSnapshot`, `issueMix`, `data quality`, `freshness` 입력으로 사용합니다.
- `GET /api/realestate/targets/{targetId}/reaction-graph?direction=out&edgeType=contains&windowMinutes=60` 응답을 시도 -> 시군구 drill-down 목록, 하위 지역별 언급량/쟁점 비교, 관련 리포트 후보 입력으로 사용합니다.
- `GET /api/realestate/targets/{targetId}/market-facts?factType=&limit=` 응답을 실거래, 전세, 매물, 가격지수의 raw fact 상세/검증 입력으로 사용합니다.
- `GET /api/realestate/targets/{targetId}/nearby-complexes?limit=` 응답을 동/단지 상세 내장 지도 marker 입력으로 사용합니다. 화면은 유효한 좌표가 있는 `items[]`를 먼저 그리고, 실패하거나 빈 응답이면 기존 fixture marker를 `mock fallback`으로 유지합니다.
- `GET /api/realestate/targets/{targetId}/content?feed=&limit=` 응답을 해당 지역/단지와 연결된 뉴스, 리포트, 영상, 링크 카드 입력으로 사용합니다.
- `GET /api/realestate/targets/{targetId}/timeline?eventType=&limit=` 응답을 정책, 공급, 교통, 뉴스/컬럼 맥락 이벤트, `market_fact`, `reaction`, `content` 시간축 입력으로 사용합니다. 이벤트는 가격 변화의 직접 원인처럼 쓰지 않고 함께 관찰된 맥락 또는 관측 사실로 표시합니다.
- `GET /api/realestate/targets/{targetId}/evidence-logs?limit=` 응답을 AI 근거 로그 섹션 입력으로 사용합니다. 화면에는 평가 요약, 평가 버전, model/prompt, confidence, caveat, evidence item을 보여주며 내부 추론 전문이나 행동 지시 문구는 표시하지 않습니다.
- 프론트 상세 화면은 route의 `targetId`를 그대로 backend API에 넘깁니다. 예시는 `region-seoul-mapo`, `living-area-gyeonggi-dongtan-station`처럼 `real_estate_targets.id`와 같은 값입니다. API 응답이 있으면 근거 링크 후보를 승인된 content row로 교체하고, 없거나 실패하면 기존 mock evidence를 `원문 확인 필요` 상태로 유지합니다.
- 단지 위치 레이어 1차 구현은 `region-seoul-mapo`, `living-area-gyeonggi-dongtan-station`, `complex-mapo-raemian-prugio`에서 front fixture marker를 사용합니다. 실제 좌표 DB/API 연결 전까지 marker `dataStatus`는 `mock 좌표`로 표시합니다.
- content row는 원문 전문을 복제하지 않고 제목, 출처, URL, 발행일/metric label만 근거 링크 카드에 표시합니다.
- `eventType=market_fact` 항목은 `sourceRefType=market_fact`, `sourceRefId=real_estate_market_facts.id`를 가지며, 제목은 `매매 실거래`, `전월세 실거래`, `매물 수`, `가격지수`처럼 사용자용 라벨로 표시합니다.
- `eventType=reaction` 항목은 `sourceRefType=reaction_snapshot`, `sourceRefId=real_estate_reaction_snapshots.id`를 가지며, 제목은 `커뮤니티 기대 우세`, `커뮤니티 우려 우세`처럼 dominant reaction 중심으로 표시합니다.
- `eventType=news|report|video|link|column` 항목은 `sourceRefType=content`, `sourceRefId=content_items.id`를 가지며, 제목과 제한 snippet만 표시하고 원문 전문은 외부 URL로 보냅니다.
- 응답의 `dominantDirection`, `reactionDirectionRatio`, `mentionDeltaPct`는 리포트 요약과 반응 비율 막대에 사용합니다.
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
- 2026-06-14: 단지 내장 지도 marker를 `nearby-complexes` API 우선 구조로 연결하고, 실패 시 fixture fallback을 유지하는 기준 추가.
- 2026-06-13: 동/단지 상세 카카오맵 SDK 내장 prototype, marker 선택 패널, mock 좌표 fallback 표시 기준 추가.
- 2026-06-13: 전국~동은 자체 도식화 heatmap, 동/단지 상세부터는 카카오맵 SDK 내장 지도로 보는 하이브리드 기준 추가.
- 2026-06-12: 지역/단지 상세 근거 링크 후보를 target content API 우선 live/fallback 구조로 연결.
- 2026-06-01: `/realestate/map` 1차 구현 방향과 지도-리포트 split interaction 추가, 실제 시도 TopoJSON 기반 3D 지도 방향 반영
- 2026-06-01: `/realestate/map/:regionId` 시군구 drilldown route와 지연 로드되는 시군구 경계 asset 계약 추가
- 2026-06-01: 지도 stage 확대, heat 색상 대비 강화, 커뮤니티 언급량/핵심 쟁점 리포트 강화
- 2026-06-01: 지도형 heat layer와 drilldown 구현 방향 추가
- 2026-06-01: 지역/단지 상세 Screen Brief 생성
