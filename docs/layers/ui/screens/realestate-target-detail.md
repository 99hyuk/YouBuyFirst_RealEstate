# 지역/단지 상세

## Route

- Parent: `realestate-dashboard`
- Route 후보: `/realestate/targets/:targetId`
- 지도 route: `/realestate/map`
- Child screens: evidence log drawer, source link drawer, similar history panel

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
- 클릭 동작: 선택 지역의 가격 흐름, 거래 강도, 전세 압력, 공급/청약, 정책/교통 이벤트, 커뮤니티 반응을 side panel에 표시
- 단지 매핑: 법정동 코드, 도로명/지번 주소, 단지명 별칭, 좌표를 묶어 `complex` target과 연결
- 지도 레이어: 가격 변화율, 거래량, 전세 압력, 매물/호가, 커뮤니티 언급량, 정책 이벤트를 별도 toggle로 분리

초기 구현은 전국 시도 단위 정적 heatmap부터 시작하고, 이후 시군구/법정동 경계 GeoJSON과 단지 좌표 매핑을 추가하는 단계가 적합합니다.

## 지도-리포트 상호작용

- 첫 진입: 지도는 화면 중앙에 단독 배치하고 리포트 패널은 숨김
- 지역 선택: 지도는 왼쪽으로 이동하고 오른쪽에 지역 리포트 패널을 50:50에 가깝게 표시
- 지역 단위: 1차 구현은 KOSTAT 2018 시도 TopoJSON 경계를 사용하며, `regionCode`/`geometryId` 계약으로 실제 지형과 데이터 target을 연결
- 시각 방향: 단순 평면 지도보다 3D surface, dark glass, neon heat layer를 사용해 미래형 관제 지도에 가깝게 표현
- 클릭성: 지도는 화면에서 충분히 크게 보이도록 세로 stage를 키우고, 지역별 hit area를 실제 도형보다 넓게 둠
- heat 표현: 빨강=상승, 파랑=하락, 변화폭이 클수록 더 진하고 밝게 표현해 한눈에 강약을 구분
- 리포트 밀도: 선택 지역 리포트는 언급량 급증, 커뮤니티 source mix, 핵심 쟁점, metric card, 후속 단지 후보까지 세로형 보고서로 제공
- 단지 단위: 현재는 후보 단지 목록만 보여주고, 좌표·별칭 매핑 후 단지 클릭 리포트를 후속 구현
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
| `nearbyComplexes[]` | realestate | 지도 확대 시 노출할 단지 좌표와 시장 fact 요약 |
| `selectedRegionReport` | realestate/indicator/community | 지도에서 선택한 지역의 가격 흐름, 거래 강도, 전세 압력, 정책 이벤트, 커뮤니티 반응 |

## 기획자 확인 필요

- 지역과 단지를 같은 상세 화면에서 처리할지, type별 섹션을 다르게 둘지
- 유사 과거 상황을 기본 노출할지 하위 panel로 둘지
- 평가 문구의 톤을 neutral/dry/watch/sharp 중 어디까지 허용할지
- 지도 경계 데이터의 기준을 행정구역, 법정동, 생활권 중 어디까지 둘지
- 매물/호가 데이터를 공공데이터로만 갈지, 포털/제휴/크롤링 후보를 별도 계약으로 둘지

## 변경 로그

- 2026-06-01: `/realestate/map` 1차 구현 방향과 지도-리포트 split interaction 추가, 실제 시도 TopoJSON 기반 3D 지도 방향 반영
- 2026-06-01: 지도 stage 확대, heat 색상 대비 강화, 커뮤니티 언급량/핵심 쟁점 리포트 강화
- 2026-06-01: 지도형 heat layer와 drilldown 구현 방향 추가
- 2026-06-01: 지역/단지 상세 Screen Brief 생성
