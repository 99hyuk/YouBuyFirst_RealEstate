# Git/PR 컨벤션

이 저장소는 Codex 또는 작업 에이전트가 `git`과 `gh`로 브랜치 생성, 커밋, push, PR 생성, 라벨 지정, CI 확인, merge를 처리합니다.

## 빠른 체크리스트

PR 전후에 아래는 생략하지 않습니다.

1. 브랜치: `codex/<short-task-name>`
2. 제목: `[트랙][타입] 명사형 요약`
3. 라벨: `track:*`, `type:*`, `size:*`, 필요 시 `part:*`
4. 본문: UTF-8 no BOM 파일 + `gh --body-file`
5. 검증: 관련 테스트 + `git diff --check`
6. 본문 확인: `gh pr view --json body --jq .body`
7. 한글 깨짐 확인: `??` 검색
8. 기록: Notion 기록 여부와 이유 명시

## 브랜치

기본 형식:

```text
codex/<track>-<task>
```

예:

- `codex/crawl-target-api`
- `codex/data-alias-matcher`
- `codex/front-dashboard-shell`
- `codex/ops-chat-stability`

루트 checkout은 main/조율용입니다. 병렬 작업은 `.worktrees/<task>` 아래에서 진행합니다.

## PR 제목

형식:

```text
[트랙][타입] 명사형 요약
```

예:

- `[crawl][feat] CrawlTarget queue API`
- `[data][fix] 별칭 중첩 매칭 보강`
- `[front][feat] 대시보드 shell`
- `[ops][docs] 채팅 안정성 규칙`

제목은 `~한다`, `~했다`, `~함`으로 끝내지 않습니다.

## 태그와 라벨

트랙:

- `crawl`, `data`, `market`, `trade`, `agent`, `front`, `ops`

작업 타입:

- `feat`: 기능
- `fix`: 버그 수정
- `docs`: 문서
- `refactor`: 구조 개선
- `perf`: 성능
- `chore`: CI/runtime/운영 보조

GitHub 라벨:

- `track:*`: 작업 트랙
- `type:*`: 작업 타입
- `size:*`: 변경 크기
- `part:*`: 실제 리뷰 경로나 변경 파트를 드러낼 때만 사용

크기 기준:

- `size:XS`: 1-2개 파일
- `size:S`: 3-5개 파일
- `size:M`: 6-10개 파일
- `size:L`: 11개 이상 파일. 원칙적으로 분리하고 예외 사유를 적습니다.

라벨의 상세 의미는 `docs/LABEL_GUIDE.md`의 필요한 섹션만 확인합니다.

## 커밋

커밋 제목은 가능하면 PR 제목과 같은 형식을 씁니다.

```text
[ops][docs] 채팅 안정성 규칙
```

커밋 본문은 필요할 때만 한국어로 짧게 씁니다.

## PR 본문

본문은 사람이 읽기 쉬운 카드형 흐름으로 씁니다.

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
[System.IO.File]::WriteAllText($bodyPath, $body, [System.Text.UTF8Encoding]::new($false))
gh pr create --body-file $bodyPath
```

생성/수정 직후 확인:

```powershell
gh pr view <number> --json body --jq .body
gh pr view <number> --json body --jq .body | Select-String -Pattern "\?\?"
```

`??` 치환 문자열이 보이면 merge 전에 UTF-8 파일 방식으로 다시 올립니다.

## 완료 보고

사용자에게는 PR 본문보다 쉽게 보고합니다.

1. 이제 무엇을 판단할 수 있게 됐는지
2. 핵심 변경
3. 포함 범위와 제외 범위
4. 검증 결과
5. Superpowers/gstack 사용 여부와 이유
6. PR, Notion, 브랜치, worktree 상태

문서/backend 작업이라 브라우저 확인 대상이 없으면 `gstack 미사용` 이유를 적습니다. front/UI 작업이면 가능하면 gstack/browser 확인 결과를 적습니다.

## Merge

- CI가 통과하면 squash merge합니다.
- merge 제목과 본문은 한국어로 정리합니다.
- merge 후 브랜치는 삭제합니다.
- merge 후 필요한 경우 Notion 작업일지에 핵심 변경과 검증 결과를 남깁니다.
