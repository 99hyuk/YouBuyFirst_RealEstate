# ops

## 역할

제품 기획, 작업 분리, 트랙 간 조율, 문서, Notion, PR/CI, 배포 정책을 담당합니다. 이 트랙은 다른 구현 트랙이 충돌 없이 일하도록 기준선을 만드는 역할입니다.

이 트랙은 기획/조율만 하는 트랙이 아닙니다. 문서 자동화, Notion 구조, PR 템플릿, CI, 배포/운영 정책처럼 실제 구현 작업도 포함합니다. 다만 사용자 화면 구현은 `front`, 커뮤니티 수집은 `crawl`, 분석 데이터는 `data`, 시세는 `market`, 모의투자는 `trade`, 전략 에이전트는 `agent`가 소유합니다.

## 담당 범위

- 관리자/Swagger 조회 경험
- PR 템플릿과 GitHub Actions
- Notion 작업일지와 트러블슈팅 기록
- 문서 구조와 읽기 우선순위 관리
- 공개 배포 정책
- 인증/인가 도입 시점 설계
- Docker Compose smoke test
- 운영 문서와 인수인계 문서
- 트랙별 PR/Notion 상태 점검
- 트랙 브랜치 사용 여부와 main 통합 시점 조율

## 파일 소유권

주로 담당:

- `docs/`
- `.github/`
- Docker Compose 운영 문서
- Notion 기록 기준
- 트러블슈팅 기록 템플릿

공유 전 협의:

- backend API contract
- worker payload contract
- DB migration
- frontend package
- quote/sentiment/simulation domain schema

## 현재 우선순위

1. 작업 트랙별 문서와 Notion view 정리
2. 문서 길이 관리와 archive 기준 운영
3. 트러블슈팅 DB 기록 품질 관리
4. 하이브리드 브랜치 전략 운영
5. 공개 배포 정책 문서화

## 하지 않는 일

- crawler parser 구현
- 감성 산식 구현
- quote provider 내부 구현
- 모의투자 체결 로직 구현
- 사용자 대시보드 UI 구현
