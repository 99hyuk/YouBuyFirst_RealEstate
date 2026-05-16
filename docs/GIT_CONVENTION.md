# Git/PR 컨벤션

이 저장소는 사용자가 직접 스크립트를 실행하는 흐름을 쓰지 않습니다. Codex 또는 작업 에이전트가 `git`과 `gh`를 직접 사용해 브랜치 생성, 커밋, push, PR 생성, CI 확인, merge를 처리합니다.

## 기본 원칙

- PR 하나는 기능 하나, 버그 하나, 문서 정리 하나, CI/runtime 설정 변경 하나만 담습니다.
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
codex/crawl-naver-targets
codex/data-alias-matcher
codex/market-quote-cache
codex/trade-order-domain
codex/agent-contrarian-log
codex/front-dashboard-shell
codex/ops-track-names
```

트랙별 권장 prefix:

- `crawl-`: `crawl`
- `data-`: `data`
- `market-`: `market`
- `trade-`: `trade`
- `agent-`: `agent`
- `front-`: `front`
- `ops-`: `ops`

## 트랙 브랜치 전략

기본은 작은 PR을 `main`에 자주 통합하는 방식입니다.

- 의존이 적은 작업은 `codex/<prefix>-<task>` 브랜치에서 작업하고, 관련 단위 테스트와 검증을 통과하면 `main`으로 PR을 보냅니다.
- API schema, DB migration, fixture, mock response 같은 공통 계약은 가능한 한 먼저 `main`에 넣습니다.
- 아직 사용자에게 노출하면 안 되는 기능은 feature flag, mock mode, disabled default로 숨깁니다.

결합이 강한 작업만 짧은 수명의 `track/*` 브랜치를 씁니다.

- 예: `track/front-dashboard`, `track/market-quotes`
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
[crawl][feat] 커뮤니티 게시글 중복 저장 방지
[crawl][fix] 에펨코리아 게시글 시간 파싱 보정
[data][feat] 종목 별칭 매칭 확장
[ops][docs] PR 크기와 라벨 규칙 정리
[ops][chore] 백엔드와 파이프라인 테스트 워크플로 분리
```

첫 번째 태그는 작업 트랙, 두 번째 태그는 작업 타입입니다. 제목은 가능한 한 `~한다`, `~했다`, `~함` 대신 명사형으로 끝냅니다. GitHub 라벨과 Notion 작업명도 같은 요약을 쓰면 추적하기 쉽습니다.

## 작업 타입 태그

- `[feat]`: 사용자나 시스템의 새 동작 추가
- `[fix]`: 버그 수정
- `[docs]`: 문서만 변경
- `[refactor]`: 동작 변경 없는 구조 개선
- `[perf]`: 성능 개선
- `[chore]`: 기타 유지보수

## 작업 트랙 태그

- `[crawl]`: `crawl`
- `[data]`: `data`
- `[market]`: `market`
- `[trade]`: `trade`
- `[agent]`: `agent`
- `[front]`: `front`
- `[ops]`: `ops`

## 변경 파트 태그

- `[backend]`: Spring Boot, DB schema, API, JPA
- `[pipeline]`: Python crawler/analysis pipeline, matcher, LLM provider
- `[ci]`: GitHub Actions, 테스트 실행 환경
- `[docs]`: README, 기획, 작업 문서
- `[rule]`: 작업 규칙, 컨벤션, 인수인계, Notion 운영 기준
- `[asset]`: 코드가 참조하는 데이터 자산, seed, fixture, mock
- `[runtime]`: Docker Compose, 환경 변수, 로컬 실행
- `[front]`: 사용자 화면, 대시보드, UI 상태, mock 화면

## GitHub 라벨 규칙

PR을 만들 때 제목 태그와 같은 의미의 작업 트랙 `track:*`, 작업 타입 `type:*` 라벨을 붙입니다. 변경 파트 `part:*`는 실제 파일이나 리뷰 경로를 드러낼 때만 붙이는 보조 라벨입니다.

작업 타입 라벨:

- `type:feat`
- `type:fix`
- `type:docs`
- `type:refactor`
- `type:perf`
- `type:chore`

작업 트랙 라벨:

- `track:crawl`: `crawl`
- `track:data`: `data`
- `track:market`: `market`
- `track:trade`: `trade`
- `track:agent`: `agent`
- `track:front`: `front`
- `track:ops`: `ops`

변경 파트 라벨:

- `part:backend`
- `part:pipeline`
- `part:front`
- `part:ci`
- `part:runtime`
- `part:docs`
- `part:rule`
- `part:asset`

크기 라벨:

- `size:XS`: 1-2개 파일, 아주 작은 수정
- `size:S`: 3-5개 파일, 한 맥락의 작은 변경
- `size:M`: 6-10개 파일, 리뷰 가능한 단일 작업
- `size:L`: 11개 이상 파일. 원칙적으로 분리하고, 예외 사유를 PR 설명에 적습니다.

## PR 크기 기준

- 선호: 5개 파일 이하
- 허용: 10개 파일 이하
- 11개 이상이면 분리 가능성을 먼저 검토합니다.
- backend와 pipeline을 동시에 바꾸는 PR은 계약 변경처럼 함께 배포되어야 할 때만 허용합니다.
- 문서와 테스트는 구현 PR에 함께 포함할 수 있지만, 독립 문서 정리는 별도 PR로 분리합니다.

## 커밋 메시지 규칙

커밋 제목은 PR 제목과 같은 형식을 씁니다.

```text
[트랙][타입] 명사형 요약
```

커밋 본문이 필요하면 한국어로 씁니다.

```text
[crawl][fix] 에펨코리아 시간 파싱 보정

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

## 완료 보고 규칙

사용자에게 작업 완료를 보고할 때는 PR 본문보다 더 쉽게 씁니다. 사용자는 파일명이나 내부 상태값보다 “그래서 무엇을 알 수 있게 됐는지”, “무엇을 믿고 다음 결정을 할 수 있는지”를 먼저 알아야 합니다.

완료 보고는 아래 순서를 따릅니다.

1. 이번 작업으로 가능해진 일을 한 문장으로 설명합니다.
2. 왜 이 작업이 필요했는지 이전의 불편함이나 판단 문제를 설명합니다.
3. 기술 용어는 처음 등장할 때 바로 쉬운 설명을 붙입니다.
4. 이번 PR에 포함한 것과 포함하지 않은 것을 나눕니다.
5. Superpowers/gstack 사용 여부와 이유를 짧게 적습니다.
6. 검증 결과를 사람이 읽기 쉬운 문장으로 요약합니다.
7. PR, Notion, 브랜치, worktree 정리 상태는 마지막에 둡니다.

도구 사용은 아래 기준으로 보고합니다.

- `Superpowers`: worktree 분리, spec/plan, TDD, 디버깅, 완료 전 검증, 브랜치 마무리처럼 작업 절차와 검증 게이트에 사용했을 때 적습니다.
- `gstack`: 실제 브라우저에서 localhost/배포 화면을 열어 라우팅, 버튼, 콘솔 에러, 반응형, 스크린샷 증거를 확인했을 때 적습니다.
- 쓰지 않은 도구도 중요한 판단이면 이유를 적습니다. 예: `gstack 미사용: 문서 전용 작업이라 브라우저 확인 대상 없음`.

예시:

```text
이번 작업으로 source policy, 즉 “어떤 커뮤니티를 지금 수집해도 되는지 정한 설정” 때문에 수집을 건너뛴 경우도 기록에 남게 됐습니다.

전에는 데이터가 안 들어왔을 때 크롤러 오류인지, 정책상 일부러 수집을 안 한 건지 구분하기 어려웠습니다. 이제는 crawl_runs, 즉 “수집을 언제, 어떻게 시도했는지 남기는 기록”에 SKIPPED, 즉 “오류가 아니라 조건 때문에 실행하지 않고 건너뛴 상태”로 남습니다.

그래서 운영할 때는 “데이터가 없다”만 보는 게 아니라 “왜 데이터가 없는지”까지 확인할 수 있습니다.

도구 사용:
- Superpowers: worktree 분리와 완료 전 검증에 사용했습니다.
- gstack: 문서/backend 작업이라 브라우저 확인 대상이 없어 사용하지 않았습니다.
```

좋지 않은 보고:

```text
source policy로 skip된 수집 실행도 crawl_runs에 SKIPPED로 남기도록 했습니다.
```

이 문장은 기술적으로 맞더라도 사용자에게는 너무 압축되어 있습니다. 반드시 기술 용어와 사람 말 설명을 같이 씁니다.

트러블슈팅 섹션에는 짧은 결론과 링크만 남깁니다. 제품 개발/운영에 영향을 주는 CI, Docker, 외부 API, 인증, 환경 변수 문제는 `docs/TROUBLESHOOTING_GUIDE.md` 형식으로 Notion `개발자 기술 경험 DB`의 `문제해결` 유형에 자세히 기록합니다. 성능 개선, 품질 개선, 기술 결정은 `docs/ENGINEERING_EVIDENCE_GUIDE.md` 기준으로 별도 종류를 선택합니다. Codex/Notion/GitHub PR/문서 운영 사고는 `에이전트 운영 로그 DB`에 분리해 남깁니다.

## GitHub CLI 인코딩 규칙

한국어 PR 본문은 PowerShell 파이프나 stdin으로 `gh`에 넘기지 않습니다. Windows PowerShell에서 `$body | gh pr create --body-file -` 또는 `$body | gh pr edit --body-file -`를 쓰면 한국어와 이모지가 `?`로 치환되어 GitHub에 저장될 수 있습니다.

PR 본문은 UTF-8 no BOM 파일로 저장한 뒤 파일 경로를 넘깁니다.

```powershell
$tmp = Join-Path $env:TEMP 'pr-body.md'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tmp, $body, $utf8NoBom)
gh pr create --body-file $tmp
Remove-Item -LiteralPath $tmp
```

PR 생성이나 수정 직후에는 저장 결과를 확인합니다.

```powershell
gh pr view <number> --json body --jq .body
gh pr view <number> --json body --jq .body | Select-String -Pattern '\?\?'
```

두 번째 명령에서 본문 치환으로 보이는 `??`가 나오면 PR 본문을 UTF-8 파일 방식으로 다시 올립니다.

좋은 예:

```text
- Backend는 Docker Maven 컨테이너에서 `mvn clean test`로 실행했고, 통합 테스트 2개가 통과했습니다.
- Pipeline은 Python 3.10 컨테이너에서 의존성을 설치한 뒤 `pytest`를 실행했고, 테스트 4개가 통과했습니다.
- Docker Compose로 MySQL, backend, pipeline이 모두 정상 기동되는 것을 확인했습니다.
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
