# front 라우팅 인벤토리 실행 계획

> **에이전트 작업자 필수 지시:** 이 계획을 실행할 때는 `superpowers:executing-plans` 또는 `superpowers:subagent-driven-development`를 사용한다. 체크박스(`- [ ]`)를 하나씩 처리하고, 루트 checkout이 아니라 `C:\agents\YouBuyFirst\.worktrees\front-route-inventory` 안에서만 작업한다.

**목표:** front 트랙의 첫 문서 PR을 마무리한다. 이 PR은 화면 구현이 아니라, 다음 Vue shell 작업이 따라갈 라우트와 mock/API 후보를 정리한다.

**방식:** 문서 전용 PR이다. Vue 프로젝트를 만들지 않고, backend/pipeline/API 계약도 바꾸지 않는다. 변경 대상은 front route inventory 설계 문서와 이 실행 계획 문서뿐이다.

**사용 도구:** Git, GitHub CLI(`gh`), Markdown 문서, 프로젝트 하위 worktree.

---

## 현재 상황 요약

- 기준 루트: `C:\agents\YouBuyFirst`
- 작업 위치: `C:\agents\YouBuyFirst\.worktrees\front-route-inventory`
- 작업 브랜치: `codex/front-route-inventory`
- 현재 변경:
  - 이미 커밋됨: `docs/superpowers/specs/2026-05-15-front-route-inventory-design.md`
  - 아직 커밋 전: `docs/superpowers/plans/2026-05-15-front-route-inventory.md`
- 원격 `main`에 새 커밋이 하나 들어와 있어, PR 전 rebase가 필요하다.

## 사용자가 이해하면 되는 핵심

이번 PR은 “프론트 첫 화면을 만든다”가 아니라 “프론트 첫 화면을 만들기 전에 화면 지도를 정한다”이다.

정한 기본값:

- 첫 화면은 `/dashboard`
- 종목 상세는 `/stocks/:symbol`
- 커뮤니티 비교는 `/communities`
- 에이전트 리더보드는 `/agents`
- 모의 포트폴리오는 `/portfolio`로 자리를 예약하되, 처음에는 “준비 중” 상태

아직 확정하지 않는 것:

- 실제 API 주소와 응답 필드
- 차트 라이브러리
- 최종 디자인
- 실제 투자 판단처럼 보이는 문구
- backend, pipeline, market, trade, agent 구현

---

## 작업 1. 작업 위치와 브랜치 확인

**파일:**

- 읽기: `docs/superpowers/specs/2026-05-15-front-route-inventory-design.md`
- 수정 없음

- [ ] **1-1. 작업 위치가 worktree인지 확인**

실행:

```powershell
git status --short --branch
git worktree list --porcelain
```

기대 결과:

```text
## codex/front-route-inventory...origin/main [ahead 1, behind 1]
worktree C:/agents/YouBuyFirst
branch refs/heads/main
worktree C:/agents/YouBuyFirst/.worktrees/front-route-inventory
branch refs/heads/codex/front-route-inventory
```

의미:

- 루트 `C:\agents\YouBuyFirst`는 main 유지
- 실제 작업은 `.worktrees/front-route-inventory`에서만 진행

- [ ] **1-2. 원격 변경 가져오기**

실행:

```powershell
git fetch origin
```

기대 결과: 오류 없이 종료.

- [ ] **1-3. 최신 main 위로 현재 브랜치 올리기**

실행:

```powershell
git rebase origin/main
```

기대 결과:

```text
Successfully rebased and updated refs/heads/codex/front-route-inventory.
```

충돌이 나면:

- front 문서 충돌만 해결한다.
- `backend`, `pipeline`, `crawl`, `data`, `market`, `trade`, `agent` 파일은 건드리지 않는다.

- [ ] **1-4. rebase 뒤 상태 확인**

실행:

```powershell
git status --short --branch
```

기대 결과:

```text
## codex/front-route-inventory...origin/main [ahead 1]
```

---

## 작업 2. 문서 품질 확인

**파일:**

- 읽기: `docs/superpowers/specs/2026-05-15-front-route-inventory-design.md`
- 문제가 발견될 때만 수정: `docs/superpowers/specs/2026-05-15-front-route-inventory-design.md`

- [ ] **2-1. 비어 있는 placeholder가 없는지 확인**

실행:

