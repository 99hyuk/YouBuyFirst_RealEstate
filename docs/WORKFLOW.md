# 보수적 개발 워크플로

이 문서는 작업을 빠뜨리지 않기 위한 실행 체크리스트입니다. 자세한 PR 문구와 라벨 의미는 `docs/GIT_CONVENTION.md`, `docs/LABEL_GUIDE.md`의 필요한 섹션만 확인합니다.

## 원칙

- 기능 하나, 버그 하나, 문서 정리 하나, CI/runtime 설정 변경 하나는 PR 하나로 끝냅니다.
- 무관한 backend, pipeline, front, ops 변경을 한 PR에 섞지 않습니다.
- 트랙 이름은 작업 관리 단위이고, 코드 패키지는 도메인 단위입니다.
- 사용자의 요구가 제품 목표, 법적/운영 리스크, 트랙 경계, 검증 가능성, 문서 보존 원칙과 충돌하면 먼저 질문하거나 반박합니다.
- 토큰 최적화는 필수 행동을 없애기 위한 근거가 아닙니다. 전문 읽기와 큰 출력만 줄입니다.
- 사용자 보고는 파일/폴더/명령어 나열보다 사람이 이해할 변화, 판단 포인트, 다음 행동을 먼저 말합니다.

## 작업 시작

1. `AGENTS.md`, `docs/CURRENT_HANDOFF.md`, `docs/DOCUMENTATION_GUIDE.md`는 필요한 섹션만 확인합니다.
2. 트랙이 명확하면 담당 트랙 README를 먼저 확인합니다.
3. 트랙 경계가 헷갈릴 때만 `docs/workstreams/README.md`를 봅니다.
4. 제품 방향이 필요한 경우에만 `docs/FINAL_PRODUCT_PLAN.md`의 관련 섹션을 봅니다.
5. 작업 트랙, 수정 대상, 기록 위치, 주요 위험을 짧게 선언합니다.
6. 루트 checkout이 아니라 `.worktrees/<task>`에서 작업합니다.
7. 장기 브랜치에서 작업을 재개할 때는 `origin/main`보다 뒤처졌는지 확인합니다. `AGENTS.md`, `CURRENT_HANDOFF.md`, `DOCUMENTATION_GUIDE.md`, `WORKFLOW.md`, `CHAT_START_GUIDE.md`, `docs/workstreams/*/README.md` 같은 에이전트 행동 규칙 문서가 main에 새로 들어왔으면 먼저 main을 병합합니다.

빈 채팅에서 `뭐 해야 해?`, `다음 뭐하지?`처럼 범위 없이 물으면 바로 구현하지 않고 `docs/CHAT_START_GUIDE.md` 기준으로 트랙 선택을 돕습니다.

## 브랜치 생명주기

새 브랜치는 변경이 필요한 작업에만 엽니다. 단순 확인, PR 상태 점검, 로그 요약, 사용자 질문 답변은 현재 checkout에서 읽기 전용으로 처리합니다.

열기 전 확인:

1. 작업 트랙과 예상 PR 제목이 있는가?
2. 수정할 파일 소유권이 한 트랙 안에 있는가?
3. 이미 같은 목적의 활성 브랜치가 있지 않은가?
4. 작업이 끝나면 merge, close, handoff 중 어떤 상태가 될지 설명할 수 있는가?

작업 중 유지:

- active, review, blocked, stale, close-candidate 중 하나로 상태를 설명할 수 있어야 합니다.
- main보다 뒤처진 장기 브랜치는 작업 재개 전에 main 반영 여부를 봅니다.
- dirty worktree는 임의로 닫거나 병합하지 않습니다. 남은 변경과 필요한 조치를 먼저 보고합니다.

닫는 기준:

- merge 완료: 원격 브랜치와 worktree 삭제
- close 완료: 살릴 조각이 없으면 브랜치와 worktree 삭제
- 대체 PR 존재: 필요한 조각만 새 작은 PR로 옮기고 기존 브랜치 정리
- 1일 이상 방치: ops가 `close-candidate`로 분류하고 다음 행동을 정합니다.

정리 책임:

- 작업 에이전트는 자기 작업이 merge/close/대체되면 브랜치와 worktree 정리 여부를 확인합니다.
- clean 상태이고 살릴 변경이 없으면 작업 에이전트가 직접 정리합니다.
- dirty 상태, 미반영 커밋, dev server 실행, 살릴 변경이 있으면 삭제하지 않고 사용자/ops/해당 트랙에 상태를 남깁니다.
- ops는 정리 누락을 주기적으로 점검하지만, 작업 에이전트의 종료 책임을 대신하는 기본 루틴은 아닙니다.

브랜치 정리 때도 출력은 줄입니다. 전체 diff를 먼저 보지 말고 `git branch -vv --sort=-committerdate`, `git worktree list`, `gh pr list --state open`의 요약으로 시작합니다.

## 에이전트 규칙 전파

ops는 에이전트 행동 규칙 PR을 main에 머지한 뒤 열린 worktree 전파 상태를 확인합니다.

1. `git worktree list`와 `git rev-list --left-right --count HEAD...origin/main`으로 열린 브랜치의 ahead/behind를 봅니다.
2. clean 상태인 활성 브랜치는 `origin/main` 병합을 진행할 수 있습니다.
3. dirty 상태인 브랜치는 임의 병합하지 않고, 브랜치명과 필요한 조치를 사용자 또는 해당 트랙 에이전트에게 남깁니다.
4. 규칙 전파 대상은 우선 front/crawl/data/market/trade/agent 같은 장기 작업 브랜치입니다. 이미 머지되었거나 폐기 예정인 ops 보조 브랜치는 정리 후보로 둡니다.
5. 전파 결과는 완료 보고나 PR 본문에 남깁니다.

