# Git/PR 컨벤션

이 저장소는 사용자가 직접 스크립트를 실행하는 흐름을 쓰지 않습니다. Codex 또는 작업 에이전트가 `git`과 `gh`를 직접 사용해 브랜치 생성, 커밋, push, PR 생성, CI 확인, merge를 처리합니다.

## 기본 원칙

- PR 하나는 기능 하나, 버그 하나, 문서 정리 하나, 인프라 변경 하나만 담습니다.
- 큰 기능은 반드시 여러 PR로 쪼갭니다.
- PR 설명과 커밋 본문은 한국어로 작성합니다.
- 코드 식별자, 명령어, API 경로, 파일명은 원문 그대로 씁니다.
- `main`에 직접 push하지 않습니다. 항상 `codex/<작업명>` 브랜치를 사용합니다.
- CI 통과 전에는 merge하지 않습니다.

## 브랜치 이름

기본 형식:

```text
codex/<short-task-name>
```

병렬 작업 트랙이 분명하면 브랜치 이름 앞부분에 트랙을 드러냅니다.

예시:

```text
codex/data-naver-target-scheduler
codex/signal-community-alpha-agent
codex/market-quote-cache
codex/frontend-dashboard-shell
codex/product-track-branch-strategy
```

트랙별 권장 prefix:

- `data-`: `community-data-platform`
- `signal-`: `signal-intelligence`
- `market-`: `market-simulation-engine`
- `frontend-`: `frontend-experience`
- `product-`: `product-planning-ops`

## 트랙 브랜치 전략

기본은 작은 PR을 `main`에 자주 통합하는 방식입니다.

- 의존이 적은 작업은 `codex/<prefix>-<task>` 브랜치에서 작업하고, 관련 단위 테스트와 검증을 통과하면 `main`으로 PR을 보냅니다.
- API schema, DB migration, fixture, mock response 같은 공통 계약은 가능한 한 먼저 `main`에 넣습니다.
- 아직 사용자에게 노출하면 안 되는 기능은 feature flag, mock mode, disabled default로 숨깁니다.

결합이 강한 작업만 짧은 수명의 `track/*` 브랜치를 씁니다.

- 예: `track/frontend-dashboard`, `track/market-quotes`
- 하위 작업은 `codex/<prefix>-<task>` 브랜치에서 만들고, PR base를 해당 `track/*` 브랜치로 둡니다.
- `track/*` 브랜치는 2-4개 PR, 3-5일 안에 `main`으로 통합하는 것을 목표로 합니다.
- `track/*` 브랜치가 길어지면 통합 리스크가 뒤로 밀리므로 범위를 줄이거나 계약 PR을 먼저 `main`에 넣습니다.
- `track/*`에서 `main`으로 통합하기 전에는 해당 트랙 테스트와 필요한 smoke test를 실행합니다.

## PR 제목 규칙

형식:

```text
[트랙][타입] 명사형 요약
```

예시:

```text
[data][feat] 커뮤니티 게시글 중복 저장 방지
[data][fix] 에펨코리아 게시글 시간 파싱 보정
[product][docs] PR 크기와 라벨 규칙 정리
[product][infra] 백엔드와 워커 테스트 워크플로 분리
```

첫 번째 태그는 작업 트랙, 두 번째 태그는 작업 타입입니다. 제목은 가능한 한 `~한다`, `~했다`, `~함` 대신 명사형으로 끝냅니다. GitHub 라벨과 Notion 작업명도 같은 요약을 쓰면 추적하기 쉽습니다.

## 작업 타입 태그

- `[feat]`: 사용자나 시스템의 새 동작 추가
- `[fix]`: 버그 수정
- `[docs]`: 문서만 변경
- `[test]`: 테스트 추가 또는 테스트 구조 변경
- `[refactor]`: 동작 변경 없는 구조 개선
- `[infra]`: Docker, CI, 배포, 개발 환경
- `[data]`: 종목 마스터, seed, fixture 같은 데이터 변경
- `[chore]`: 기타 유지보수

## 작업 트랙 태그

- `[data]`: `community-data-platform`
- `[signal]`: `signal-intelligence`
- `[market]`: `market-simulation-engine`
- `[frontend]`: `frontend-experience`
- `[product]`: `product-planning-ops`

## 개발 영역 태그

- `[backend]`: Spring Boot, DB schema, API, JPA
- `[worker]`: Python crawler, matcher, LLM provider
- `[ci]`: GitHub Actions, 테스트 실행 환경
- `[docs]`: README, 기획, 작업 문서
- `[process]`: 작업 방식, 컨벤션, 인수인계
- `[data]`: 종목 마스터, fixture, seed
- `[runtime]`: Docker Compose, 환경 변수, 로컬 실행
- `[frontend]`: 사용자 화면, 대시보드, UI 상태, mock 화면

