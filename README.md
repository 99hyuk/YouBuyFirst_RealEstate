# 인간지표 MVP

커뮤니티 게시글을 30분 단위로 수집하고, 종목 언급량과 `bullish / bearish / neutral` 투자 심리를 Spring Boot 중심 파이프라인에 저장하는 MVP입니다.

## 구성

- `backend/`: Spring Boot API, MySQL 저장, Swagger 관리 조회
- `worker/`: Python crawler, Playwright fallback, 종목 별칭 매칭, LLM 감성 분석
- `docker-compose.yml`: MySQL, backend, worker 로컬 실행 환경

## 실행

```bash
docker compose up --build
```

Swagger:

```text
http://localhost:8080/swagger-ui.html
```

관리 API:

```text
GET /admin/crawl-runs
GET /admin/posts
GET /admin/stocks/{symbol}/metrics?market=US
POST /internal/ingestions/community-posts
POST /internal/ingestions/crawl-runs
```

## LLM 설정

`OPENAI_API_KEY`가 있으면 worker가 OpenAI provider를 사용합니다. 없으면 로컬 시연용 `MockLLMProvider`가 사용됩니다.

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

## 종목 마스터

샘플 CSV인 `worker/data/instruments.sample.csv`는 backend Flyway seed에도 들어 있습니다. 국내 전체 종목 + 미국 상장 주식/ETF로 확장할 때는 같은 컬럼 형식의 CSV를 준비하고 `INSTRUMENT_CSV_PATH`를 교체합니다. `NAVER_STOCK_CODES`를 별도로 지정하지 않으면 worker는 CSV 안의 `KR` 종목 전체를 네이버 종토방 수집 대상으로 사용합니다.

```csv
market,symbol,name,aliases,type
US,TSLA,Tesla,테슬라|TSLA,STOCK
```

## 테스트

로컬에 Maven/Python이 있으면:

```bash
cd backend && mvn test
cd worker && pip install -e .[test] && pytest
```

Docker로 실행하려면:

```bash
docker run --rm -v "${PWD}/backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn test
docker run --rm -v "${PWD}/worker:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] && pytest"
```

## 에이전트/PR 작업 흐름

새 채팅이나 다른 에이전트는 먼저 [AGENTS.md](AGENTS.md), [docs/CURRENT_HANDOFF.md](docs/CURRENT_HANDOFF.md), [docs/FINAL_PRODUCT_PLAN.md](docs/FINAL_PRODUCT_PLAN.md), [docs/CONTEXT.md](docs/CONTEXT.md)를 읽고 시작합니다. 작업은 `docs/work-units/`의 문서 하나와 PR 하나로 쪼개는 것을 기본 규칙으로 둡니다.
