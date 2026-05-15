# 도메인 패키지 이름 가이드

이 문서는 병렬 작업 트랙과 코드 패키지 이름을 구분하기 위한 기준입니다. 트랙은 작업 관리 단위이고, 패키지는 제품 도메인 단위입니다.

## 핵심 원칙

- 트랙 이름은 PR, 브랜치, Notion, 작업 분배에 사용합니다.
- 코드 패키지는 사용자가 이해하기 쉬운 제품 도메인 이름을 사용합니다.
- 트랙 이름을 그대로 패키지 이름으로 쓰지 않습니다. 특히 `data`는 코드 패키지명으로 너무 넓고 모호합니다.
- 다른 트랙의 패키지를 바꿔야 하면 구현 PR에 섞지 말고 계약 변경 또는 작은 리네임 PR로 분리합니다.

## 추천 도메인 패키지

Backend 목표 구조:

```text
backend/
  src/main/java/com/youbuyfirst/backend/
    ingestion/      # 수집 결과 수신, 검증, 저장 orchestration
    crawl/          # crawl run 상태와 source 실행 기록
    post/           # 제한 원문과 게시글 메타데이터
    stock/          # 종목 마스터, 티커, 별칭
    analysis/       # 종목별 분위기 판단, bullish/bearish/neutral, 근거
    indicator/      # 30분 집계, 열기 지수, 랭킹, 지표 snapshot
    market/         # 시세/호가, quote cache, WebSocket
    trade/          # 가상 계좌, 주문, 체결, 포트폴리오
    agent/          # AI 전략 판단, 커뮤니티별 성과 비교, 결정 로그
```

Pipeline 목표 구조:

```text
pipeline/
  src/youbuyfirst_pipeline/
    crawlers/       # 커뮤니티 수집 adapter
    stock/          # 종목/별칭 로딩과 매칭
    analysis/       # LLM 분석 provider, bullish/bearish/neutral 분류
    scheduler/      # batch orchestration
```

## 이름 선택 기준

| 기존/후보 | 목표 이름 | 이유 |
| --- | --- | --- |
| `instrument` | `stock` | 이 프로젝트에서 사용자가 이해하는 핵심 단어는 종목입니다. |
| `sentiment` | `analysis` | 감성뿐 아니라 판단, 근거, confidence까지 포함합니다. |
| `metrics` | `indicator` | 집계 결과가 투자 참고 지표로 쓰입니다. |
| `data` | 패키지명으로 사용하지 않음 | 트랙명으로는 괜찮지만 코드 도메인으로는 너무 넓습니다. |

## 트랙과 패키지 매핑

| 트랙 | 주 소유 패키지 | 비고 |
| --- | --- | --- |
| `crawl` | `pipeline/crawlers`, `backend/crawl`, `backend/ingestion` 일부 | 수집 입력과 실행 상태를 담당합니다. |
| `data` | `stock`, `analysis`, `indicator` | 종목 인식, 분석, 지표화까지 담당합니다. 매매 판단은 하지 않습니다. |
| `market` | `market` | 시세/호가와 quote cache만 담당합니다. |
| `trade` | `trade` | 가상 계좌, 주문, 체결, 포트폴리오를 담당합니다. |
| `agent` | `agent` | data/market/trade 결과를 읽어 전략 판단과 결정 로그를 만듭니다. |
| `front` | frontend app | 화면과 API 연동을 담당합니다. |
| `ops` | `docs`, `.github`, Notion, CI/운영 문서 | 제품 조율과 운영 기준을 담당합니다. |

## 경계 규칙

- `stock`: 글이 어떤 종목을 말하는지 찾습니다.
- `analysis`: 그 종목을 어떤 분위기로 말하는지 판단합니다.
- `indicator`: 여러 글과 분석 결과를 모아 시간 단위 지표로 만듭니다.
- `agent`: 지표와 시세, 계좌 상태를 읽어 전략적 결정을 내립니다.

따라서 종목 매칭을 `analysis`에 넣지 않고, 30분 집계를 `analysis`에 넣지 않습니다. 이름은 비슷해 보여도 책임은 분리합니다.

## 현재 코드 적용 방식

현재 MVP 코드에는 아직 `instrument`, `sentiment`, `metrics` 패키지가 남아 있을 수 있습니다. 이 문서의 이름은 앞으로의 목표 기준입니다.

실제 리네임은 한 PR에 모두 묶지 않습니다.

1. Backend 도메인 패키지 리네임: `instrument -> stock`, `sentiment -> analysis`, `metrics -> indicator`
2. Pipeline 모듈 리네임: `instruments.py`와 matcher 주변을 `stock` 기준으로 정리
3. 문서/Swagger/API 용어 정리: 사용자 facing 용어와 내부 패키지 용어를 맞춤

DB table 이름은 별도 결정 전까지 유지합니다. 기존 데이터와 migration 안정성을 위해 package/class 이름 변경과 DB schema 변경은 분리합니다.
