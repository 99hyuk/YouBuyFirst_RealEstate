# Git/PR 컨벤션

이 저장소는 사용자가 직접 스크립트를 실행하는 흐름을 쓰지 않습니다. Codex 또는 작업 에이전트가 `git`과 `gh`를 직접 사용해 브랜치 생성, 커밋, push, PR 생성, CI 확인, merge를 처리합니다.

## 기본 원칙

- PR 하나는 기능 하나, 버그 하나, 문서 정리 하나, 인프라 변경 하나만 담습니다.
- 큰 기능은 반드시 여러 PR로 쪼갭니다.
- PR 설명과 커밋 본문은 한국어로 작성합니다.
- 코드 식별자, 명령어, API 경로, 파일명은 원문 그대로 씁니다.
- `main`에 직접 push하지 않습니다. 항상 `codex/<작업명>` 브랜치를 사용합니다.
- CI 통과 전에는 merge하지 않습니다.

## PR 제목 규칙

형식:

```text
[타입][영역] 한국어 요약
```

예시:

```text
[feat][backend] 커뮤니티 게시글 중복 저장을 방지한다
[fix][worker] 에펨코리아 게시글 시간 파싱을 보정한다
[docs][process] PR 크기와 라벨 규칙을 정리한다
[infra][ci] 백엔드와 워커 테스트 워크플로를 분리한다
```

## 타입 태그

- `[feat]`: 사용자나 시스템의 새 동작 추가
- `[fix]`: 버그 수정
- `[docs]`: 문서만 변경
- `[test]`: 테스트 추가 또는 테스트 구조 변경
- `[refactor]`: 동작 변경 없는 구조 개선
- `[infra]`: Docker, CI, 배포, 개발 환경
- `[data]`: 종목 마스터, seed, fixture 같은 데이터 변경
- `[chore]`: 기타 유지보수

## 영역 태그

- `[backend]`: Spring Boot, DB schema, API, JPA
- `[worker]`: Python crawler, matcher, LLM provider
- `[ci]`: GitHub Actions, 테스트 실행 환경
- `[docs]`: README, 기획, 작업 문서
- `[process]`: 작업 방식, 컨벤션, 인수인계
- `[data]`: 종목 마스터, fixture, seed
- `[runtime]`: Docker Compose, 환경 변수, 로컬 실행

## GitHub 라벨 규칙

PR을 만들 때 제목 태그와 같은 의미의 라벨을 붙입니다.

타입 라벨:

- `type:feat`
- `type:fix`
- `type:docs`
- `type:test`
- `type:refactor`
- `type:infra`
- `type:data`
- `type:chore`

영역 라벨:

- `area:backend`
- `area:worker`
- `area:ci`
- `area:docs`
- `area:process`
- `area:data`
- `area:runtime`

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
[타입][영역] 한국어 요약
```

커밋 본문이 필요하면 한국어로 씁니다.

```text
[fix][worker] 에펨코리아 시간 파싱을 보정한다

상대 시간과 당일 시각 표기를 KST 기준으로 정규화한다.
기존 fixture를 확장해 중복 URL 제거도 함께 검증한다.
```

## PR 본문 규칙

PR 본문은 다음을 반드시 포함합니다.

- 무엇을 바꿨는지
- 왜 이 크기로 묶었는지
- 검증 명령과 결과
- 남은 리스크
- 후속 작업이 있다면 명시

## Merge 규칙

- CI가 모두 통과하면 Codex가 사용자를 대신해 merge할 수 있습니다.
- 기본 merge 방식은 squash merge입니다.
- merge 제목과 본문은 한국어로 정리합니다.
- merge 후 브랜치는 삭제합니다.
