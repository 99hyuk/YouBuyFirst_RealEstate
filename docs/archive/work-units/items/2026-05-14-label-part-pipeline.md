# 2026-05-14 라벨 part 체계와 pipeline 명명 정리

## 한눈에 보기

작업 트랙은 `ops`입니다. GitHub, Notion, 로컬 문서, Python 패키지명이 서로 다른 단어를 쓰지 않도록 정리합니다.

## 바뀐 기준

- GitHub의 `area:*` 라벨은 `part:*` 라벨로 바꿉니다.
- Notion 작업 로그와 다음 작업 DB는 `변경 파트` 컬럼을 씁니다.
- `process`는 `rule`, `worker`는 `pipeline`, `data` 성격의 코드 참조 자산은 `asset`으로 표현합니다.
- 작업 타입은 `feat`, `fix`, `docs`, `refactor`, `perf`, `chore`로 제한합니다.
- `test`, `infra`, `dataset`은 작업 타입이 아니라 변경 파트나 검증 맥락에서 설명합니다.

## 변경 범위

- `worker/` 디렉터리를 `pipeline/`으로 바꾸고 Python import package를 `youbuyfirst_pipeline`으로 정리합니다.
- Docker Compose service와 GitHub Actions job 이름도 `pipeline` 기준으로 맞춥니다.
- `AGENTS.md`, `docs/GIT_CONVENTION.md`, `docs/LABEL_GUIDE.md`, `docs/CURRENT_HANDOFF.md` 등 에이전트가 자주 보는 문서를 최신 라벨 체계로 맞춥니다.
- GitHub 실제 라벨과 Notion DB 속성도 같은 기준으로 갱신합니다.

## 검증 기록

- Pipeline Docker test에서 pytest 4개 통과를 확인했습니다.
- Docker Compose config에서 서비스가 `mysql`, `backend`, `pipeline`으로 잡히는지 확인했습니다.
- GitHub label list에서 `part:*`와 `type:perf`가 보이고, `type:test`, `type:infra`, `type:dataset`이 사라진 것을 확인했습니다.
- Notion 라벨/태그 사전과 작업 로그/다음 작업 DB schema에서 `변경 파트` 옵션을 확인했습니다.
- `git diff --check` 통과를 확인했습니다.

## 트러블슈팅 기록

- Notion schema rename 중 suffix 컬럼이 생긴 문제: https://www.notion.so/360df321bd8981fe8a12fe59190a5329
- `pyproject.toml` UTF-8 BOM 때문에 pip editable install이 실패한 문제: https://www.notion.so/360df321bd8981d597bfdadb48117f16

## 다음 작업자 메모

새 작업을 시작할 때는 `track:*`, `type:*`, `size:*`를 기본으로 붙입니다. `part:*`는 실제 리뷰 경로를 드러낼 때만 붙이면 됩니다. Notion에서는 같은 값을 `변경 파트` 컬럼에 넣습니다.
