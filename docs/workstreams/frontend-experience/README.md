# frontend-experience

## 역할

사용자가 실제로 보는 너나사 (YouBuyFirst)의 화면 경험을 담당합니다. 이 트랙은 대시보드, mock data, 차트, 사용자 흐름, API 연동, 로딩/오류/빈 상태를 소유합니다.

프론트는 모든 백엔드가 끝난 뒤 마지막에 몰아서 하지 않습니다. 먼저 fixture/mock 기반으로 투자 참고 사이트의 골격을 만들고, 각 기능 트랙의 API 계약이 생길 때마다 작은 PR로 연결합니다.

## 담당 범위

- 사용자용 대시보드 shell
- 종목/커뮤니티 감성 랭킹 화면
- 열기 지수, 감성 비율, 대표 키워드 표시
- 가격, 등락률, 거래량, stale quote 상태 표시
- 커뮤니티별 수익률 비교 화면
- 모의투자/에이전트 리더보드 화면
- fixture/mock data
- API contract 기반 client adapter
- 로딩, 오류, 빈 상태
- 반응형 레이아웃과 접근성 기본값

## 파일 소유권

주로 담당:

- frontend 또는 dashboard 패키지
- frontend fixture/mock data
- frontend client adapter
- UI component와 page layout
- frontend 테스트

공유 전 협의:

- backend API contract
- metrics API response
- quote snapshot response
- simulation/agent API response
- 문서/Notion/PR 운영 기준

## 초기 작업 순서

1. 대시보드 정보 구조와 라우팅 후보 설계
2. fixture/mock 기반 dashboard shell 구현
3. 감성 ranking/metrics API 계약 연결
4. quote snapshot API 계약 연결
5. 커뮤니티별 수익률 비교 화면 연결
6. 모의투자/AI 에이전트 화면 연결

## PR 규칙

- 브랜치 prefix는 `codex/frontend-*`를 씁니다.
- GitHub 라벨은 `stream:frontend`, `area:frontend`를 함께 붙입니다.
- 실제 API가 없으면 fixture/mock data를 명시합니다.
- dashboard shell, component system, chart area, real API integration을 한 PR에 섞지 않습니다.
- UI 구현 PR은 가능하면 스크린샷 또는 브라우저 검증 결과를 PR 본문에 남깁니다.

## 하지 않는 일

- crawler parser 구현
- 감성 산식 구현
- quote provider 내부 구현
- 모의투자 체결 로직 구현
- GitHub/Notion 운영 자동화