## GitHub 라벨 규칙

PR을 만들 때 제목 태그와 같은 의미의 작업 트랙 `track:*`, 작업 타입 `type:*` 라벨을 붙입니다. 개발 영역 `area:*`는 실제 파일이나 리뷰 경로를 드러낼 때만 붙이는 보조 라벨입니다.

작업 타입 라벨:

- `type:feat`
- `type:fix`
- `type:docs`
- `type:test`
- `type:refactor`
- `type:infra`
- `type:data`
- `type:chore`

작업 트랙 라벨:

- `track:data`: `community-data-platform`
- `track:signal`: `signal-intelligence`
- `track:market`: `market-simulation-engine`
- `track:frontend`: `frontend-experience`
- `track:product`: `product-planning-ops`

개발 영역 라벨:

- `area:backend`
- `area:worker`
- `area:ci`
- `area:docs`
- `area:process`
- `area:data`
- `area:runtime`
- `area:frontend`

크기 라벨:

- `size:XS`: 1-2개 파일, 아주 작은 수정
- `size:S`: 3-5개 파일, 한 맥락의 작은 변경
- `size:M`: 6-10개 파일, 리뷰 가능한 단일 작업
- `size:L`: 11개 이상 파일. 원칙적으로 분리하고, 예외 사유를 PR 설명에 적습니다.

## PR 크기 기준

- 선호: 5개 파일 이하
- 허용: 10개 파일 이하
- 11개 이상이면 분리 가능성을 먼저 검토합니다.
- backend와 worker를 동시에 바꾸는 PR은 계약 변경처럼 함께 배포되어야 할 때만 허용합니다.
- 문서와 테스트는 구현 PR에 함께 포함할 수 있지만, 독립 문서 정리는 별도 PR로 분리합니다.

## 커밋 메시지 규칙

커밋 제목은 PR 제목과 같은 형식을 씁니다.

```text
[트랙][타입] 명사형 요약
```

커밋 본문이 필요하면 한국어로 씁니다.

```text
[data][fix] 에펨코리아 시간 파싱 보정

상대 시간과 당일 시각 표기를 KST 기준으로 정규화한다.
기존 fixture를 확장해 중복 URL 제거도 함께 검증한다.
```

## PR 본문 규칙

PR 본문은 다음을 반드시 포함합니다.

- 무엇을 바꿨는지
- 어떤 트랙의 작업인지
- 리뷰어가 먼저 볼 곳
- 이 PR에 포함한 것과 제외한 것
- 검증 결과
- 남은 리스크
- 후속 작업이 있다면 명시
- Notion 기록 여부
- 트러블슈팅이 있었다면 상세 기록 링크

PR 본문은 Notion 작업 카드와 같은 카드형 순서를 따릅니다. PR #7처럼 첫 화면에서 의도와 상태가 보여야 합니다.

1. `🧭 한눈에 보기`
2. `🧩 바뀐 내용`
3. `🔎 리뷰 가이드`
4. `📌 PR 범위`
5. `✅ 검증 결과`
6. `⚠️ 리스크와 후속 작업`
7. `🗂️ Notion 기록`
8. `🏷️ 라벨/태그 참고`

검증 섹션은 명령어 목록만 붙이지 않습니다. 먼저 사람이 읽을 수 있는 문장으로 무엇을 확인했고 결과가 어땠는지 씁니다. 필요한 명령어는 `<details>` 블록 안에 접어두거나, 결과 문장 뒤에 보조 정보로 둡니다.

트러블슈팅 섹션에는 짧은 결론과 링크만 남깁니다. CI, Docker, GitHub, Notion, 외부 API, 인증, 환경 변수처럼 반복될 수 있는 문제는 `docs/TROUBLESHOOTING_GUIDE.md` 형식으로 Notion 트러블슈팅 DB에 자세히 기록합니다.

좋은 예:

```text
- Backend는 Docker Maven 컨테이너에서 `mvn clean test`로 실행했고, 통합 테스트 2개가 통과했습니다.
- Worker는 Python 3.10 컨테이너에서 의존성을 설치한 뒤 `pytest`를 실행했고, 테스트 4개가 통과했습니다.
- Docker Compose로 MySQL, backend, worker가 모두 정상 기동되는 것을 확인했습니다.
```

피해야 할 예:

```text
- docker run --rm ...
- docker compose up --build -d
- git diff --check
```

## Merge 규칙

- CI가 모두 통과하면 Codex가 사용자를 대신해 merge할 수 있습니다.
- 기본 merge 방식은 squash merge입니다.
- merge 제목과 본문은 한국어로 정리합니다.
- merge 후 브랜치는 삭제합니다.
- merge 후 Notion 작업일지에 PR 카드 형태로 핵심 변경과 검증 결과를 남깁니다.
