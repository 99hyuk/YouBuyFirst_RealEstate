# front

## 역할

사용자가 실제로 보는 너나사 (YouBuyFirst)의 화면 경험을 담당합니다. 이 트랙은 대시보드, mock data, 차트, 사용자 흐름, API 연동, 로딩/오류/빈 상태를 소유합니다.

프론트는 모든 백엔드가 끝난 뒤 마지막에 몰아서 하지 않습니다. 먼저 fixture/mock 기반으로 투자 참고 사이트의 골격을 만들고, 각 기능 트랙의 API 계약이 생길 때마다 작은 PR로 연결합니다.

## 현재 프론트 전략

초기 프론트는 최종 디자인이 아니라 `저충실도 와이어프레임`으로 시작합니다. 목표는 예쁜 화면을 먼저 만드는 것이 아니라, 사용자가 실제로 볼 정보 구조와 라우팅, mock data, API 계약 후보, 빠진 기획 질문을 드러내는 것입니다.

- 기술 선택은 `Vue 3 + Vite + TypeScript` SPA를 기본으로 둡니다.
- 라우팅은 `Vue Router`를 기준으로 설계합니다.
- 서버 데이터 연동 방식은 실제 API 계약이 생긴 뒤 별도 PR에서 확정합니다.
- 디자인 시스템, 브랜드 컬러, 일러스트, 고충실도 UI는 후순위입니다.
- Figma AI, Stitch 같은 디자인 도구는 시안 탐색용으로만 쓰고, 초기 구현의 정본은 repo 코드와 문서입니다.
- 차트 라이브러리는 대시보드 정보 구조와 데이터 형태를 먼저 본 뒤 확정합니다.

프론트 에이전트는 화면을 만들면서 기획을 임의로 확정하지 않습니다. 애매한 지표, 화면 문구, API 응답, 사용자 행동은 `기획자 확인 필요` 항목으로 남기고, mock 화면은 그 경계를 명시한 상태로 진행합니다.

현재 `front/`에는 Vue 3 + Vite + TypeScript 기반 mock 와이어프레임 shell이 있습니다. 실제 backend API 연결, 차트 라이브러리 확정, 고충실도 디자인은 아직 하지 않았습니다.

## 프론트 에이전트 시작 지시

사용자가 새 채팅에서 `front 작업`, `프론트 맡아줘`, `화면 와이어프레임 해줘`처럼 짧게 말하면 아래 지시를 사용자가 다시 붙여 넣지 않아도 프론트 에이전트가 스스로 적용합니다.

```text
너는 너나사 (YouBuyFirst)의 front 담당 에이전트다.
AGENTS.md, docs/CURRENT_HANDOFF.md, docs/DOCUMENTATION_GUIDE.md,
docs/workstreams/README.md, docs/workstreams/front/README.md를 읽는다.

이번 front 작업의 기본값은 Vue 3 + Vite + TypeScript 기반 저충실도 와이어프레임이다.
목표는 화면 구조, 라우팅, mock data, API 계약 후보, 기획자 확인 필요 항목을 드러내는 것이다.
브랜드 디자인, 고충실도 UI, 최종 컬러, 일러스트, 디자인 툴 산출물 고정은 하지 않는다.

작업 중 기획이 불명확한 부분은 임의로 확정하지 말고 "기획자 확인 필요"로 문서와 PR에 남긴다.
작업 하나는 브랜치 하나와 PR 하나로 만들고, PR 설명과 작업 기록은 한국어로 작성한다.
```

## 담당 범위

- 사용자용 대시보드 shell
- 종목/커뮤니티 반응 랭킹 화면
- 열기 지수, 반응 방향 비율, 대표 키워드 표시
- 가격, 등락률, 거래량, stale quote 상태 표시
- 커뮤니티별 수익률 비교 화면
- 모의투자/에이전트 리더보드 화면
- fixture/mock data
- API contract 기반 client adapter
- 로딩, 오류, 빈 상태
- 반응형 레이아웃과 접근성 기본값

## 파일 소유권

주로 담당:

- front 또는 dashboard 패키지
- front fixture/mock data
- front client adapter
- UI component와 page layout
- front 테스트

공유 전 협의:

- backend API contract
- indicator API response
- quote snapshot response
- trade/agent API response
- 문서/Notion/PR 운영 기준

## 초기 작업 순서

1. 화면 인벤토리와 라우팅 후보 설계 완료
2. mock data와 API 응답 후보 정리 완료
3. fixture/mock 기반 dashboard shell 구현 완료
4. 브라우저 QA와 기획자 확인 필요 항목 정리
5. 메인 대시보드 와이어프레임 보강
6. 종목 상세/커뮤니티 반응 와이어프레임 보강
7. 시세/모의투자/AI 에이전트 화면 초안
8. analysis ranking/indicator API 계약 연결
9. quote snapshot API 계약 연결
10. 커뮤니티별 수익률 비교 화면 연결
11. 모의투자/AI 에이전트 화면 연결

## PR 규칙

- 브랜치 prefix는 `codex/front-*`를 씁니다.
- GitHub 라벨은 `track:front`를 붙입니다. 화면 파일을 직접 바꾸면 `part:front`도 함께 붙입니다.
- 실제 API가 없으면 fixture/mock data를 명시합니다.
- dashboard shell, component system, chart view, real API integration을 한 PR에 섞지 않습니다.
- PR 본문에는 `기획자 확인 필요` 항목을 별도로 두고, 임의 확정한 부분이 없었는지 적습니다.
- UI 구현 PR은 가능하면 스크린샷 또는 브라우저 검증 결과를 PR 본문에 남깁니다.

## 하지 않는 일

- crawler parser 구현
- 반응 지표 산식 구현
- quote provider 내부 구현
- 모의투자 체결 로직 구현
- GitHub/Notion 운영 자동화
- 최종 브랜드 디자인 확정
- Figma AI/Stitch 산출물을 정본처럼 고정
