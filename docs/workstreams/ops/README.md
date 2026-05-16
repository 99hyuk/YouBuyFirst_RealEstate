# ops

## 역할

제품 기획, 작업 분리, 트랙 간 조율, 문서, Notion, PR/CI, 배포 정책을 담당합니다. 이 트랙은 다른 구현 트랙이 충돌 없이 일하도록 기준선을 만드는 역할입니다.

이 트랙은 기획/조율만 하는 트랙이 아닙니다. 문서 자동화, Notion 구조, PR 템플릿, CI, 배포/운영 정책처럼 실제 구현 작업도 포함합니다. 다만 사용자 화면 구현은 `front`, 커뮤니티 수집은 `crawl`, 분석 데이터는 `data`, 시세는 `market`, 모의투자는 `trade`, 전략 에이전트는 `agent`가 소유합니다.

## 담당 범위

- 관리자/Swagger 조회 경험
- PR 템플릿과 GitHub Actions
- Notion 작업 로그, 개발자 기술 경험, 에이전트 운영 로그
- 문서 구조와 읽기 우선순위 관리
- 공개 배포 정책
- 인증/인가 도입 시점 설계
- Docker Compose smoke test
- 운영 문서와 인수인계 문서
- 트랙별 PR/Notion 상태 점검
- 트랙 브랜치 사용 여부와 main 통합 시점 조율
- 에이전트 행동 규칙 PR 머지 후 열린 worktree/main 전파 상태 점검
- 개발자 포트폴리오 관점의 문제해결, 성능개선, 품질개선, 기술결정 기록 기준
- 빈 채팅과 짧은 트랙 지시 처리 규칙 관리
- 루트 대시보드, 트랙별 진행판, 제품 기획과 작업 맥락의 정합성 점검

## 파일 소유권

주로 담당:

- `docs/`
- `.github/`
- Docker Compose 운영 문서
- Notion 기록 기준
- 기술 경험 기록 템플릿

공유 전 협의:

- backend API contract
- pipeline payload contract
- DB migration
- front package
- quote/analysis/indicator/trade domain schema

## 현재 우선순위

1. 작업 트랙별 문서와 Notion view 정리
2. 채팅 시작/트랙 선택 원칙과 작업자 응답 틀 관리
3. 문서 길이 관리와 archive 기준 운영
4. 에이전트 행동 규칙 PR의 main 전파와 장기 브랜치 반영 점검
5. 개발자 기술 경험 DB의 문제해결/성능개선/품질개선/기술결정 기록 품질 관리
6. 하이브리드 브랜치 전략 운영
7. 공개 배포 정책 문서화

## 하지 않는 일

- crawler parser 구현
- 반응 지표 산식 구현
- quote provider 내부 구현
- 모의투자 체결 로직 구현
- 사용자 대시보드 UI 구현
