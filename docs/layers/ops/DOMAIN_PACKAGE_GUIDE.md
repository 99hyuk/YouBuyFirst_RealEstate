# 도메인 패키지 이름 가이드

이 문서는 부동산 전용 프로젝트에서 작업 영역과 코드 패키지 이름을 구분하기 위한 기준입니다. 작업 영역은 PR 범위와 문서 읽기 경계를 정하는 단위이고, 패키지는 코드 안에서 책임을 나누는 단위입니다.

## 핵심 원칙

- 작업 영역 이름은 PR 범위, 브랜치 이름, Notion 기록, 작업 분배에 사용합니다.
- 코드 패키지는 사용자가 이해하기 쉬운 제품 도메인 이름을 사용합니다.
- 주식 프로젝트의 `stock`, `instrument`, `symbol`, `quote`, `chart candle`, `simulation` 개념을 부동산 모델로 억지 일반화하지 않습니다.
- 부동산의 핵심 모델은 `region`, `complex`, `transaction`, `rent`, `listing`, `policy event`, `market fact`, `reaction snapshot`입니다.
- 다른 작업 영역의 패키지를 바꿔야 하면 구현 PR에 섞지 말고 계약 변경 또는 작은 리네임 PR로 분리합니다.

## 권장 도메인 패키지

Backend 목표 구조:

```text
backend/
  src/main/java/com/youbuyfirst/backend/
    common/          # 공통 유틸
    crawl/           # crawl run 상태와 source 실행 기록
    ingestion/       # 수집 결과 수신, 검증, 저장 orchestration
    post/            # 제한 원문과 게시글 메타데이터
    realestate/      # 지역, 단지, alias, 실거래/전세/매물, 정책 이벤트
    analysis/        # 지역/단지별 반응 방향과 쟁점 판단
    indicator/       # window 집계, 반응 지표, snapshot
    agent/           # 지역/단지 평가, 근거 로그, 유사 과거 비교 설명
    stock/           # legacy stock reference, 후속 삭제 또는 참고 후보
    market/          # legacy quote/chart reference, 부동산 market fact와 섞지 않음
    simulation/      # legacy paper trading reference, 부동산 1차 범위에서 비활성
```

Pipeline 목표 구조:

```text
pipeline/
  src/youbuyfirst_pipeline/
    crawlers/        # 커뮤니티 수집 adapter
    realestate/      # 지역/단지 alias matcher, 부동산 source adapter
    analysis/        # LLM 분석 provider, 쟁점 clustering 후보
    scheduler/       # batch orchestration
    stock/           # legacy stock reference, 후속 삭제 또는 참고 후보
```

Frontend 목표 구조:

```text
front/
  src/
    shared/          # 디자인 시스템, 공통 컴포넌트
    apps/realestate/ # 부동산 대시보드와 지역/단지 상세
    apps/stock/      # legacy stock reference, 후속 삭제 또는 참고 후보
```

## 이름 선택 기준

| 기존/후보 | 목표 이름 | 이유 |
| --- | --- | --- |
| `instrument` | `realestate target`로 즉시 일반화하지 않음 | 주식 종목 식별과 부동산 지역/단지 식별은 비슷하지만 다릅니다. 초반에는 `region`, `complex`를 별도 모델로 둡니다. |
| `stock`, `symbol`, `ticker` | `region`, `complex`, `regionCode`, `complexId`, `legalDongCode` | 부동산 식별자는 지역 법정동 코드와 단지 id 중심입니다. |
| `quote snapshot` | `market fact snapshot` | 실거래, 전세, 매물, 청약, 정책 상태를 provider/asOf/stale와 함께 기록합니다. |
| `chart candle` | `market time series` | 일/주/월 단위 가격, 전세, 매물 흐름을 관찰합니다. |
| `sentiment` | `analysis` | 감성보다 반응 방향과 쟁점 판단을 다룹니다. |
| `metrics` | `indicator` | window 단위 집계와 반응 지표 snapshot을 소유합니다. |
| `paper trading decision` | `evidence-based area evaluation` | 매매 판단이 아니라 지역/단지에 대한 근거 있는 평가를 남깁니다. |

## 작업 영역과 패키지 매핑

| 작업 영역 | 주 소유 패키지 | legacy alias | 비고 |
| --- | --- | --- | --- |
| `realestate` | `realestate` | `data` 일부, `market` 일부 | 지역/단지 식별, market fact, 정책 이벤트를 담당합니다. |
| `community` | `pipeline/crawlers`, `backend/crawl`, `backend/ingestion` 일부, `post` | `crawl` | 수집 입력, source policy, 제한 원문 저장을 담당합니다. |
| `indicator` | `analysis`, `indicator` | `data` 일부 | 지역/단지 반응 분석과 지표화를 담당합니다. 행동 판단은 하지 않습니다. |
| `agent` | `agent` | `agent` | realestate/analysis/indicator 결과를 읽어 근거 로그와 평가를 만듭니다. |
| `ui` | frontend app | `front` | 화면, 디자인 시스템, fixture/API 후보를 담당합니다. |
| `ops` | `docs`, `.github`, Notion, CI/운영 문서 | `ops` | 제품 조율과 운영 기준을 담당합니다. |
| `stock` | `stock` | `data` 일부 | 주식 프로젝트 참고 영역입니다. 부동산 기능 구현에 섞지 않습니다. |
| `market` | `market` | `market` | 주식 quote/chart 참고 영역입니다. 부동산 market fact와 이름을 섞지 않습니다. |
| `simulation` | `simulation` | `trade` | 주식 paper trading 참고 영역입니다. 부동산 1차 범위에서는 비활성입니다. |

## 경계 규칙

- `realestate`: 글과 market fact가 어떤 지역 또는 단지를 말하는지 찾고, 대상 식별자를 관리합니다.
- `community`: 공개 source에서 제한 원문과 메타데이터를 수집합니다.
- `analysis`: 지역/단지 언급을 어떤 반응 방향과 쟁점으로 말하는지 판단합니다.
- `indicator`: 여러 글과 분석 결과를 모아 시간 단위 지표로 만듭니다.
- `agent`: 지표, 시장 사실, 유사 과거 상황을 읽어 사용자용 평가와 근거 로그를 남깁니다.

따라서 지역/단지 alias 매칭을 `analysis`에 넣지 않고, window 집계를 `realestate`에 넣지 않습니다. 이름은 비슷해 보여도 책임은 분리합니다.

## 현재 코드 적용 방식

현재 복제본에는 주식 프로젝트의 `stock`, `instrument`, `market`, `simulation`, `sentiment`, `metrics` 패키지가 남아 있을 수 있습니다. 이 문서의 이름은 앞으로의 목표 기준이며, 기존 주식 패키지는 첫 부동산 정렬 단계에서 삭제하지 않습니다.

실제 정리는 한 PR에 모두 묶지 않습니다.

1. 문서와 작업 영역을 부동산 중심으로 고정합니다.
2. `realestate` 도메인 문서와 패키지 skeleton을 만듭니다.
3. 기존 주식 패키지를 `legacy stock reference`로 분류하고 중복을 확인합니다.
4. 중복이 명확해진 뒤 공통 수집, 제한 원문 저장, 지표 snapshot 구조만 공통화합니다.

DB table 이름은 별도 결정 전까지 유지합니다. 기존 migration 안정성을 위해 package/class 이름 변경과 DB schema 변경은 분리합니다.
