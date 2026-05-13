# 작업 단위: 프론트 lane과 market 내부 lane 정리

## 목적

프론트 작업을 언제 시작할지, 누가 담당할지, `market-simulation-engine` 안에서 시세 수집과 모의투자/에이전트를 어떻게 나눌지 명확히 합니다.

후속 결정으로 프론트는 `product-ops-experience`의 하위 lane이 아니라 `frontend-experience` 독립 트랙으로 분리했습니다. 최신 기준은 `docs/workstreams/README.md`와 `docs/workstreams/frontend-experience/README.md`를 우선합니다.

## 범위

- `frontend-experience` 독립 트랙 기준 추가
- `market-simulation-engine`에 `market-data`, `simulation-core`, `agent-runtime` lane 추가
- Git/PR 컨벤션에 `area:frontend` 기준 추가
- 작업 목록과 공통 워크플로 갱신

## 제외

- 프론트 프로젝트 생성
- quote provider 구현
- 모의투자 엔진 구현
- AI 에이전트 구현

## 다음 작업자 메모

프론트는 API 완성 후 마지막에 몰아서 하지 않습니다. 먼저 `frontend-experience` 트랙에서 fixture/mock 기반 대시보드 shell을 만들고, signal/market/simulation 계약이 생길 때마다 작은 연동 PR로 붙입니다.
