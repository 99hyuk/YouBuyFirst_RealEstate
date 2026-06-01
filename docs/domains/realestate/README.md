# realestate 도메인

realestate는 부동산 전용 프로젝트의 주 도메인입니다. 기존 YouBuyFirst의 커뮤니티 반응 분석 구조를 재사용하되, 주식 도메인의 종목/시세/모의투자 모델을 부동산에 억지로 맞추지 않습니다.

## 제품 정체성

이 서비스는 지역과 단지에 대한 실제 사람들의 반응, 뉴스/컬럼 이슈, 실거래/전세/매물 같은 시장 사실 데이터를 함께 보여주는 관찰형 분석 서비스입니다. 핵심은 행동 지시가 아니라 관찰, 비교, 근거 기록입니다.

## 1차 대상 모델

| 모델 | 의미 | 예시 필드 |
| --- | --- | --- |
| `region` | 시/구/동/생활권 같은 지역 대상 | `id`, `name`, `type`, `parentId`, `legalCode`, `normalizedName` |
| `complex` | 아파트/주거 단지 대상 | `id`, `regionId`, `name`, `address`, `builtYear`, `householdCount` |
| `realestate alias` | 지역/단지 별칭 | `targetType`, `targetId`, `alias`, `source`, `reviewState` |
| `realestate mention` | 게시글이 언급한 지역/단지 | `postId`, `targetType`, `targetId`, `confidence`, `matchedAlias` |
| `market fact` | 실거래/전세/매물/정책/공급/뉴스 상태 | `targetType`, `targetId`, `factType`, `observedAt`, `provider`, `asOf`, `stale` |
| `reaction snapshot` | window 단위 반응 지표 | `mentionCount`, `expectationScore`, `concernScore`, `issueMix`, `sourceSkew` |
| `evidence log` | 에이전트가 본 근거 기록 | `summary`, `evidence`, `caveats`, `evaluatedAt` |

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
GET /api/realestate/targets/{targetId}/reaction-snapshot
GET /api/realestate/targets/{targetId}/timeline
GET /api/realestate/targets/{targetId}/evidence-logs
GET /api/realestate/sources
POST /internal/realestate/market-facts
```

## 공공데이터와 source 기준

- 국토교통부 아파트 매매 실거래가 자료와 아파트 전월세 실거래가 자료는 공공데이터포털에서 REST/XML API로 제공됩니다.
- 공공데이터포털에는 해당 실거래가 API의 업데이트 주기가 `실시간`으로 표시되지만, 서비스에서는 매일 공시 확정처럼 표현하지 않습니다. 신고/확정일자/원천 공개/우리 수집 시각을 분리합니다.
- 건축HUB 건축물대장정보 서비스는 단지/건물 기본 속성 보강 후보입니다.
- 커뮤니티와 카페 source는 30개 내외 후보를 `crawl_sources` registry에 먼저 쌓고, 정책 검토 전에는 `disabled`로 둡니다.
- 네이버 카페와 다음 카페는 공개 목록 접근이 가능한 경우만 후보로 검토합니다. 로그인, CAPTCHA, 프록시, fingerprint 우회가 필요한 source는 구현하지 않습니다.

## 기존 주식 도메인과의 분리

| 주식 프로젝트 | 부동산 프로젝트 | 처리 |
| --- | --- | --- |
| `stock`, `instrument` | `region`, `complex` | 새 모델로 분리 |
| `symbol`, `ticker` | `regionCode`, `complexId`, `legalDongCode` | 새 식별자 사용 |
| `quote snapshot` | `market fact snapshot` | 실거래/전세/매물/정책 상태로 재정의 |
| `chart candle` | `market time series` | 일/주/월 단위 시장 사실 흐름 |
| `paper trading decision` | `evidence-based area evaluation` | 거래 판단이 아니라 근거 있는 평가 |

## 다음 문서 후보

- `DATA_CONTRACT.md`: region/complex/alias/mention/source/reaction/market fact/evidence log 상세 계약
- `SOURCE_POLICY.md`: 부동산 source별 공개 수집 가능성, 제한 저장 범위, stale 기준
- `screens/` 또는 `docs/layers/ui/screens/`: realestate dashboard와 target detail 화면 기준
