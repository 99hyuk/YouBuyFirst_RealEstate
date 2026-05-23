# 너나사 (YouBuyFirst) MVP

커뮤니티 게시글을 30분 단위로 수집하고, 종목 언급량과 `bullish / bearish / neutral` 투자 심리를 Spring Boot 중심 파이프라인에 저장하는 MVP입니다.

## 구성

- `backend/`: Spring Boot API, MySQL 저장, Swagger 관리 조회
- `pipeline/`: Python crawler/analysis pipeline, Playwright fallback, 종목 별칭 매칭, LLM 감성 분석
- `docker-compose.yml`: MySQL, backend, pipeline 로컬 실행 환경

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

`OPENAI_API_KEY`가 있으면 pipeline이 OpenAI provider를 사용합니다. 없으면 로컬 시연용 `MockLLMProvider`가 사용됩니다.

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

## 종목 마스터

샘플 CSV인 `pipeline/data/instruments.sample.csv`는 backend Flyway seed에도 들어 있습니다. 국내 전체 종목 + 미국 상장 주식/ETF로 확장할 때는 같은 컬럼 형식의 CSV를 준비하고 `INSTRUMENT_CSV_PATH`를 교체합니다. `NAVER_STOCK_CODES`를 별도로 지정하지 않으면 pipeline은 CSV 안의 `KR` 종목 전체를 네이버 종토방 수집 대상으로 사용합니다.

```csv
market,symbol,name,aliases,type
US,TSLA,Tesla,테슬라|TSLA,STOCK
```

## 수집 소스 정책

pipeline은 crawler adapter를 실행하기 전에 소스 상태와 실행 환경을 확인합니다. 현재 MVP 소스인 `NAVER`, `FMKOREA`는 공개 검토 전까지 `local-research-only`로 취급합니다.

상태 의미:

- `enabled`: local/public 환경에서 실제 수집 가능
- `local-research-only`: `CRAWL_RUNTIME_ENV=local`일 때만 실제 수집 가능
- `public-demo-only`: 실제 외부 요청 금지, fixture/sample 데이터만 사용
- `disabled`: 실제 외부 요청 금지

`CRAWL_RUNTIME_ENV`가 없거나 알 수 없는 값이면 `public`처럼 처리합니다. 공개 환경에서 값을 빠뜨렸을 때 외부 요청이 나가지 않게 하기 위한 fail-closed 기본값입니다. 로컬에서 실제 수집을 돌리려면 아래처럼 명시합니다.

```bash
CRAWL_RUNTIME_ENV=local
```

## 테스트

로컬에 Maven/Python이 있으면:

```bash
cd backend && mvn clean test
cd pipeline && pip install -e .[test] && pytest
```

Docker로 실행하려면:

```bash
docker run --rm -v "${PWD}/backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn clean test
docker run --rm -v "${PWD}/pipeline:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] && pytest"
```

## 에이전트/PR 작업 흐름

새 채팅이나 다른 에이전트는 [AGENTS.md](AGENTS.md)와 [docs/current/HANDOFF.md](docs/current/HANDOFF.md)의 필요한 섹션만 확인하고 시작합니다. 트랙이 명확하면 관련 도메인/layer의 `AGENTS.md`를 먼저 보고, 세부 색인이 필요할 때만 README를 엽니다. 제품 방향, Git/PR 규칙, 트랙 경계가 필요할 때만 관련 문서를 좁게 열며, 작업은 작은 PR 하나로 쪼개는 것을 기본 규칙으로 둡니다.