## 구현 중

- 해당 작업만 구현합니다.
- 다른 트랙의 파일이나 계약을 바꿔야 하면 먼저 범위와 리스크를 확인합니다.
- 스킬 문서는 실제로 적용할 때만 필요한 절차를 확인합니다.
- gstack은 front/UI 변경, 라우팅, 콘솔, 반응형처럼 실제 브라우저 확인 가치가 있을 때 사용합니다.
- 로그/세션/Notion fetch는 디버깅이나 구조 변경처럼 필요할 때만 대상 하나씩 확인합니다.

## 필수 검증

- 관련 테스트를 실행합니다.
- 문서만 바꿔도 `git diff --check`를 실행합니다.
- front/UI 변경은 가능하면 gstack/browser로 화면, 콘솔, 반응형을 확인합니다.
- PR 생성/수정 후 `gh pr view --json body --jq .body`로 본문 저장 상태를 확인합니다.
- 한국어 본문에 `??` 치환 문자열이 보이면 merge 전에 고칩니다.

## PR 전 체크리스트

1. 변경 범위가 한 작업/한 트랙인지 확인합니다.
2. 관련 테스트와 `git diff --check` 결과를 확인합니다.
3. PR 제목은 `[트랙][타입] 명사형 요약`으로 씁니다.
4. `track:*`, `type:*`, `size:*` 라벨을 붙입니다.
5. 필요한 경우에만 `part:*` 라벨을 붙입니다.
6. PR 본문은 UTF-8 no BOM 파일과 `gh --body-file <path>`를 사용합니다.
7. PR 본문에는 변경 내용, 범위, 검증 결과, 리스크, Notion 기록 여부를 적습니다.

## Notion 기록

Notion은 무조건 전체 fetch하지 않습니다. 필요한 page/database 하나씩 확인합니다.

- 작업 로그 DB: PR별 요약 기록
- 개발자 기술 경험 DB: 제품 개발/운영 문제, 성능 개선, 품질 개선, 기술 결정
- 에이전트 운영 로그 DB: Codex, Notion, GitHub PR, 문서 운영 사고

문서/ops 최적화처럼 Notion fetch가 오히려 비용과 리스크를 늘리는 경우에는 PR 본문에 `Notion 미기록`과 이유를 남길 수 있습니다.

## Notion 구조 변경 게이트

Notion 루트, 홈카드, 주요 DB 페이지, 제품 기획, 작업 진행, 기술 경험 기록, 에이전트 운영 로그, Archive 변경은 일반 문서 수정이 아니라 사용자용 정보 구조 변경입니다.

1. 변경 전 대상 page/database를 확인합니다.
2. child page/database 링크 보존 여부를 확인합니다.
3. 사용자 화면 개선인지, 에이전트 운영 규칙 정리인지 분리합니다.
4. 큰 구조 변경은 후보안이나 작은 섹션 변경으로 시작합니다.
5. `replace_content`와 `allow_deleting_content`는 최후 수단입니다.
6. 제품 기획, 작업 로그, 기술 경험 기록, 에이전트 운영 로그의 목적을 섞지 않습니다.
7. 변경 후 루트와 핵심 카드 2개 이상을 다시 확인합니다.

## 문서 미준수 사고 게이트

사용자가 "문서에 있는데 왜 안 따랐냐", "이전 원칙과 다르다", "멋대로 바꿨다"라고 지적하면 즉시 아래를 확인합니다.

1. 어떤 문서, 섹션, 원칙을 놓쳤는가?
2. 읽지 않은 문제인가, 해석 오류인가, 검증 누락인가?
3. Notion child page/database, PR 본문, git 변경, 작업 로그, 제품 기획 문서에 손상이 있는가?
4. 복구가 필요한가, 보정만 하면 되는가, 사용자 확인이 필요한가?
5. 재발 방지 규칙을 repo 문서나 에이전트 운영 로그에 남겨야 하는가?

## 완료 보고

완료 보고는 파일명보다 사용자가 판단할 수 있게 된 것을 먼저 말합니다.

- 무엇이 해결됐는지
- 사용자가 이제 무엇을 결정하면 되는지
- 포함 범위와 제외 범위
- 검증 결과
- PR/브랜치/Notion 상태
- Superpowers/gstack 사용 여부와 이유

gstack을 쓰지 않았다면 `gstack 미사용: 문서/backend 작업이라 브라우저 확인 대상 없음`처럼 이유를 적습니다.

## 문서 길이 관리

- `AGENTS.md`와 `CURRENT_HANDOFF.md`는 짧은 시작 문서로 유지합니다.
- 오래된 완료 내역은 `docs/work-units/`나 archive 성격 문서로 보냅니다.
- 세부 설명은 필요한 문서에 두고, 시작 루틴에는 넣지 않습니다.
- 문서 구조와 확인 우선순위는 `docs/DOCUMENTATION_GUIDE.md`를 따릅니다.
- 시작 문서나 트랙 문서를 바꾸는 PR은 컨텍스트 예산을 확인합니다.
- 예산을 줄일 때도 미완료 작업, 테스트, PR/라벨, Notion/gstack 필요성 판단은 삭제하지 않습니다.
