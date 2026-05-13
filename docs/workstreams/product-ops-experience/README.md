# product-ops-experience

## 역할

사용자가 보는 제품 경험과 운영 체계를 담당합니다. 대시보드, 관리자 화면, 문서, Notion, PR/CI, 배포 정책이 이 트랙에 속합니다.

이 트랙은 기획/조율만 하는 트랙이 아닙니다. 사용자용 화면, 프론트 정보 구조, mock 대시보드, 운영 자동화처럼 실제 구현 작업도 포함합니다. 다만 커뮤니티 수집, 감성 산식, 시세 수집, 모의투자 엔진 같은 기능 내부 구현은 각 기능 트랙이 소유합니다.

## 담당 범위

- 사용자용 대시보드
- 관리자/Swagger 조회 경험
- PR 템플릿과 GitHub Actions
- Notion 작업일지와 트러블슈팅 기록
- 공개 배포 정책
- 인증/인가 도입 시점 설계
- Docker Compose smoke test
- 운영 문서와 인수인계 문서

## frontend lane

프론트 작업은 `product-ops-experience` 안의 하위 lane으로 둡니다. 별도 최상위 트랙으로 빼지 않는 이유는 화면 구조가 제품 기획, API 계약, 운영 상태 표시와 강하게 연결되어 있기 때문입니다.

초기 프론트 순서:

1. 정보 구조와 화면 골격: fixture/mock 데이터로 투자 참고 사이트의 첫 화면을 만듭니다.
2. 감성 API 계약 연동: `signal-intelligence`가 ranking/metrics 계약을 잡으면 연결합니다.
3. 시세 API 계약 연동: `market-simulation-engine`의 quote snapshot 계약을 연결합니다.
4. 실시간 polish: WebSocket, stale quote, 로딩/오류 상태를 다듬습니다.
5. 모의투자/에이전트 화면: simulation API가 안정된 뒤 붙입니다.

프론트 PR 규칙:

- 브랜치 prefix는 `codex/product-*`를 씁니다.
- GitHub 라벨은 `stream:product`, `area:frontend`를 함께 붙입니다.
- 실제 API가 없으면 fixture/mock data를 명시하고, API 계약이 생기면 별도 연동 PR로 바꿉니다.
- dashboard shell, component system, chart area, real API integration을 한 PR에 섞지 않습니다.

## 파일 소유권

주로 담당:

- `docs/`
- `.github/`
- frontend 또는 dashboard 패키지
- Docker Compose 운영 문서
- Notion 기록 기준

공유 전 협의:

- backend API contract
- worker payload contract
- DB migration
- quote/sentiment/simulation domain schema

## 현재 우선순위

1. 작업 트랙별 문서와 Notion view 정리
2. 공개 배포 정책 문서화
3. Swagger payload 예시 개선
4. 첫 사용자용 대시보드 정보 구조 설계

## 하지 않는 일

- crawler parser 구현
- 감성 산식 구현
- quote provider 내부 구현
- 모의투자 체결 로직 구현
