# Git/PR 컨벤션

이 저장소는 Codex 또는 작업 에이전트가 `git`과 `gh`로 브랜치 생성, 커밋, push, PR 생성, 라벨 지정, CI 확인, merge를 처리합니다.

## 빠른 체크리스트

PR 전후에 아래는 생략하지 않습니다.

1. 브랜치: `codex/<short-task-name>`
2. 제목: `[작업영역][타입] 명사형 요약`
3. 라벨: `track:<작업영역>`, `type:*`, `size:*`, 필요 시 `part:*`
4. 본문: `.github/pull_request_template.md` 복사본 + UTF-8 no BOM 파일 + `gh --body-file`
5. 검증: 관련 테스트 + `git diff --check`
6. 본문 확인: `gh pr view --json body --jq .body`
7. 템플릿 감사: 현재 PR 템플릿의 `##` 섹션이 모두 남아 있는지 확인
8. 한글 깨짐 확인: `??` 검색
9. 리뷰 확인: 사람 리뷰와 `chatgpt-codex-connector`의 actionable 의견 확인
10. 기록: Notion 기록 여부와 이유 명시
11. 종료: merge/close 후 브랜치와 worktree 정리 여부 확인

## 브랜치

기본 형식:

```text
codex/<work-area>-<task>
```

예:

- `codex/community-target-api`
- `codex/stock-alias-matcher`
- `codex/ui-dashboard-shell`
- `codex/ops-chat-stability`

루트 checkout은 main/조율용입니다. 병렬 작업은 `.worktrees/<task>` 아래에서 진행합니다.

### 브랜치 생명주기

브랜치는 작업 단위가 실제로 생겼을 때 엽니다.

- 엽니다: 코드/문서 수정이 필요하고 PR 후보가 분명할 때
- 엽니다: 병렬 ui/community/stock/indicator/market/simulation/agent 작업처럼 파일 소유권을 분리해야 할 때
- 열지 않습니다: 단순 조사, PR/로그 확인, 사용자 질문 답변처럼 변경이 없는 작업
- 열지 않습니다: 이미 같은 작업 영역/같은 목적의 활성 브랜치가 있고 그 브랜치에서 이어가는 편이 자연스러울 때

작업 중인 브랜치는 아래 상태 중 하나여야 합니다.

- active: 현재 작업 중이고 다음 행동이 명확함
- review: PR이 열려 있고 리뷰/CI/사용자 확인을 기다림
- blocked: 외부 결정이나 다른 작업 영역 계약을 기다림
- stale: main보다 오래 뒤처졌거나 대체 PR이 생김
- close-candidate: merge, 폐기, 대체 중 하나로 정리할 수 있음

닫는 기준:

- PR이 merge되면 원격 브랜치와 worktree를 삭제합니다.
- PR이 close되고 되살릴 조각이 없으면 브랜치와 worktree를 정리합니다.
- PR이 close됐지만 살릴 조각이 있으면 새 작은 브랜치/PR로 옮기고 기존 브랜치는 닫습니다.
- main에 이미 같은 내용이 들어갔거나 더 최신 PR이 대체했으면 stale 브랜치로 두지 않습니다.
- 1일 이상 진행이 없고 다음 행동이 불명확하면 ops가 close-candidate로 보고합니다.

정리 책임:

- 작업을 끝낸 에이전트가 자기 PR의 merge/close 직후 브랜치와 worktree 정리 여부를 확인합니다.
- clean worktree이고 main에 반영됐거나 폐기 확정이면 작업 에이전트가 정리합니다.
- dirty worktree, 미반영 커밋, 살릴 조각, 실행 중인 dev server가 있으면 삭제하지 않고 상태와 다음 조치를 남깁니다.
- ops는 열린 브랜치/worktree가 누적되거나 close-candidate가 생겼을 때 주기적으로 누락분을 점검합니다.

남겨둘 수 있는 경우:

- PR review/CI/user 확인을 기다리는 review 상태
- 다른 작업 영역 계약이나 사용자 결정이 필요한 blocked 상태
- 실제로 이어서 작업할 active 상태
- 데모 서버나 화면 확인이 그 worktree에 묶여 있고 대체 URL을 아직 못 정한 경우

브랜치 정리는 넓은 diff 출력 대신 요약으로 봅니다. 우선 `git branch -vv --sort=-committerdate`, `git worktree list`, `gh pr list --state open`으로 상태를 보고, 필요한 브랜치만 diff를 확인합니다.

