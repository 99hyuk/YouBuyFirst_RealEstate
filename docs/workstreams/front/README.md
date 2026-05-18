# front

## 역할

사용자가 실제로 보는 너나사 (YouBuyFirst)의 화면 경험을 담당합니다. 이 트랙은 대시보드, mock data, 차트, 사용자 흐름, API 연동, 로딩/오류/빈 상태를 소유합니다.

프론트는 모든 백엔드가 끝난 뒤 마지막에 몰아서 하지 않습니다. 먼저 fixture/mock 기반으로 투자 참고 사이트의 골격을 만들고, 각 기능 트랙의 API 계약이 생길 때마다 작은 PR로 연결합니다.

## 현재 프론트 전략

새 front 세션에서 현재 dashboard 작업을 이어갈 때는 이 README보다 먼저 `docs/workstreams/front/WIREFRAME_HANDOFF.md`를 확인합니다. 해당 파일은 현재 기준만 짧게 담습니다. 과거 디자인 조정 로그는 `docs/workstreams/front/archive/`에서 필요한 키워드로만 검색합니다.

초기 프론트는 최종 디자인이 아니라 `저충실도 와이어프레임`으로 시작합니다. 목표는 예쁜 화면을 먼저 만드는 것이 아니라, 사용자가 실제로 볼 정보 구조와 라우팅, mock data, API 계약 후보, 빠진 기획 질문을 드러내는 것입니다.

기획 정리 구간의 기본 운영은 `front-first discovery`입니다. backend/API 구현을 기다리지 않고 관심종목 브리핑, 종목 이벤트 타임라인, 신호 신뢰도 배지 같은 핵심 사용자 흐름을 mock으로 먼저 세우고, 필요한 API 계약을 역으로 도출합니다.

- 기술 선택은 `Vue 3 + Vite + TypeScript` SPA를 기본으로 둡니다.
- 라우팅은 `Vue Router`를 기준으로 설계합니다.
- 서버 데이터 연동 방식은 실제 API 계약이 생긴 뒤 별도 PR에서 확정합니다.
- 디자인과 프론트 구현은 기본적으로 Codex가 `front/` 코드에서 함께 진행합니다.
- Figma AI, Stitch 같은 외부 디자인 도구는 기본 흐름이 아니며, 사용자가 명시적으로 요청할 때만 참고 시안 탐색용으로 씁니다.
- 디자인 시스템, 브랜드 컬러, 일러스트, 고충실도 UI도 최종 산출물은 외부 툴 파일이 아니라 작은 front PR로 반영된 코드입니다.
- 차트 라이브러리는 대시보드 정보 구조와 데이터 형태를 먼저 본 뒤 확정합니다.

프론트 에이전트는 화면을 만들면서 기획을 임의로 확정하지 않습니다. 애매한 지표, 화면 문구, API 응답, 사용자 행동은 `기획자 확인 필요` 항목으로 남기고, mock 화면은 그 경계를 명시한 상태로 진행합니다.

현재 `front/`에는 Vue 3 + Vite + TypeScript 기반 mock 와이어프레임 shell이 있습니다. 실제 backend API 연결, 차트 라이브러리 확정, 고충실도 디자인은 아직 하지 않았습니다.

현재 화면과 Codex 디자인/구현 기준은 `docs/workstreams/front/WIREFRAME_HANDOFF.md`를 먼저 봅니다. 오래된 세부 로그는 archive 기록이므로 현재 `main` 코드와 브랜치 상태를 확인한 뒤 참고합니다.

## 현재 디자인 우선순위

다음 front 작업에서 디자인 판단이 필요하면 이 순서를 우선합니다. 과거 `Balanced Dark Toss` 같은 별도 다크 테마 제안은 현재 정본이 아니며, 다크/라이트 테마 구현은 후속 작업으로 둡니다.