```powershell
$patterns = @(
  ('T' + 'BD'),
  ('TO' + 'DO'),
  [string]::Concat([char]0xBBF8, [char]0xC815),
  [string]::Concat([char]0xB098, [char]0xC911, [char]0xC5D0, ' ', [char]0xC54C, [char]0xC544, [char]0xC11C),
  [string]::Concat([char]0xC801, [char]0xB2F9, [char]0xD788)
)
foreach ($pattern in $patterns) {
  rg -n $pattern docs\superpowers\specs\2026-05-15-front-route-inventory-design.md
}
```

기대 결과: 검색 결과 없음.

- [ ] **2-2. 필요한 route가 모두 들어 있는지 확인**

실행:

```powershell
rg -n "/dashboard|/stocks/:symbol|/communities|/agents|/portfolio" docs\superpowers\specs\2026-05-15-front-route-inventory-design.md
```

기대 결과: 다섯 route가 모두 검색된다.

- [ ] **2-3. 제외 범위가 명확한지 확인**

실행:

```powershell
rg -n "Vue 프로젝트 생성|backend API|차트 라이브러리|기획자 확인 필요|투자 자문" docs\superpowers\specs\2026-05-15-front-route-inventory-design.md
```

기대 결과:

- Vue 프로젝트 생성 제외
- backend API 변경 제외
- 차트 라이브러리 확정 제외
- 기획자 확인 필요 항목 존재
- 투자 자문처럼 보이는 문구 경계 존재

- [ ] **2-4. 줄 끝 공백 확인**

실행:

```powershell
git diff --check HEAD~1 HEAD
```

기대 결과: 출력 없음.

---

## 작업 3. 계획 문서 커밋

**파일:**

- 추가: `docs/superpowers/plans/2026-05-15-front-route-inventory.md`

- [ ] **3-1. 계획 문서 공백 확인**

실행:

```powershell
git diff --check
```

기대 결과: 출력 없음.

- [ ] **3-2. 계획 문서 stage**

실행:

```powershell
git add docs/superpowers/plans/2026-05-15-front-route-inventory.md
```

기대 결과: 오류 없이 종료.

- [ ] **3-3. 계획 문서 커밋**

실행:

```powershell
git commit -m "[front][docs] 라우팅 인벤토리 실행 계획"
```

기대 결과: 계획 문서 1개가 커밋된다.

---

## 작업 4. PR 생성

**파일:**

- repo 밖 임시 파일 생성: `$env:TEMP\front-route-inventory-pr.md`
- tracked repo 파일은 수정하지 않는다.

- [ ] **4-1. 브랜치 push**

실행:

```powershell
git push -u origin codex/front-route-inventory
```

기대 결과: 원격 브랜치가 생성되고 upstream이 설정된다.

- [ ] **4-2. PR 본문을 UTF-8 no BOM 파일로 작성**

실행:

