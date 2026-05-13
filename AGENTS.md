# 에이전트 작업 가이드

이 저장소는 너나사 (YouBuyFirst) 최종 제품을 단계적으로 구현합니다. `main`에 올라간 현재 실행 기반은 커뮤니티 크롤링/감성 ingestion MVP이고, 이후 작업은 `docs/workstreams/`의 병렬 트랙 단위로 나눠 진행합니다.

## 제품 목표

너나사 (YouBuyFirst)는 커뮤니티 심리, 종목별 언급량, 시세/호가, 모의투자 에이전트를 결합해 “개미 심리를 읽는 투자 참고 서비스”를 만드는 프로젝트입니다.

현재 구현된 기반은 네이버 종토방과 에펨코리아 주식 게시판에서 신규 글을 수집하고, 국내 주식과 미국 상장 주식/ETF 언급을 인식한 뒤, 각 언급을 `bullish`, `bearish`, `neutral`로 분류해 Spring Boot 백엔드에 저장하는 ingestion 파이프라인입니다.

새 채팅에서 맡는 일은 전체 제품 중 하나의 트랙입니다. 먼저 사용자의 요청이 어느 트랙인지 정하고, 해당 트랙 문서를 읽은 뒤 그 범위 안에서만 작업합니다.

## 현재 아키텍처

- `backend/`: Spring Boot 3.3, Java 21, JPA, Flyway, MySQL, Swagger
- `worker/`: Python worker, APScheduler, HTTPX, BeautifulSoup, Playwright fallback, OpenAI provider abstraction
- `docker-compose.yml`: local MySQL + backend + worker runtime

## 범위 제한

- 담당 트랙과 명시 요청 없이 OCR 자산 연동, 실거래, 로그인/보안, 운영 배포를 추가하지 않습니다.
- 프론트 작업은 `frontend-experience` 트랙에서만 진행합니다.
- 시세, 모의투자, 에이전트 작업은 `market-simulation-engine` 트랙에서만 진행합니다.
- CAPTCHA 우회, 로그인 세션 크롤링, 프록시 회전, fingerprint 위장은 하지 않습니다.
- 공개 HTTP 수집을 우선하고, Playwright는 렌더링 fallback으로만 사용합니다.
- 저장 원문은 제목, 본문 일부, URL, 작성자 해시, 작성 시각, 원문 해시로 제한합니다.

## 검증 명령

Backend:

```bash
docker run --rm -v "${PWD}/backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn clean test
```

Worker:

```bash
docker run --rm -v "${PWD}/worker:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] && pytest"
```

Local app:

```bash
docker compose up --build -d
docker compose ps
```

Swagger:

```text
http://localhost:8080/swagger-ui.html
```

## 브랜치와 PR 규칙

작업 하나는 브랜치 하나와 PR 하나로 처리합니다. 기능 하나, 버그 하나, 문서 정리 하나, 인프라 변경 하나를 한 PR에 담습니다.

```text
codex/<short-task-name>
```

병렬 작업은 `docs/workstreams/README.md`의 다섯 트랙 중 하나로 구분합니다.

- `community-data-platform`: 커뮤니티 수집, 소스 어댑터, 종목별 수집 타깃, 수집 정책
- `signal-intelligence`: 종목 인식, 감성 분석, 열기 지수, 커뮤니티별 수익률 비교
- `market-simulation-engine`: 시세/호가, Redis quote cache, 모의투자, AI 에이전트
- `frontend-experience`: 사용자 대시보드, UI 상태, mock data, API 연동, 차트
- `product-planning-ops`: 기획 조율, 작업 분리, 문서, Notion, PR/CI, 배포 정책

