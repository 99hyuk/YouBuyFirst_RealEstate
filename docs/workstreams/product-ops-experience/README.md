# product-ops-experience

## 역할

사용자가 보는 제품 경험과 운영 체계를 담당합니다. 대시보드, 관리자 화면, 문서, Notion, PR/CI, 배포 정책이 이 트랙에 속합니다.

## 담당 범위

- 사용자용 대시보드
- 관리자/Swagger 조회 경험
- PR 템플릿과 GitHub Actions
- Notion 작업일지와 트러블슈팅 기록
- 공개 배포 정책
- 인증/인가 도입 시점 설계
- Docker Compose smoke test
- 운영 문서와 인수인계 문서

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
