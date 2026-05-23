# ops layer 작업 지침

ops layer는 문서 구조, Git/PR, Notion 기록, 트랙/라벨, 브랜치/worktree 생명주기, 컨텍스트 예산을 소유합니다.

## 시작

- 문서 구조와 읽기 게이트는 `DOCUMENTATION_GUIDE.md`를 봅니다.
- 브랜치, PR, 템플릿, 라벨 작업은 `GIT_CONVENTION.md`와 `LABEL_GUIDE.md`의 관련 섹션만 봅니다.
- 트랙 경계가 헷갈리면 `TRACKS.md`를 봅니다.
- 빈 채팅 시작 방식은 `CHAT_START_GUIDE.md`를 봅니다.

## 경계

- ops는 다른 도메인 결정을 대신 확정하지 않습니다. 필요한 경우 해당 도메인 AGENTS/README와 contract 문서로 연결합니다.
- 문서 최적화는 테스트, PR 규칙, Notion 기록, 필요한 화면 검증을 생략하는 근거가 아닙니다.
- 오래된 기록은 삭제보다 archive 이동이나 검색 가능한 요약을 우선합니다.
- 루트 `AGENTS.md`는 전체 라우터로 유지합니다. 세부 PR, Notion, 컨텍스트 예산, 브랜치/worktree 규칙은 이 layer 문서로 내려보내고 루트에 길게 복제하지 않습니다.

## 게이트

- Notion 루트, 홈카드, 주요 DB 페이지, 제품 기획, 작업 진행, 기술 경험 기록, 에이전트 운영 로그, Archive 변경은 사용자용 정보 구조 변경입니다. 변경 전 대상과 child link 보존 여부를 확인합니다.
- PR/브랜치/라벨/템플릿 작업은 `GIT_CONVENTION.md`와 `LABEL_GUIDE.md`를 기준으로 하고, 문서만 바꿔도 `git diff --check`를 실행합니다.
- 시작 문서나 트랙 문서를 바꾸면 `DOCUMENTATION_GUIDE.md`의 컨텍스트 예산 기준을 확인합니다.

## 기록

- 새 문서 규칙은 중복 파일을 늘리기보다 루트 `AGENTS.md`, 이 문서, `DOCUMENTATION_GUIDE.md` 중 맞는 위치에 짧게 합칩니다.
- Codex/Notion/PR/문서 운영 사고는 에이전트 운영 로그 DB로, 제품 개발/기술 결정은 개발자 기술 경험 DB로 분리합니다.
- 작업 브랜치와 worktree는 머지/폐기 후 정리 후보로 확인합니다.