다른 채팅에서 작업을 시작하면 담당 트랙 문서를 먼저 읽고, 가능하면 해당 트랙 파일만 수정합니다.
PR에는 담당 트랙에 맞는 작업 트랙 `track:*` 라벨을 붙이고, Notion 작업 카드에도 `트랙` 값을 채웁니다.
작업 타입은 `type:*` 라벨로 표시합니다. 실제로 건드린 코드나 문서 표면은 개발 영역 `area:*` 라벨로 표시하되, 필요할 때만 붙입니다.
프론트 작업은 `frontend-experience` 트랙으로 처리하고, `track:frontend` 라벨을 붙입니다. 화면 파일을 직접 바꾸면 `area:frontend`도 함께 붙입니다.
`market-simulation-engine` 작업은 필요하면 `market-data`, `simulation-core`, `agent-runtime` lane으로 더 나누어 진행합니다.
의존이 적은 작업은 단위 테스트 후 `main`으로 바로 PR을 보냅니다. 결합이 강한 작업만 짧은 수명의 `track/*` 브랜치에서 통합 테스트 후 `main`으로 보냅니다.

PR을 열기 전:

1. `docs/CONTEXT.md`를 읽습니다.
2. `docs/CURRENT_HANDOFF.md`를 읽습니다.
3. `docs/DOCUMENTATION_GUIDE.md`에서 매번 읽을 문서와 검색용 기록을 구분합니다.
4. `docs/GIT_CONVENTION.md`를 읽습니다.
5. `docs/LABEL_GUIDE.md`에서 GitHub 라벨과 Notion 태그 의미를 확인합니다.
6. 병렬 작업이면 `docs/workstreams/README.md`와 담당 트랙 문서를 읽습니다.
7. 문제가 발생했거나 반복될 가능성이 있으면 `docs/TROUBLESHOOTING_GUIDE.md`를 읽고 Notion 트러블슈팅 DB에 기록합니다.
8. 필요한 경우 `docs/work-units/`에 작업 단위 문서를 만들거나 갱신합니다.
9. 관련 테스트를 실행합니다.
10. 작업 상태나 범위가 바뀌면 `docs/CURRENT_HANDOFF.md`와 `docs/TASKS.md`를 갱신합니다.
11. `git`과 `gh`로 직접 push, PR 생성, 라벨 지정, CI 확인을 수행합니다.

무관한 backend, worker, infra, product-scope 변경을 한 PR에 섞지 않습니다.

PR 제목은 `[트랙][타입] 명사형 요약`으로 씁니다. 예: `[product][docs] 에이전트 가이드와 PR 문장 정리`. `~한다`, `~했다`, `~함`처럼 동사형이나 축약형으로 끝내지 않습니다.

PR 본문과 Notion 작업 카드는 같은 카드형 흐름으로 씁니다: 한눈에 보기, 바뀐 내용, 리뷰 가이드, PR 범위, 검증 결과, 리스크와 후속 작업, Notion 기록, 라벨/태그 참고. 검증은 명령어보다 사람이 읽기 쉬운 결과를 먼저 적습니다.

트러블슈팅은 작업일지보다 자세히 남깁니다. CI, Docker, GitHub, Notion, 외부 API, 인증, 환경 변수, 반복 가능성이 있는 문제는 Notion 트러블슈팅 DB에 `증상`, `발생 맥락`, `조사 과정`, `원인`, `해결`, `검증`, `재발 방지`를 카드형으로 기록합니다.

## 참고 문서

- 최종 제품 기획: `docs/FINAL_PRODUCT_PLAN.md`
- 현재 MVP 범위: `docs/PROJECT_BRIEF.md`
- 현재 인수인계 상태: `docs/CURRENT_HANDOFF.md`
- 문서 구조와 읽기 우선순위: `docs/DOCUMENTATION_GUIDE.md`
- 트러블슈팅 기록 기준: `docs/TROUBLESHOOTING_GUIDE.md`
- 크롤링/공개 배포 리스크 사례: `docs/LEGAL_RISK_CASES.md`
- 라벨/태그 사전: `docs/LABEL_GUIDE.md`
- 병렬 작업 트랙: `docs/workstreams/README.md`
- Git/PR 컨벤션: `docs/GIT_CONVENTION.md`
- 작업 방식: `docs/WORKFLOW.md`
