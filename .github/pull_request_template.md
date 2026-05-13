## 🧭 한눈에 보기

> 이번 PR은 <한 문장 요약>입니다.

| 항목 | 내용 |
| --- | --- |
| 작업 트랙 | `track:` |
| 작업 타입 | `type:` |
| 개발 영역 | `area:` 필요할 때만 |
| 크기 | `size:` |
| 기준 문서 | `docs/LABEL_GUIDE.md` |
| 상태 | CI 확인 전 / CI 통과 / 병합 완료 |
| Notion 기록 | 작업일지 반영 전 / 반영 완료 |

## 🧩 바뀐 내용

- 

## 🔎 리뷰 가이드

- 먼저 볼 곳:
- 가볍게 훑어도 되는 곳:
- 특별히 확인해줬으면 하는 점:

## 📌 PR 범위

- 제목 형식: `[트랙][타입] 명사형 요약`
- 이 PR에 포함한 것:
- 일부러 제외한 것:
- 이 크기로 묶은 이유:

## ✅ 검증 결과

- Backend:
- Worker:
- Runtime:
- 문서/공백:

<details>
<summary>실행한 명령과 근거 보기</summary>

```bash
# 필요한 항목만 남기고 지웁니다.
docker run --rm -v "${PWD}\backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn clean test
docker run --rm -v "${PWD}\worker:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] >/tmp/pip.log && pytest"
docker compose up --build -d
docker compose ps
git diff --check
```

</details>

## ⚠️ 리스크와 후속 작업

- 남은 리스크:
- 운영/데이터 영향:
- 후속 작업:

## 🗂️ Notion 기록

- 작업일지:
- 트러블슈팅:
- 다음 에이전트 메모:

## 🏷️ 라벨/태그 참고

- GitHub/Notion 라벨 의미: `docs/LABEL_GUIDE.md`
- 트랙별 작업 기준: `docs/workstreams/README.md`