## PR 제목

형식:

```text
[작업영역][타입] 명사형 요약
```

예:

- `[community][feat] CrawlTarget queue API`
- `[stock][fix] 별칭 중첩 매칭 보강`
- `[ui][feat] 대시보드 shell`
- `[ops][docs] 채팅 안정성 규칙`

제목은 `~한다`, `~했다`, `~함`으로 끝내지 않습니다.

## 태그와 라벨

작업 영역:

- PR 제목 prefix와 `track:*` 라벨 값은 `community`, `stock`, `indicator`, `market`, `simulation`, `agent`, `ui`, `ops` 중 하나를 씁니다.
- GitHub 라벨 family 이름은 기존 형식인 `track:*`를 유지합니다. 바뀌는 것은 `track:` 뒤 분류값입니다.
- 과거 `crawl`, `data`, `trade`, `front` 값은 닫힌 PR이나 과거 Notion 카드 해석용 alias입니다.

작업 타입:

- `feat`: 기능
- `fix`: 버그 수정
- `docs`: 문서
- `refactor`: 구조 개선
- `perf`: 성능
- `chore`: CI/runtime/운영 보조

GitHub 라벨:

- `track:*`: 작업 영역. 예: `track:community`, `track:stock`, `track:ui`
- `type:*`: 작업 타입
- `size:*`: 변경 크기
- `part:*`: 실제 리뷰 경로나 변경 파트를 드러낼 때만 사용

크기 기준:

- `size:XS`: 1-2개 파일
- `size:S`: 3-5개 파일
- `size:M`: 6-10개 파일
- `size:L`: 11개 이상 파일. 원칙적으로 분리하고 예외 사유를 적습니다.

라벨의 상세 의미는 `docs/layers/ops/LABEL_GUIDE.md`의 필요한 섹션만 확인합니다.

## 커밋

커밋 제목은 가능하면 PR 제목과 같은 형식을 씁니다.

```text
[ops][docs] 채팅 안정성 규칙
```

커밋 본문은 필요할 때만 한국어로 짧게 씁니다.

## PR 본문

본문은 사람이 읽기 쉬운 카드형 흐름으로 씁니다.

PR 본문은 `.github/pull_request_template.md`를 출발점으로 작성합니다. GitHub 웹 UI를 쓰면 템플릿이 자동으로 깔리지만, CLI에서 `gh pr create --body-file <path>`를 쓰면 넘긴 파일 내용이 그대로 저장됩니다. 그래서 `--body-file`에 넘기는 파일도 반드시 템플릿 파일을 복사한 뒤 각 항목을 채워야 합니다.

기억에 의존해 비슷한 구조로 다시 쓰는 것은 실패로 봅니다. 제목과 문체가 비슷해도 현재 템플릿의 `##` 섹션 제목이 하나라도 빠지면 PR 규칙 미준수입니다.

템플릿을 일부 비워야 하는 경우에도 섹션 제목은 유지합니다. 해당 없는 항목은 `해당 없음` 또는 `Notion 미기록: <이유>`처럼 이유를 남깁니다.

PR 본문은 파일 목록, 브랜치 이름, 명령어, 내부 기술명 나열로 시작하지 않습니다. 첫 화면에서는 사용자가 무엇을 판단할 수 있게 되었는지, 제품이나 운영 흐름이 어떻게 달라졌는지부터 설명합니다. 파일명, 경로, 브랜치명, 구현 세부 기술은 `리뷰 가이드`, `PR 범위`, 접힌 details 같은 보조 위치에 둡니다.

문장은 리뷰어가 저장소 맥락을 몰라도 읽을 수 있게 씁니다. 예를 들어 `DashboardPage.vue 수정`보다 `대시보드 첫 화면에서 커뮤니티 반응과 주요 지표를 한 번에 비교할 수 있게 함`처럼 결과와 이유를 먼저 적습니다.

권장 섹션:

1. `한눈에 보기`
2. `바뀐 내용`
3. `리뷰 가이드`
4. `PR 범위`
5. `검증 결과`
6. `리스크와 후속 작업`
7. `Notion 기록`
8. `라벨/태그 참고`

검증 섹션은 명령어 목록만 붙이지 않습니다. 먼저 사람이 읽을 수 있는 문장으로 무엇을 확인했고 결과가 어땠는지 씁니다. 필요한 명령어는 보조 정보로 둡니다.