1. 가독성: Pretendard 기준으로 숫자, 제목, 보조 설명, 태그의 크기와 위계를 분명히 둡니다. 큰 글씨와 큰 박스로만 강조하지 않습니다.
2. 정보 밀도: 한 화면에서 커뮤니티 비교, 종목 반응, 지표, 뉴스/리포트가 함께 읽혀야 합니다. 한 종목이나 한 카드가 과하게 넓은 영역을 차지하지 않게 합니다.
3. 전문적인 금융 차트 느낌: 커뮤니티 지표 비교와 주요 지표 그래프는 축, 라벨, 범례, 선 두께, 색을 정돈해 PPT식 단순 그래프처럼 보이지 않게 합니다.
4. 토스증권과 야선식 직관성: 긴 설명보다 숫자, 순위, 상태, 링크, 작은 태그로 바로 이해되게 합니다. 검색, 오른쪽 탭, 지표, 뉴스/리포트 목록은 실제 기능처럼 보여야 합니다.
5. AI스러운 네모 박스 반복 줄이기: 카드 남발 대신 간격, 선, 헤더, 배경 톤, 정보 밀도 차이로 영역을 구분합니다.
6. 커뮤니티 반응 서비스의 차별점: 단순 주식 대시보드가 아니라 기사, 공시, 커뮤니티 키워드, 가격 변동이 왜 반응을 움직였는지 짧게 연결합니다.
7. 투자 자문처럼 보이지 않기: 서비스의 판단, CTA, 제목, 요약 문구에서 `추천`, `매수`, `매도`, `수익 보장`, `진입`, `시그널 확정`처럼 투자 행동을 지시하는 표현을 쓰지 않습니다. 커뮤니티 원문이나 외부 링크 제목에 이런 단어가 포함될 때도 출처가 있는 반응 데이터로만 다루고 서비스의 결론처럼 보이게 만들지 않습니다.
8. 변경 기록 유지: 디자인 변경은 PR preview와 visual history로 비교 가능하게 남깁니다. 운영 주소는 Netlify main 배포본, 작업 중 확인은 로컬 서버 또는 PR preview를 사용합니다.

## 프론트 에이전트 시작 지시

사용자가 새 채팅에서 `front 작업`, `프론트 맡아줘`, `화면 와이어프레임 해줘`처럼 짧게 말하면 아래 지시를 사용자가 다시 붙여 넣지 않아도 프론트 에이전트가 스스로 적용합니다.

```text
너는 너나사 (YouBuyFirst)의 front 담당 에이전트다.
AGENTS.md, docs/CURRENT_HANDOFF.md, docs/DOCUMENTATION_GUIDE.md,
docs/workstreams/README.md, docs/workstreams/front/README.md는 필요한 섹션만 확인한다.
이미 대화에 주입된 긴 문서는 다시 전문 출력하지 않는다.
docs/superpowers/specs, docs/superpowers/plans, docs/workstreams/front/archive는 과거 archive이므로 현재 handoff가 부족할 때만 파일 1개와 키워드 1개로 좁혀 본다.
Browser/gstack 검증은 구현 후 화면 확인 가치가 있을 때 한 번에 모아 실행하고, 스킬 문서/콘솔/DOM 전문은 출력하지 않는다.

이번 front 작업의 기본값은 Vue 3 + Vite + TypeScript 기반 저충실도 와이어프레임이다.
목표는 화면 구조, 라우팅, mock data, API 계약 후보, 기획자 확인 필요 항목을 드러내는 것이다.
브랜드 디자인, 고충실도 UI, 최종 컬러, 일러스트는 Codex가 화면 코드 안에서 점진적으로 다듬는다.
디자인 판단은 README의 "현재 디자인 우선순위"를 따른다.
Figma AI, Stitch 같은 외부 디자인 도구 산출물을 정본처럼 고정하지 않는다.

작업 중 기획이 불명확한 부분은 임의로 확정하지 말고 "기획자 확인 필요"로 문서와 PR에 남긴다.
작업 하나는 브랜치 하나와 PR 하나로 만들고, PR 설명과 작업 기록은 한국어로 작성한다.
```

## 담당 범위

- 사용자용 대시보드 shell
- 관심종목 브리핑 화면
- 종목별 기사/공시/커뮤니티/가격 이벤트 타임라인
- 종목/커뮤니티 반응 랭킹 화면
- 열기 지수, 반응 방향 비율, 대표 키워드 표시
- 신호 신뢰도/주의 배지
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
6. 관심종목 브리핑 와이어프레임 추가
7. 종목 상세의 기사/공시/커뮤니티/가격 이벤트 타임라인 보강
8. 신호 신뢰도/주의 배지 표현 정리
9. 시세/모의투자/AI 에이전트 화면 초안
10. analysis ranking/indicator API 계약 연결
11. quote snapshot API 계약 연결
12. 커뮤니티별 수익률 비교 화면 연결
13. 모의투자/AI 에이전트 화면 연결

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
- Figma AI/Stitch 산출물을 정본처럼 고정
- 외부 디자인 도구 결과를 검토 없이 그대로 구현
