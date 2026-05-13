# 작업 단위 PR 자동화

## 현재 상태

로컬 저장소에는 PR 자동화 스크립트가 준비되어 있습니다. 다만 실제 GitHub PR을 만들려면 GitHub 저장소와 로컬 checkout을 연결해야 합니다.

현재 확인된 상태:

- GitHub remote: `origin` -> `https://github.com/99hyuk/YouBuyFirst.git`
- GitHub CLI: 설치/로그인 완료. Codex PATH에는 없을 수 있어 스크립트가 기본 설치 경로도 자동 탐색합니다.
- 현재 브랜치: `codex/human-indicator-mvp`
- Bootstrap draft PR: https://github.com/99hyuk/YouBuyFirst/pull/1

## 사용자가 준비해야 하는 것

GitHub 계정 인증과 저장소 생성은 사용자 권한이 필요한 영역입니다. 아래 둘 중 하나를 선택하면 됩니다.

### 옵션 A. GitHub 웹에서 저장소 만들기

1. GitHub에서 새 repository를 만듭니다.
2. 저장소 이름 예: `human-indicator`
3. Visibility는 우선 `Private` 권장
4. `Add a README file`을 켭니다. 이렇게 해야 `main` 브랜치가 생겨 첫 bootstrap PR을 만들기 쉽습니다.
5. 로컬에서 다음 명령을 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-github.ps1 -Repository "<owner>/human-indicator"
```

### 옵션 B. GitHub CLI로 저장소 만들기

먼저 GitHub CLI를 설치하고 로그인합니다.

```powershell
gh --version
gh auth login
```

그 다음 저장소 생성과 remote 연결을 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-github.ps1 -Repository "<owner>/human-indicator" -CreateRepo
```

단, 이 방식은 빈 저장소를 만들 수 있으므로 첫 PR의 base branch가 없을 수 있습니다. 가장 안전한 첫 흐름은 옵션 A처럼 README가 있는 GitHub 저장소를 먼저 만드는 방식입니다.

## 자동화 스크립트

### 1. 새 작업 단위 시작

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\new-work-unit.ps1 -Name "crawler-parser-hardening"
```

이 스크립트는 다음을 수행합니다.

- `codex/crawler-parser-hardening` 브랜치 생성
- `docs/work-units/YYYY-MM-DD-crawler-parser-hardening.md` 생성
- 작업 목적, 범위, 검증 계획을 적을 템플릿 제공

### 2. PR 생성

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\open-pr.ps1 `
  -Title "Implement crawler parser hardening" `
  -Body "Adds parser hardening and tests." `
  -CommitMessage "Harden crawler parsers" `
  -WorkUnit "docs/work-units/YYYY-MM-DD-crawler-parser-hardening.md"
```

`scripts/open-pr.ps1`은 다음 일을 합니다.

- 현재 브랜치 확인
- `main`/`master` 직접 PR 금지
- `codex/<task-name>` 브랜치 규칙 확인
- 작업 단위 문서 확인
- 너무 큰 PR 기본 차단
- `git diff --check` 실행
- 변경 파일 stage
- commit 생성
- branch push
- draft PR 생성

## 첫 bootstrap PR

현재 저장소는 초기 scaffold라 변경 파일이 많습니다. 첫 PR에 한해서 다음 옵션이 필요할 수 있습니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\open-pr.ps1 `
  -Title "Bootstrap human indicator MVP" `
  -Body "Initial MVP scaffold and project workflow." `
  -CommitMessage "Bootstrap human indicator MVP" `
  -AllowLargePr
```

첫 PR 이후에는 `-AllowLargePr`를 쓰지 않는 것을 원칙으로 합니다.

## 보수적 운영 규칙

- 기능 하나, 버그 하나, 인프라 변경 하나당 PR 하나.
- 기본 PR 크기 제한은 20 files입니다.
- 여러 기능을 한 PR에 섞지 않습니다.
- 검증을 일부러 건너뛰는 경우에만 `-SkipVerification`을 씁니다.
- `docs/CURRENT_HANDOFF.md`와 해당 work-unit 문서는 PR마다 갱신합니다.
