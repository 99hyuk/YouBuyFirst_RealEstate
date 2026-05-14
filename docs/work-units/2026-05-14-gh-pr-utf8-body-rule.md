# 2026-05-14 GitHub PR 본문 UTF-8 규칙

## 한눈에 보기

작업 트랙은 `ops`입니다. PowerShell에서 한국어 PR 본문을 `gh`에 파이프로 넘기면 본문이 `??`로 저장될 수 있어, PR 생성/수정 규칙을 UTF-8 파일 방식으로 고정합니다.

## 원인

Windows PowerShell here-string을 `$body | gh pr create --body-file -`처럼 native process stdin으로 넘기면 한국어와 이모지가 `?`로 치환될 수 있습니다. 이 경우 GitHub 브라우저 문제가 아니라 API에 저장된 본문 자체가 이미 손상됩니다.

## 변경 범위

- `AGENTS.md`에 한국어 PR 본문 입력 금지 패턴과 검증 절차를 추가합니다.
- `docs/GIT_CONVENTION.md`에 UTF-8 no BOM 파일을 `--body-file <path>`로 넘기는 예시를 추가합니다.
- `docs/WORKFLOW.md`에 PR 생성 후 본문 확인 단계를 추가합니다.
- `docs/TROUBLESHOOTING_GUIDE.md`에 GitHub PR 본문 인코딩 문제 확인 방법을 추가합니다.

## 검증 기준

- PR 본문을 만든 뒤 `gh pr view --json body --jq .body`로 한국어가 보이는지 확인합니다.
- `Select-String -Pattern '\?\?'`로 본문 치환 흔적이 없는지 확인합니다.

## 트러블슈팅 기록

- https://www.notion.so/360df321bd8981e5b31af8acc4f1d2d6
