# 짧은 트랙명과 에이전트 분리

## 목표

병렬 작업 트랙 이름을 짧고 기억하기 쉬운 한 단어 체계로 바꾸고, 기존 긴 시장/모의투자 트랙에 섞여 있던 시세, 모의투자, 에이전트 역할을 별도 트랙으로 분리합니다.

## 범위

- `crawl`, `data`, `market`, `trade`, `agent`, `front`, `ops` 7트랙 체계 도입
- `docs/workstreams/` 디렉터리명과 README 갱신
- `AGENTS.md`, `CURRENT_HANDOFF.md`, `WORKFLOW.md`, `GIT_CONVENTION.md`, `LABEL_GUIDE.md`, `FINAL_PRODUCT_PLAN.md` 갱신
- GitHub `track:*` 라벨과 Notion `트랙` select 옵션 갱신

## 제외

- 애플리케이션 코드 변경
- 실제 기능 구현
- 기존 PR 기록의 제목 수정

## 결정

- `crawl`: 커뮤니티 글 수집
- `data`: 종목 인식, 감성 분류, 열기 지수, 30분 집계
- `market`: 시세/호가와 quote cache
- `trade`: 모의 계좌, 주문, 체결, 수익률
- `agent`: AI 전략 판단과 결정 로그
- `front`: 사용자 화면
- `ops`: 기획, 문서, Notion, PR/CI, 운영 정책

## 검증 기준

- 오래된 긴 트랙명이 canonical 문서에서 제거됩니다.
- GitHub 라벨과 Notion 트랙 옵션이 새 이름으로 맞춰집니다.
- `git diff --check`가 통과합니다.
