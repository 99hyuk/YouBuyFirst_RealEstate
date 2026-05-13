## 🧭 한눈에 보기

> 이번 PR은 <한 문장 요약>

| 항목 | 내용 |
| --- | --- |
| 타입 | `type:` |
| 영역 | `area:` |
| 트랙 | `stream:` |
| 크기 | `size:` |
| 상태 | CI 확인 전 |
| Notion 기록 | 작업일지 반영 전 |

## 🧩 바뀐 내용

- 

## 🔎 리뷰 가이드

- 먼저 볼 곳:
- 가볍게 훑어도 되는 곳:
- 특별히 확인해줬으면 하는 점:

## 📦 왜 이 단위인가

- 제목 형식: `[타입][영역] 한국어 요약`
- 트랙 구분: `stream:data` / `stream:signal` / `stream:market` / `stream:frontend` / `stream:product`
- 이 범위로 묶은 이유:
- 분리하지 않았다면 그 이유:

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
