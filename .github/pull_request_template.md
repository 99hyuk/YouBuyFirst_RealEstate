<!--
PR template guard:
- 이 파일을 복사해서 채웁니다. 기억으로 비슷하게 다시 쓰지 않습니다.
- 아래 ## 섹션 제목은 삭제하거나 이름을 바꾸지 않습니다.
- 해당 없는 항목도 지우지 말고 `해당 없음` 또는 `Notion 미기록: <이유>`처럼 남깁니다.
- 생성/수정 직후 `docs/layers/ops/GIT_CONVENTION.md`의 PR 본문 감사 명령으로 섹션 누락과 물음표 두 개 치환 깨짐을 확인합니다.
-->

## 🧭 한눈에 보기

> 이번 PR은 <한 문장 요약>입니다.
> 파일명이나 기술명보다 사용자가 무엇을 판단할 수 있게 되었는지, 제품/운영 흐름이 어떻게 달라졌는지를 먼저 적습니다.

| 항목 | 내용 |
| --- | --- |
| 작업 영역 | `track:<realestate/community/indicator/agent/ui/ops>` |
| 작업 타입 | `type:` |
| 변경 파트 | `part:` 필요할 때만 |
| 크기 | `size:` |
| 기준 문서 | `docs/layers/ops/LABEL_GUIDE.md` |
| 상태 | CI 확인 전 / CI 통과 / 병합 완료 |
| Notion 기록 | 작업일지 반영 전 / 반영 완료 |
| 트러블슈팅 | 해당 없음 / 상세 기록 링크 |
| 템플릿 확인 | 원본 섹션 유지 / 보정 필요 |

## 🧩 바뀐 내용

- 

<!-- 파일 목록 대신 사람이 이해할 수 있는 변화 단위로 적습니다. 예: `DashboardPage.vue 수정`보다 `대시보드에서 커뮤니티 반응과 주요 지표를 한 번에 비교할 수 있게 함` -->

## 🔎 리뷰 가이드

- 먼저 볼 곳:
- 가볍게 훑어도 되는 곳:
- 특별히 확인해줬으면 하는 점:

<!-- 파일 경로, 브랜치명, 내부 구현명은 이 섹션이나 details에 보조 정보로 둡니다. -->

## 📌 PR 범위

- 제목 형식: `[작업영역][타입] 한국어 명사형 요약`
- 이 PR에 포함한 것:
- 일부러 제외한 것:
- 이 크기로 묶은 이유:

## ✅ 검증 결과

- Backend:
- Pipeline:
- Runtime:
- 문서/공백:

<details>
<summary>실행한 명령과 근거 보기</summary>

```bash
# 필요한 항목만 남기고 지웁니다.
docker run --rm -v "${PWD}\backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn clean test
docker run --rm -v "${PWD}\pipeline:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] >/tmp/pip.log && pytest"
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
- 트러블슈팅: 해당 없음 / 기록 링크 (`docs/governance/TROUBLESHOOTING_GUIDE.md` 기준)
- 다음 에이전트 메모:

## 🏷️ 라벨/태그 참고

- GitHub/Notion 라벨 의미: `docs/layers/ops/LABEL_GUIDE.md`
- 작업 영역 기준: `docs/layers/ops/WORK_AREAS.md`
