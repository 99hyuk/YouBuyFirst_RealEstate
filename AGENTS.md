# 에이전트 작업 가이드

이 파일은 너나사 부동산 프로젝트 전체의 얇은 라우터입니다. 세부 규칙은 담당 도메인/layer `AGENTS.md`, `README.md`, contract 문서에서 확인합니다.

너나사 부동산은 지역과 단지에 대한 실제 사람들의 반응, 뉴스/컬럼 이슈, 실거래/전세/매물 같은 시장 사실 데이터를 함께 보여주는 관찰형 분석 서비스입니다. 기존 YouBuyFirst의 커뮤니티 수집, 반응 분석, 지표화, 유사 과거 비교, 근거 로그 구조를 재사용하되 주식 도메인 안에 부동산을 끼워 넣지 않습니다.

## 읽는 순서

1. 요청을 작업 영역(domain/layer)과 정본 위치로 나눕니다. 작업 영역은 PR 범위와 문서 읽기 경계를 정하는 1차 기준입니다.
2. 이미 대화에 주입된 긴 문서는 터미널로 다시 전문 출력하지 않습니다.
3. 작업 영역이 정해지면 아래 라우팅 표의 담당 `AGENTS.md`를 먼저 보고, 세부 색인이 필요할 때만 같은 폴더의 `README.md`를 봅니다.
4. 제품 방향이 필요하면 `docs/product/REAL_ESTATE_PRODUCT_DIRECTION.md`와 `docs/product/FINAL_PRODUCT_PLAN.md`를 봅니다.
5. 시작할 때 작업 영역, 수정 대상, 기록 위치, 주요 위험을 짧게 말합니다.
6. 범위 없는 `뭐 해야 해?`, `다음 뭐하지?` 요청에는 바로 구현하지 말고 `docs/layers/ops/CHAT_START_GUIDE.md` 기준으로 선택지를 좁힙니다.

## 라우팅

| 요청/작업 영역 | 먼저 볼 곳 | 주 작업 위치 |
| --- | --- | --- |
| `realestate` | `docs/domains/realestate/AGENTS.md` | 지역/단지 모델, 실거래/전세/매물/정책 이벤트, 부동산 데이터 contract |
| `community` (`crawl`) | `docs/domains/community/AGENTS.md` | 공개 수집, 제한 원문 저장, source registry |
| `indicator` | `docs/domains/indicator/AGENTS.md` | 지역/단지 반응 지표, window snapshot, 쟁점 비율 |
| `agent` | `docs/domains/agent/AGENTS.md` | 지역/단지 평가, 근거 로그, 유사 과거 비교 설명 |
| `ui` (`front`) | `docs/layers/ui/AGENTS.md` | `front/`, 화면별 Screen Brief, fixture/API 후보 |
| `ops` | `docs/layers/ops/AGENTS.md` | 문서 구조, Git/PR, Notion, 브랜치/worktree, 컨텍스트 예산 |
| `stock`, `market`, `simulation` | 각 도메인 문서 | 주식 프로젝트에서 넘어온 참고/비활성 영역. 첫 정렬 단계에서 삭제하지 않습니다. |

## 공통 게이트

- 사용자 화면의 기본 언어는 `관찰`, `분석`, `반응 지표`, `쟁점 비율`, `표본 신뢰도`, `근거 로그`입니다.
- 특정 매수, 매도, 청약, 대출 행동을 권유하거나 가격 상승을 단정하는 표현은 서비스 판단, CTA, 제목, 요약 문구에 쓰지 않습니다.
- 커뮤니티 반응은 시장 관찰 데이터로만 표현합니다. 서비스 결론이나 확정 판단처럼 보이게 만들지 않습니다.
- CAPTCHA 우회, 로그인 세션 크롤링, 프록시 회전, fingerprint 위장은 하지 않습니다. 공개 HTTP 수집을 우선하고 Playwright는 렌더링 fallback으로만 씁니다.
- 저장 원문은 제목, 일부 snippet, URL, 작성자 해시, 작성 시각, 원문 해시처럼 필요한 범위로 제한합니다.
- 실거래/전세/매물/정책 데이터는 provider, `asOf`, `stale`, 지연 여부를 분리해서 다룹니다. 확인되지 않은 데이터를 실시간처럼 말하지 않습니다.
- 확인할 수 없는 값은 추측으로 채우지 않고 `unknown`, `null`, `확인 필요`, `mock`처럼 구분합니다.

## 컨텍스트 예산

- 스킬 문서, Browser/gstack, Figma/Stitch, Notion, 세션 로그, archive는 시작 루틴이 아닙니다.
- 큰 문서나 로그는 전문 출력하지 않습니다. `rg -n -m 20`, `Select-Object -First/-Skip`, 관련 섹션 읽기처럼 먼저 좁힙니다.
- Browser/gstack은 front/UI 변경처럼 실제 브라우저 확인 가치가 있을 때 씁니다. 콘솔/DOM 전문 대신 핵심 오류와 화면 경로만 요약합니다.
- Notion은 필요한 page/database 하나씩 확인합니다. 루트, Archive, 전체 DB를 연달아 fetch하지 않습니다.
- 메모리와 과거 대화는 색인입니다. 최신 기준은 repo 문서와 현재 코드입니다.
- 토큰 최적화는 테스트, PR/라벨, Notion 기록 필요성 판단, 필요한 화면 검증을 없애는 근거가 아닙니다.

## 작업, 검증, 기록

- 한 PR은 하나의 primary work area만 소유합니다. 다른 작업 영역 파일을 바꿔야 하면 계약 문서, 작은 선행 PR, 또는 사용자 확인을 먼저 둡니다.
- 실제 수정/PR 후보가 생길 때만 브랜치를 엽니다. 기본 이름은 `codex/<short-task-name>`입니다.
- 작업은 작게 나누되, 사용자 승인이 꼭 필요한 결정이 아니면 구현하고 검증합니다.
- 문서만 바꿔도 `git diff --check`를 실행합니다. 코드 변경은 해당 테스트/빌드/스모크 테스트를 실행하고, front/UI 변경은 가능한 경우 Browser/gstack으로 확인합니다.
- PR 제목과 merge 제목은 기술 고유명사를 제외하고 한국어 명사형으로 씁니다. PR 생성/ready/merge 전에는 사람 리뷰와 `chatgpt-codex-connector` 같은 자동 리뷰의 actionable 의견을 확인하고, 리뷰가 필요한 PR은 생성 직후 바로 처리하지 말고 review 상태로 둔 뒤 재확인합니다. 처리 기준은 `docs/layers/ops/GIT_CONVENTION.md`의 리뷰 확인 규칙을 따릅니다.
- 현재 상태는 `docs/current/`, 제품 결정은 `docs/product/`, 도메인 contract는 `docs/domains/`, UI 화면 기준은 `docs/layers/ui/screens/`, 운영 규칙은 `docs/layers/ops/`, 리스크는 `docs/governance/`에 둡니다.
- front 화면 구조나 문구 기준이 바뀌면 사용자의 별도 기록 지시가 없어도 해당 Screen Brief를 갱신합니다.
- 개발자 취업/포트폴리오에 쓸 수 있는 제품 개발 문제해결, 성능/품질 개선, 기술 의사결정은 `docs/layers/ops/ENGINEERING_EVIDENCE_GUIDE.md` 기준으로 Notion 개발자 기술 경험 DB에 남깁니다.
- PR/라벨/브랜치/worktree/Notion 세부 규칙은 `docs/layers/ops/AGENTS.md`와 관련 ops 문서의 필요한 섹션만 봅니다.

## 보고 방식

- 파일명, 폴더명, 명령어 나열보다 무엇이 해결됐고 사용자가 무엇을 판단하면 되는지 먼저 말합니다.
- 답변은 `쉬운 결론 -> 왜 중요한지 -> 사용자가 할/판단할 일 -> 필요한 기술 근거` 순서로 씁니다. 기술 용어를 처음 쓰면 바로 옆에 쉬운 뜻을 붙입니다.
- provider, API, 아키텍처가 걸린 작업은 역할, 응답 shape, 호출 예시, 캐시/지연/stale 기준을 먼저 설명합니다.
- 완료 보고에는 무엇이 바뀌었는지, 검증 결과, 남은 리스크, 다음 행동을 짧게 포함합니다.
