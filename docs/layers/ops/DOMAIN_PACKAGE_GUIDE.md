# 도메인 패키지 이름 가이드

이 문서는 작업 영역과 코드 패키지 이름을 구분하기 위한 기준입니다. 작업 영역은 PR 범위와 문서 읽기 경계를 정하는 단위이고, 패키지는 코드 안에서 책임을 나누는 단위입니다.

## 핵심 원칙

- 작업 영역 이름은 PR 범위, 브랜치 이름, Notion 기록, 작업 분배에 사용합니다.
- 코드 패키지는 사용자가 이해하기 쉬운 제품 도메인 이름을 사용합니다.
- legacy track 이름을 그대로 패키지 이름으로 쓰지 않습니다. 특히 `data`, `front`, `trade`는 코드 패키지명으로 너무 넓거나 현재 제품 책임과 다릅니다.
- 다른 작업 영역의 패키지를 바꿔야 하면 구현 PR에 섞지 말고 계약 변경 또는 작은 리네임 PR로 분리합니다.

## 추천 도메인 패키지

Backend 목표 구조:

```text
backend/
  src/main/java/com/youbuyfirst/backend/
    ingestion/      # 수집 결과 수신, 검증, 저장 orchestration
    crawl/          # crawl run 상태와 source 실행 기록
    post/           # 제한 원문과 게시글 메타데이터
    stock/          # 종목 마스터, 티커, 별칭
    analysis/       # 종목별 반응 방향 판단, bullish/bearish/neutral, 근거
    indicator/      # 30분 집계, 열기 지수, 랭킹, 지표 snapshot
    market/         # 시세/호가, quote cache, WebSocket
    simulation/     # 가상 계좌, 주문, 체결, 포트폴리오
    agent/          # AI 전략 판단, 커뮤니티별 성과 비교, 결정 로그
```

Pipeline 목표 구조:

```text
pipeline/
  src/youbuyfirst_pipeline/
    crawlers/       # 커뮤니티 수집 adapter
    stock/          # 종목/별칭 로딩과 매칭
    analysis/       # LLM 분석 provider, 반응 방향 분류
    scheduler/      # batch orchestration
```

## 이름 선택 기준

| 기존/후보 | 목표 이름 | 이유 |
| --- | --- | --- |
| `instrument` | `stock` | 이 프로젝트에서 사용자가 이해하는 핵심 단어는 종목입니다. |
| `sentiment` | `analysis` | legacy 이름입니다. 목표 용어는 커뮤니티 반응 분석이며, 판단, 근거, confidence까지 포함합니다. |
| `metrics` | `indicator` | 집계 결과가 투자 참고 지표로 쓰입니다. |
| `data` | 패키지명으로 사용하지 않음 | legacy track alias로만 보고, 코드 도메인은 `stock`, `analysis`, `indicator`로 나눕니다. |

## 작업 영역과 패키지 매핑

| 작업 영역 | 주 소유 패키지 | legacy alias | 비고 |
| --- | --- | --- | --- |
| `community` | `pipeline/crawlers`, `backend/crawl`, `backend/ingestion` 일부, `post` | `crawl` | 수집 입력, source policy, 제한 원문 저장을 담당합니다. |
| `stock` | `stock` | `data` 일부 | 종목 master, symbol, alias, 종목 식별을 담당합니다. |
| `indicator` | `analysis`, `indicator` | `data` 일부 | 반응 방향 분석과 지표화를 담당합니다. 매매 판단은 하지 않습니다. |
| `market` | `market` | `market` | 시세/호가, chart candle, provider/cache를 담당합니다. |
| `simulation` | `simulation` | `trade` | 가상 계좌, 주문, 체결, 원장, 포트폴리오를 담당합니다. |
| `agent` | `agent` | `agent` | stock/analysis/indicator/market/simulation 결과를 읽어 전략 판단과 결정 로그를 만듭니다. |
| `ui` | frontend app | `front` | 화면, 디자인 시스템, fixture/API 후보를 담당합니다. |
| `ops` | `docs`, `.github`, Notion, CI/운영 문서 | `ops` | 제품 조율과 운영 기준을 담당합니다. |

## 경계 규칙

- `stock`: 글이 어떤 종목을 말하는지 찾습니다.
- `analysis`: 그 종목을 어떤 반응 방향으로 말하는지 판단합니다.
- `indicator`: 여러 글과 분석 결과를 모아 시간 단위 지표로 만듭니다.
- `agent`: 지표와 시세, 계좌 상태를 읽어 전략적 결정을 내립니다.

따라서 종목 매칭을 `analysis`에 넣지 않고, 30분 집계를 `analysis`에 넣지 않습니다. 이름은 비슷해 보여도 책임은 분리합니다.

## 현재 코드 적용 방식

현재 MVP 코드에는 아직 `instrument`, `sentiment`, `metrics` 패키지가 남아 있을 수 있습니다. 이 문서의 이름은 앞으로의 목표 기준이며, `sentiment`는 후속 리네임 전까지 남아 있는 legacy 구현 이름으로만 봅니다.

실제 리네임은 한 PR에 모두 묶지 않습니다.

1. Backend 도메인 패키지 리네임: `instrument -> stock`, `sentiment -> analysis`, `metrics -> indicator`
2. Pipeline 모듈 리네임: `instruments.py`와 matcher 주변을 `stock` 기준으로 정리
3. 문서/Swagger/API 용어 정리: 사용자 facing 용어는 `커뮤니티 반응`, 문서/기술 설명은 `커뮤니티 반응 데이터`, 단일 분석값은 `반응 방향`, 내부 후보 필드는 `reactionDirection`으로 맞춤

DB table 이름은 별도 결정 전까지 유지합니다. 기존 데이터와 migration 안정성을 위해 package/class 이름 변경과 DB schema 변경은 분리합니다.
