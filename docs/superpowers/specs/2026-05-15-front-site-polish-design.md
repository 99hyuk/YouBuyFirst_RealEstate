# front 사이트형 와이어프레임 개선 설계

작성일: 2026-05-15
트랙: `front`
작업 타입: `feat`
브랜치: `codex/front-site-polish`

## 목적

현재 Vue shell은 route와 mock data 위치를 확인하기에는 충분하지만, 사용자가 처음 들어왔을 때는 내부 관리 화면처럼 보인다. 이번 작업의 목적은 최종 디자인을 확정하는 것이 아니라, 메인 대시보드가 서비스 웹사이트처럼 읽히도록 정보 구조와 화면 리듬을 개선하는 것이다.

사용자 피드백은 `B나 C가 좋다`였고, 이후 `B의 브리핑 진입부 + C의 고밀도 투자 터미널 영역` 방향을 승인했다. 따라서 이번 PR은 매거진형 설명성과 터미널형 데이터 밀도를 섞은 저충실도 와이어프레임 개선으로 진행한다.

## 디자인 방향

선택한 방향은 `Briefing + Terminal`이다.

- 상단은 B안처럼 “오늘 투자자들이 왜 이 종목을 말하는지”가 바로 읽히는 브리핑 영역으로 둔다.
- 본문 핵심은 C안처럼 종목별 언급량, 열기 후보, 반응 방향, 가격 상태를 고밀도 테이블/랭킹으로 보여준다.
- 시각 톤은 최종 브랜드 디자인이 아니라 제품 성격을 설명하는 수준의 와이어프레임으로 유지한다.
- 투자 자문처럼 보이지 않도록 `관찰`, `mock`, `후보`, `준비 중` 표현을 유지한다.

## 포함 범위

포함한다.

- `/dashboard` 첫 화면의 사이트형 구조 개선
- 브리핑형 hero 영역
- 고밀도 종목 반응 보드
- 커뮤니티/에이전트/포트폴리오로 이어지는 짧은 feature rail
- `기획자 확인 필요` 항목을 화면 하단에 유지
- 모바일에서 navigation, hero, 랭킹 rows가 단어 중간 줄바꿈이나 겹침 없이 보이도록 CSS 보정
- 기존 shell 테스트가 깨지지 않도록 navigation과 route contract 유지

제외한다.

- 실제 backend API 연동
- 차트 라이브러리 확정
- 최종 브랜드 컬러, 일러스트, 고충실도 시각 시스템
- `/communities`, `/agents`, `/portfolio`, `/stocks/:symbol`의 대대적인 재설계
- market/trade/agent/crawl/data 로직 변경

## 화면 구조

### 1. Site header

현재 상단 navigation은 유지하되, 제품 설명을 조금 더 사용자용 문장으로 바꾼다.

- 제품명: `너나사 YouBuyFirst`
- 보조 문장: `커뮤니티 반응으로 시장의 먼저 흔들리는 지점을 관찰합니다.`
- navigation: 대시보드, 종목 상세, 커뮤니티, 에이전트, 포트폴리오 준비 중

### 2. Briefing hero

대시보드 최상단은 “오늘의 커뮤니티 브리핑”으로 시작한다.

표시 후보:

- `오늘 커뮤니티 브리핑`
- `투자자들이 먼저 떠드는 종목을 읽습니다`
- 최근 1시간 기준, mock data, 투자 참고용 관찰 서비스 고지
- 대표 종목 1개를 hero side panel에 노출
- 핵심 키워드 3개

이 영역은 랜딩 페이지의 marketing hero처럼 과하게 꾸미지 않는다. 실제 제품 첫 화면으로서 브리핑과 데이터 진입을 동시에 제공한다.

### 3. Terminal-style reaction board

기존 `커뮤니티 반응 랭킹`은 더 고밀도로 재배치한다.

각 종목 row는 아래 정보를 포함한다.

- 종목명, symbol, market
- 열기 후보 점수
- 언급 수
- 낙관/비관/중립 비율
- 대표 키워드
- quote 상태 badge

차트 라이브러리는 쓰지 않고 CSS bar와 텍스트만으로 반응 비율을 표현한다. 실제 산식과 endpoint는 후속 data/market 계약 전까지 mock으로 둔다.

### 4. Feature rail

대시보드 아래쪽에는 후속 화면으로 이어지는 짧은 feature rail을 둔다.

- 종목 상세: 특정 종목의 커뮤니티 반응과 가격 상태를 함께 확인
- 커뮤니티 비교: 소스별 반응과 성과 후보 비교
- 에이전트 실험: 모의 페르소나 성과 비교
- 포트폴리오: trade 트랙 연동 전 준비 중

이 rail은 사용자를 route로 유도하는 구조 설명이며, 아직 실제 기능 완성을 암시하지 않는다.

### 5. Planning boundary

`기획자 확인 필요` 섹션은 유지한다. 이번 작업은 디자인 확정이 아니므로 애매한 지표와 용어를 화면에서 숨기지 않는다.

유지할 항목:

- `열기 지수` 용어 확정
- 기본 시간창 `1h`, `24h`, `30m` 중 선택
- AI 3줄 요약 placeholder 문구 확정

## 데이터와 fixture

기존 fixture를 최대한 재사용한다.

- `dashboard-summary.json`: title, description, confirmationNeeded 문구를 브리핑형으로 보정
- `reaction-ranking.json`: 기존 ranking items를 유지하되 quote 상태나 direction ratio 표시를 화면에서 더 적극적으로 사용
- `quote-snapshots.json`: dashboard board의 quote badge에 연결

새 fixture가 꼭 필요하면 작은 필드 추가로 제한한다. API 계약처럼 보일 정도로 필드명을 과하게 확정하지 않는다.

## 테스트 전략

기존 `shell.spec.ts`가 보장하는 route/navigation contract는 그대로 유지한다.

추가 검증:

- dashboard가 브리핑 제목을 렌더링한다.
- ranking board가 종목명과 navigation을 계속 렌더링한다.
- `기획자 확인 필요` 문구가 남아 있다.

브라우저 확인:

- `/`가 `/dashboard`로 redirect된다.
- desktop viewport에서 hero와 board가 화면 첫 구간에 같이 보인다.
- mobile 390px에서 navigation과 ranking row가 겹치지 않는다.
- console error가 없다.

## 위험과 대응

| 위험 | 대응 |
| --- | --- |
| 최종 디자인 확정처럼 보일 수 있음 | PR 본문과 화면 문구에 `mock`, `후보`, `기획자 확인 필요`를 유지한다. |
| 투자 자문처럼 읽힐 수 있음 | “추천”, “매수”, “수익 보장” 표현을 쓰지 않고 관찰/참고 표현으로 제한한다. |
| 정보 밀도가 높아져 모바일에서 깨질 수 있음 | row를 모바일에서 세로 stack으로 전환하고 한글 단어 중간 줄바꿈을 피한다. |
| PR 범위가 커질 수 있음 | 이번 PR은 dashboard page, CSS, fixture/test 보정 위주로 제한한다. |

## 승인된 결정

- 작업 성격은 최종 디자인이 아니라 와이어프레임이다.
- 다만 와이어프레임도 사용자-facing 웹사이트처럼 보이도록 첫 화면 구조를 개선한다.
- 방향은 B안과 C안의 혼합이다.
- A안처럼 서비스 소개 중심 랜딩으로 가지 않는다.
