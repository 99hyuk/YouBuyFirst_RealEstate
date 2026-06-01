# 부동산 평가 카피 가이드

이 문서는 지역/단지 상세 화면에 노출되는 짧은 평가 문구의 기준을 정리합니다. 이 카피는 행동 지시가 아니라, 반응 지표와 시장 사실 데이터를 기반으로 한 관찰 요약입니다.

## 적용 위치

- 지역/단지 상세 첫 화면의 상단 평가 문구
- 에이전트 근거 로그 요약
- 유사 과거 상황 비교 요약
- 대시보드의 짧은 상태 라벨

화면 표현 기준은 `docs/layers/ui/screens/realestate-target-detail.md`가 소유합니다.

## 입력 근거

최소 2개 이상의 독립 근거가 같은 방향을 가리킬 때 강한 톤을 사용합니다.

| 근거 묶음 | 예시 |
| --- | --- |
| 커뮤니티 반응 | 언급량 변화, 기대/우려 비율, issueMix |
| 시장 사실 | 실거래, 전세, 매물, 공급, 정책, provider/asOf/stale |
| 이벤트 | 교통, 개발, 재건축, 청약, 대출, 학군, 정책 변화 |
| 출처 품질 | 표본 수, source 다양성, source skew, 수집 지연 |
| 유사 과거 | 비슷한 반응과 이후 시장 흐름 |

입력은 숫자와 출처가 있어야 합니다. 확인되지 않은 값은 `unknown`, `not_available`, `mock`으로 구분합니다.

## 톤

기본 톤은 `차분한 관찰 브리핑`입니다. 재미있는 표현은 가능하지만, 특정 행동을 부추기거나 미래를 단정하면 안 됩니다.

허용:

- `기대는 교통에 몰렸고, 우려는 전세에 몰렸습니다`
- `언급은 늘었지만 market fact는 아직 확인이 필요합니다`
- `표본은 충분하지만 한 source에 편중되어 있습니다`
- `비슷한 과거 사례와 흐름이 다르게 나타납니다`

금지:

- 특정 행동을 하라는 식으로 말합니다.
- 가격 상승, 수익, 청약 성공을 단정합니다.
- 사용자의 판단이나 행동을 조롱합니다.
- 근거 없이 강한 결론만 남깁니다.

## 강도 단계

| 톤 | 조건 | 예시 방향 |
| --- | --- | --- |
| `neutral` | 데이터가 엇갈리거나 근거가 약함 | `근거가 엇갈려 방향 판단은 보류` |
| `dry` | 약한 변화 또는 단순 상태 | `관심은 늘었지만 확인할 시장 사실이 부족함` |
| `sharp` | 여러 근거가 같은 경고 방향 | `우려는 전세에 몰렸고, 표본도 충분함` |
| `watch` | 행동 지시 없이 주의 깊게 볼 상태 | `정책 이벤트 이후 반응이 빠르게 바뀌는 중` |

## 생성 규칙

1. 먼저 reaction snapshot, market fact, issueMix, source coverage를 확인합니다.
2. 데이터가 부족하면 강한 문구를 만들지 않습니다.
3. 근거가 2개 이상 같은 방향이면 `sharp` 또는 `watch` 후보를 만듭니다.
4. 행동 지시, 가격 단정, 개인 공격 표현을 필터링합니다.
5. 문구에는 가능한 한 근거 chip을 함께 붙입니다.
6. 커뮤니티 원문 톤은 서비스 판단과 분리해 표시합니다.

## API 후보

후보 endpoint:

- `GET /api/realestate/targets/{targetId}/evaluation`
- 또는 target detail 응답 안의 `evaluation` 필드

응답 후보:

| 필드 | 설명 |
| --- | --- |
| `tone` | `neutral`, `dry`, `sharp`, `watch` |
| `summary` | 상단 평가 문구 |
| `subtitle` | 짧은 보조 설명 |
| `evidence[]` | 근거 chip 목록 |
| `caveats[]` | 표본 부족, source skew, stale 등 주의점 |
| `dataQuality` | `complete`, `partial`, `mock`, `stale`, `insufficient` |
| `asOf` | 근거 데이터 기준 시각 |
| `sourceBreakdown` | 어떤 도메인 데이터가 쓰였는지 |
| `disclaimer` | 관찰형 분석이라는 고지 |

예시:

```json
{
  "tone": "watch",
  "summary": "기대는 교통에 몰렸고, 우려는 전세에 몰렸습니다.",
  "subtitle": "최근 7일 언급량은 늘었지만 실거래 데이터는 지연 상태입니다.",
  "dataQuality": "partial",
  "asOf": "2026-06-01T09:30:00+09:00",
  "evidence": [
    {
      "label": "교통 쟁점",
      "value": "34%",
      "source": "indicator",
      "severity": "expectation"
    },
    {
      "label": "전세 우려",
      "value": "26%",
      "source": "indicator",
      "severity": "concern"
    }
  ],
  "caveats": ["market_fact_stale"],
  "disclaimer": "특정 매수, 매도, 청약, 대출 행동을 권유하지 않는 관찰형 분석입니다."
}
```