## UTF-8 본문 규칙

한국어 PR 본문은 PowerShell 파이프나 stdin으로 `gh`에 넘기지 않습니다. UTF-8 no BOM 파일을 만들고 `--body-file <path>`로 전달합니다.

예:

```powershell
$bodyPath = Join-Path $env:TEMP 'pr-body.md'
$template = Get-Content -Raw -Encoding utf8 .github\pull_request_template.md
$body = $template.Replace('<한 문장 요약>', '이번 작업의 실제 요약')
[System.IO.File]::WriteAllText($bodyPath, $body, [System.Text.UTF8Encoding]::new($false))
gh pr create --body-file $bodyPath
```

생성/수정 직후 확인:

```powershell
gh pr view <number> --json body --jq .body
gh pr view <number> --json body --jq .body | Select-String -Pattern "\?\?"
```

`??` 치환 문자열이 보이면 merge 전에 UTF-8 파일 방식으로 다시 올립니다.

템플릿 섹션 감사:

```powershell
$template = Get-Content -Raw -Encoding utf8 .github\pull_request_template.md
$required = [regex]::Matches($template, '(?m)^## .+$') | ForEach-Object { $_.Value }
$body = gh pr view <number> --json body --jq .body
$missing = $required | Where-Object { -not $body.Contains($_) }
if ($missing) { throw "PR template headings missing: $($missing -join ', ')" }
```

## 리뷰 확인

`chatgpt-codex-connector`는 GitHub PR에 붙는 Codex 자동 리뷰 앱입니다. 너나사 서비스 기능이 아니며, repo 코드 안에서 켜고 끄는 대상도 아닙니다. 현재 Codex GitHub code review 안내 기준의 발동 조건은 아래입니다.

- Codex code review가 켜진 repo에서 review 대상 PR을 열 때
- draft PR을 ready for review로 바꿀 때
- PR 댓글에 `@codex review`를 포함할 때. 일회성 초점이 있으면 `@codex review for security regressions`처럼 추가 지시를 붙일 수 있습니다.

자동 리뷰가 아직 달리지 않았는데 리뷰가 필요한 PR이면 merge 전에 `@codex review`로 수동 요청하거나, 자동 리뷰 미실행 사유를 PR 본문/완료 보고에 남깁니다.

작업자는 merge 전 아래를 확인합니다.

- 사람 리뷰와 자동 리뷰 댓글을 모두 봅니다.
- P1/P2 또는 명확한 버그 지적은 기본적으로 merge 전 처리합니다.
- 오탐이면 PR 본문이나 댓글에 왜 오탐인지 한국어로 남깁니다.
- 당장 분리해야 하는 지적이면 후속 PR/TASKS/Notion 중 하나에 남기고, merge 보고에 이유를 적습니다.
- 자동 리뷰가 영어로 달려도 봇 댓글 자체를 수정하려 하지 않습니다. 대신 핵심 지적과 처리 결과를 한국어로 요약합니다.

확인 명령 예:

```powershell
gh pr view <number> --comments
gh pr view <number> --json reviews,comments
```

## 완료 보고

사용자에게는 PR 본문보다 쉽게 보고합니다.

1. 무엇이 해결됐고 이제 무엇을 판단할 수 있는지
2. 핵심 변경을 사람이 이해할 말로 설명
3. 포함 범위와 제외 범위
4. 검증 결과
5. Superpowers/gstack 사용 여부와 이유
6. PR, Notion, 브랜치, worktree 상태

파일명, 폴더명, 명령어만 나열하지 않습니다. 파일 경로는 사용자가 직접 확인해야 할 때 보조 정보로 붙입니다. 문서/backend 작업이라 브라우저 확인 대상이 없으면 `gstack 미사용` 이유를 적습니다. front/UI 작업이면 가능하면 gstack/browser 확인 결과를 적습니다.

## Merge

- CI가 통과하면 squash merge합니다.
- merge 전 사람 리뷰와 `chatgpt-codex-connector` 자동 리뷰의 P1/P2/actionable 의견이 처리됐는지 확인합니다.
- merge 제목과 본문은 한국어로 정리합니다.
- merge 후 브랜치는 삭제합니다.
- merge 후 필요한 경우 Notion 작업일지에 핵심 변경과 검증 결과를 남깁니다.
