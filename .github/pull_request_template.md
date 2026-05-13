## 요약

- 

## 분류

- 제목 형식: `[타입][영역] 한국어 요약`
- 타입 라벨:
- 영역 라벨:
- 크기 라벨: `size:XS | size:S | size:M | size:L`
- 작은 PR로 유지한 이유:

## 검증

- [ ] `git diff --check`
- [ ] Backend tests: `docker run --rm -v "${PWD}\backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn clean test`
- [ ] Worker tests: `docker run --rm -v "${PWD}\worker:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] >/tmp/pip.log && pytest"`
- [ ] Docker smoke test, if runtime changed: `docker compose up --build -d`

## 리스크와 후속 작업

- 데이터/schema 리스크:
- 크롤링 정책 리스크:
- 후속 작업:
