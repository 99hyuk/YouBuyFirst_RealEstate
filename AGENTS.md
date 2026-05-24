# 에이전트 작업 가이드

이 파일은 너나사(YouBuyFirst) 전체의 얇은 라우터입니다. 세부 규칙은 담당 도메인/layer `AGENTS.md`, `README.md`, contract 문서에서 확인합니다.

너나사는 커뮤니티 반응, 종목 언급량, 시세/수급, 모의투자 에이전트를 결합해 "개미들의 투자 반응을 읽는 참고 서비스"를 만듭니다. 실제 투자 자문, 실거래 지시, 수익 보장, 개인화 투자 권유처럼 보이는 기능과 표현은 피합니다.

## 읽는 순서

1. 요청을 작업 영역(domain/layer)과 정본 위치로 나눕니다. 작업 영역은 PR 범위와 문서 읽기 경계를 정하는 1차 기준입니다.
2. 이미 대화에 주입된 긴 문서는 터미널로 다시 전문 출력하지 않습니다.
3. `docs/current/HANDOFF.md`는 필요한 줄만 확인합니다. 제품 방향이 필요할 때만 `docs/product/FINAL_PRODUCT_PLAN.md`의 관련 섹션을 봅니다.
4. 작업 영역이 정해지면 아래 라우팅 표의 담당 `AGENTS.md`를 먼저 보고, 세부 색인이 필요할 때만 같은 폴더의 `README.md`를 봅니다.
5. 시작할 때 작업 영역, 수정 대상, 기록 위치, 주요 위험을 짧게 말합니다.
6. 범위 없는 `뭐 해야 해?`, `다음 뭐하지?` 요청에는 바로 구현하지 말고 `docs/layers/ops/CHAT_START_GUIDE.md` 기준으로 선택지를 좁힙니다.

## 라우팅

| 요청/작업 영역 | 먼저 볼 곳 | 주 작업 위치 |
| --- | --- | --- |
| `community` (`crawl`) | `docs/domains/community/AGENTS.md` | `pipeline/`, 수집 정책, source registry |
| `stock` (`data` 일부) | `docs/domains/stock/AGENTS.md` | 종목 master, symbol, alias, 종목 식별 |
| `indicator` (`data` 일부) | `docs/domains/indicator/AGENTS.md` | 반응 방향 집계, 열기 지수, 개미 심리 지수 |
| `market` | `docs/domains/market/AGENTS.md` | 시세, 차트 캔들, 수급, provider/cache |
| `simulation` (`trade`) | `docs/domains/simulation/AGENTS.md` | 가상 계좌, 주문, 체결, 원장, 수익률 |
| `agent` | `docs/domains/agent/AGENTS.md` | AI 판단, paper trading 결정 로그, 헤드라인 |
| `ui` (`front`) | `docs/layers/ui/AGENTS.md` | `front/`, 화면별 Screen Brief, fixture/API 후보 |
| `ops` | `docs/layers/ops/AGENTS.md` | 문서 구조, Git/PR, Notion, 브랜치/worktree, 컨텍스트 예산 |

## 공통 게이트

- 사용자 화면의 기본 언어는 `커뮤니티 반응`, 단일 분석값은 `반응 방향`, 대표 점수는 `개미 심리 지수`, 내부 후보 필드는 `reactionDirection`입니다.
- `추천`, `사라`, `팔아라`, `수익 보장`, `진입`, `시그널 확정`처럼 투자 행동을 지시하는 표현은 서비스 판단, CTA, 제목, 요약 문구에 쓰지 않습니다.
- CAPTCHA 우회, 로그인 세션 크롤링, 프록시 회전, fingerprint 위장은 하지 않습니다. 공개 HTTP 수집을 우선하고 Playwright는 렌더링 fallback으로만 씁니다.
- 저장 원문은 제목, 본문 일부, URL, 작성자 해시, 작성 시각, 원문 해시처럼 필요한 범위로 제한합니다. 출처가 있는 관찰 데이터 라벨은 쓸 수 있지만 서비스 결론처럼 보이게 만들지 않습니다.
- 시세/수급/차트는 provider, `asOf`, `stale`, 지연 여부를 분리해서 다룹니다. 확인되지 않은 데이터를 실시간처럼 말하지 않습니다.
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
