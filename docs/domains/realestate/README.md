# realestate 도메인

realestate는 부동산 전용 프로젝트의 주 도메인입니다. 지역/단지 대상, 시장 사실, 정책 이벤트, alias, 반응 지표, 근거 로그를 부동산 정본 모델로 관리합니다.

## 제품 정체성

이 서비스는 지역과 단지에 대한 실제 사람들의 반응, 뉴스/컬럼 이슈, 실거래/전세/매물 같은 시장 사실 데이터를 함께 보여주는 관찰형 분석 서비스입니다. 핵심은 행동 지시가 아니라 관찰, 비교, 근거 기록입니다.

## 1차 대상 모델

| 모델 | 의미 | 예시 필드 |
| --- | --- | --- |
| `region` | 시/구/동/생활권 같은 지역 대상 | `id`, `name`, `type`, `parentId`, `legalCode`, `normalizedName` |
| `complex` | 아파트/주거 단지 대상 | `id`, `regionId`, `name`, `address`, `builtYear`, `householdCount` |
| `realestate alias` | 지역/단지 별칭 | `targetType`, `targetId`, `alias`, `source`, `reviewState` |
| `realestate mention` | 게시글이 언급한 지역/단지 | `postId`, `targetType`, `targetId`, `confidence`, `matchedAlias` |
| `target edge` | 지역/단지/생활권/정책권 관계 | `fromTargetId`, `toTargetId`, `edgeType`, `confidence`, `reviewState` |
| `market fact` | 실거래/전세/매물/정책/공급/뉴스 상태 | `targetType`, `targetId`, `factType`, `observedAt`, `provider`, `asOf`, `stale` |
| `reaction snapshot` | window 단위 반응 지표 | `mentionCount`, `expectationScore`, `concernScore`, `issueMix`, `sourceSkew` |
| `evidence log` | 에이전트가 본 근거 기록 | `summary`, `evidence`, `caveats`, `evaluatedAt` |

현재 구현된 alias registry는 `real_estate_aliases` 테이블을 사용합니다. 내부 API로 후보/승인 별칭을 upsert하고, 공개 화면과 matcher export는 `approved`이면서 `ambiguous=false`인 별칭만 사용합니다. alias 정규화는 공백과 기호를 제거한 글자/숫자 기준으로 맞추며, matcher는 정규화 키로 찾되 evidence에는 실제 원문에서 잡힌 문자열을 남깁니다.

현재 구현된 target graph는 `real_estate_targets`를 공통 부모로 두고 `real_estate_target_edges`로 관계를 연결합니다. 지역, 단지, 생활권, 정책권을 같은 `targetId` 체계로 묶어 지도 drill-down, 반응 roll-up, 정책 영향권 연결에 사용할 수 있습니다. pipeline은 현재 `approved contains` edge를 읽어 하위 지역/단지 반응을 상위 target snapshot에 합산할 수 있습니다.

현재 구현된 timeline은 `timeline_events`를 상세 리포트용 공개 시간축으로 사용합니다. 승인된 정책/공급/교통 이벤트, `targetId`가 확인된 market fact, window 단위 reaction snapshot, 승인된 content-target link가 같은 `sourceRefType/sourceRefId` 규칙으로 materialize됩니다.

## 핵심 화면 후보

- 요즘 언급 많은 지역/단지
- 실시간 이슈, 뉴스, 컬럼
- 지역/단지별 반응 지표
- 쟁점 비율: 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책
- 실거래/전세/매물 흐름
- 정책/개발/교통 이벤트 타임라인
- 과거 유사 상황과 이후 시장 흐름
- 에이전트 지역/단지 평가와 근거 로그

## API 후보

```text
GET /api/realestate/trending-targets
GET /api/realestate/targets/search?q=
GET /api/realestate/targets/{targetId}/aliases
GET /api/realestate/targets/{targetId}/graph
GET /api/realestate/targets/{targetId}/reaction-snapshot
GET /api/realestate/targets/{targetId}/timeline
GET /api/realestate/targets/{targetId}/evidence-logs
GET /internal/realestate/aliases?reviewState=approved&ambiguous=false
GET /internal/realestate/target-edges?reviewState=approved
POST /internal/realestate/targets
POST /internal/realestate/target-edges
POST /internal/realestate/aliases
POST /internal/realestate/policy-events
GET /api/realestate/sources
POST /internal/realestate/market-facts
```

## 공공데이터와 source 기준

- 국토교통부 아파트 매매 실거래가 자료와 아파트 전월세 실거래가 자료는 공공데이터포털에서 REST/XML API로 제공됩니다.
- 공공데이터포털에는 해당 실거래가 API의 업데이트 주기가 `실시간`으로 표시되지만, 서비스에서는 매일 공시 확정처럼 표현하지 않습니다. 신고/확정일자/원천 공개/우리 수집 시각을 분리합니다.
- 건축HUB 건축물대장정보 서비스는 단지/건물 기본 속성 보강 후보입니다.
- 커뮤니티와 카페 source는 30개 내외 후보를 `crawl_sources` registry에 먼저 쌓고, 정책 검토 전에는 `disabled`로 둡니다.
- 네이버 카페와 다음 카페는 공개 목록 접근이 가능한 경우만 후보로 검토합니다. 로그인, CAPTCHA, 프록시, fingerprint 우회가 필요한 source는 구현하지 않습니다.

## 부동산 정본 모델 기준

| 영역 | 정본 모델 | 기준 |
| --- | --- | --- |
| 대상 | `region`, `complex`, `living_area`, `policy_area` | 모든 화면과 지표는 부동산 target 기준으로 연결 |
| 식별자 | `regionCode`, `complexId`, `legalDongCode`, `targetId` | provider 식별자와 서비스 target id를 분리 |
| 시장 사실 | `market fact`, `market time series` | 실거래/전세/매물/정책 상태를 provider/asOf/stale와 함께 저장 |
| 평가/관심 | `evidence-based area evaluation`, `watchlist` | 거래 판단이 아니라 관찰과 관심 지역 관리로 표현 |

## 다음 문서 후보

- `DATA_CONTRACT.md`: region/complex/alias/mention/source/reaction/market fact/evidence log 상세 계약
- `ERD.md`: 현재 화면과 최종 기획을 기준으로 한 논리 ERD
- `ERD.dbml`: dbdiagram.io에 붙여 넣을 수 있는 DBML ERD
- `ERD.visual-import.sql`: ChartDB/DrawSQL/DBeaver 같은 시각화 도구에 넣기 쉬운 MySQL DDL
- `ERD.visual.html`: 외부 ERD 사이트 입력 제한을 우회하기 위한 로컬 HTML ERD 뷰어. 캔버스 드래그, 관계선/군집 보기 전환, 한글 테이블명, 군집별 설명, 브라우저 편집 모드를 제공합니다.
- `SOURCE_POLICY.md`: 부동산 source별 공개 수집 가능성, 제한 저장 범위, stale 기준
- `screens/` 또는 `docs/layers/ui/screens/`: realestate dashboard와 target detail 화면 기준

로컬 ERD 뷰어는 다음 명령으로 재생성합니다.

```powershell
node tools/build-realestate-erd-visual.mjs
```