```powershell
$body = @'
## 🧭 한눈에 보기

> 이번 PR은 front 트랙의 첫 화면 구현 전에 route-first 화면 인벤토리와 mock/API 후보를 정리하는 문서 PR입니다.

| 항목 | 내용 |
| --- | --- |
| 작업 트랙 | `track:front` |
| 작업 타입 | `type:docs` |
| 변경 파트 | `part:docs` |
| 크기 | `size:S` |
| 기준 문서 | `docs/workstreams/front/README.md` |
| 상태 | CI 확인 전 |
| Notion 기록 | 작업일지 반영 전 |
| 트러블슈팅 | 해당 없음 |

## 🧩 바뀐 내용

- `docs/superpowers/specs/2026-05-15-front-route-inventory-design.md`를 추가했습니다.
- `docs/superpowers/plans/2026-05-15-front-route-inventory.md`를 추가했습니다.
- `/dashboard`, `/stocks/:symbol`, `/communities`, `/agents`, `/portfolio` route 후보를 정리했습니다.
- 화면별 목적, mock fixture 후보, API 응답 후보, 소유 트랙, loading/empty/error 상태를 나눴습니다.
- `기획자 확인 필요` 항목을 화면별로 분리했습니다.

## 🔎 리뷰 가이드

- 먼저 볼 곳: `docs/superpowers/specs/2026-05-15-front-route-inventory-design.md`
- 가볍게 훑어도 되는 곳: 실행 계획 문서
- 특별히 확인해줬으면 하는 점: `/portfolio`를 disabled shell로 예약하는 방향과 `열기 지수` 용어를 후보로 두는 방향

## 📌 PR 범위

- 제목 형식: `[front][docs] 화면 라우팅 인벤토리 설계`
- 이 PR에 포함한 것: front route inventory 설계 문서와 실행 계획
- 일부러 제외한 것: Vue 프로젝트 생성, 실제 화면 구현, 차트 라이브러리 확정, backend/pipeline 변경
- 이 크기로 묶은 이유: 다음 Vue shell PR의 입력을 먼저 고정하기 위한 작은 docs-only PR입니다.

## ✅ 검증 결과

- 문서/공백: route 후보, placeholder, 범위 제외 문구를 검색했고 `git diff --check`가 통과했습니다.
- Backend: 변경 없음
- Pipeline: 변경 없음
- Runtime: 변경 없음

<details>
<summary>실행한 명령과 근거 보기</summary>

```powershell
git status --short --branch
git worktree list --porcelain
git fetch origin
git rebase origin/main
rg -n "/dashboard|/stocks/:symbol|/communities|/agents|/portfolio" docs\superpowers\specs\2026-05-15-front-route-inventory-design.md
rg -n "Vue 프로젝트 생성|backend API|차트 라이브러리|기획자 확인 필요|투자 자문" docs\superpowers\specs\2026-05-15-front-route-inventory-design.md
git diff --check
```

</details>

## ⚠️ 리스크와 후속 작업

- 남은 리스크: 실제 API 계약과 지표 이름은 아직 확정하지 않았습니다.
- 운영/데이터 영향: 없음
- 후속 작업: `front` 트랙에서 Vue 3 + Vite + TypeScript 기반 와이어프레임 shell 구현

## 🗂️ Notion 기록

- 작업일지: PR 생성 후 반영 예정
- 트러블슈팅: 해당 없음
- 다음 에이전트 메모: 이 문서의 route map을 기준으로 `front/src/router/routes.ts`와 fixture 파일을 만들면 됩니다.

## 🏷️ 라벨/태그 참고

- `track:front`
- `type:docs`
- `part:docs`
- `size:S`
'@
$tmp = Join-Path $env:TEMP 'front-route-inventory-pr.md'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tmp, $body, $utf8NoBom)
```

기대 결과: 임시 PR 본문 파일이 생성되고 한글이 깨지지 않는다.

- [ ] **4-3. PR 생성**

실행:

```powershell
gh pr create --base main --head codex/front-route-inventory --title "[front][docs] 화면 라우팅 인벤토리 설계" --body-file $tmp
```

기대 결과: GitHub PR URL이 출력된다.

- [ ] **4-4. 라벨 붙이기**

실행:

```powershell
gh pr edit --add-label "track:front,type:docs,part:docs,size:S"
```

기대 결과: PR에 라벨 4개가 붙는다.

- [ ] **4-5. PR 본문 한글 깨짐 확인**

실행:

```powershell
gh pr view --json body --jq .body
gh pr view --json body --jq .body | Select-String -Pattern '\?\?'
```

기대 결과:

- 첫 명령에서 한글이 정상적으로 보인다.
- 두 번째 명령에서 인코딩 깨짐으로 보이는 `??`가 나오지 않는다.

---

## 작업 5. 사용자에게 결과 전달

**파일:**

- 기본적으로 추가 수정 없음
- 사용자가 요청하면 `docs/CURRENT_HANDOFF.md`, `docs/TASKS.md` 갱신 가능

- [ ] **5-1. PR 요약 전달**

말할 내용:

```text
front route inventory PR을 만들었습니다. 이 PR은 Vue 프로젝트를 만들지 않고, 다음 shell 구현 PR의 route와 fixture 입력만 정리합니다.
```

- [ ] **5-2. 다음 작업 제안**

말할 내용:

```text
다음 작업은 `front-dashboard-shell`입니다. 별도 worktree `C:\agents\YouBuyFirst\.worktrees\front-dashboard-shell`에서 Vue 3 + Vite + TypeScript shell을 만들고, 이번 문서의 mock fixture를 코드로 옮기는 PR로 나누겠습니다.
```

- [ ] **5-3. Notion 기록**

PR 생성 후 Notion 도구가 사용 가능하면 작업 로그 DB에 기록한다.

기록 내용:

- 트랙: `front`
- 변경 파트: `docs`
- 크기: `S`
- 검증: 문서 검색과 `git diff --check` 통과
- 다음 메모: 다음 PR은 Vue shell 구현
