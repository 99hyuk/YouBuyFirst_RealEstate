# Stitch Dashboard Prompt

이 문서는 과거에 Stitch로 대시보드 시안을 탐색하려고 만든 프롬프트입니다. 현재 디자인/구현 정본이 아니며, 기본 작업 루틴에서는 읽지 않습니다.

Stitch를 다시 쓰기로 명시 결정한 경우에만 보조 입력으로 사용합니다. 현재 UI 기준은 `docs/layers/ui/WIREFRAME_HANDOFF.md`, `docs/layers/ui/DESIGN_SYSTEM.md`, `docs/layers/ui/screens/`입니다.

## 사용 방법

1. 현재 웹화면 스크린샷을 함께 참고합니다.
   - 로컬 캡처 예: `artifacts/front-dashboard-current.png`
2. Stitch에 아래 프롬프트를 넣어 desktop dashboard 시안을 생성합니다.
3. 마음에 드는 안을 Figma로 정리하거나, screenshot/HTML export를 Codex 구현 입력으로 넘깁니다.

## Prompt

```text
Create a polished high-fidelity desktop web app dashboard for a Korean product named "너나사 YouBuyFirst".

Product context:
- YouBuyFirst is an investment reference and simulation service.
- It reads public community reactions, stock mention volume, quote status, and mock AI/agent experiments.
- It is NOT investment advice, NOT a real trading service, and must not show buy/sell recommendation CTAs.
- The current low-fidelity wireframe direction is "Briefing + Terminal".

Screen:
- Route: /dashboard
- Desktop web app, 1440px wide target.
- Use a dense but readable SaaS dashboard layout.
- This is an operational analytics product screen, not a marketing landing page.

Must keep these Korean UI texts exactly:
- App name: "너나사 YouBuyFirst"
- Main title: "오늘 커뮤니티 브리핑"
- Headline: "투자자들이 먼저 떠드는 종목을 읽습니다"
- Main board title: "반응 터미널"
- Planning section title: "기획자 확인 필요"
- Notice: "투자 자문이 아니라 커뮤니티 반응을 관찰하는 참고 화면입니다."

Required navigation:
- 대시보드
- 종목 상세
- 커뮤니티
- 에이전트
- 포트폴리오 준비 중

Required layout:
1. Top app header with app name, short service subtitle, and the navigation above.
2. Compact briefing area for "오늘 커뮤니티 브리핑".
   - It should explain that the screen scans community reaction using mock data before real API contracts are finalized.
   - Keep the hero product-like and compact, not oversized.
3. Top reaction summary card:
   - Stock: 삼성전자
   - Symbol: 005930
   - Market: KRX
   - Heat score: 82
   - Keywords: 실적 / 반도체 / 외국인
4. Main "반응 터미널" board with two rows:
   - 삼성전자, 005930, KRX, mock, heat score 82, mentions 128, bullish 52%, bearish 31%, keywords 실적 / 반도체 / 외국인, price status mock quote.
   - Tesla, TSLA, NASDAQ, mock, heat score 68, mentions 74, bullish 41%, bearish 43%, keywords 실적 / 가격 / 변동성, price status stale quote.
5. Feature rail cards:
   - 종목 상세: 특정 종목의 반응과 가격 상태 확인
   - 커뮤니티 비교: 소스별 반응과 성과 후보 비교
   - 에이전트 실험: 모의 페르소나의 관찰 결과 비교
   - 포트폴리오 준비 중: trade 트랙 연동 후 활성화
6. Market placeholder panel:
   - 삼성전자 78,200원, mock quote
   - Tesla 183원, stale quote
7. Planning boundary panel with bullets:
   - 열기 지수 용어 확정
   - 기본 시간창 1h, 24h, 30m 중 선택
   - AI 3줄 요약 placeholder 문구 확정

Visual direction:
- Quiet, serious, product-like Korean fintech/analytics SaaS.
- Dense but organized information for repeated scanning.
- Prefer white/light panels, dark readable text, restrained green for positive reaction, restrained red or amber for warning/stale quote, neutral gray dividers.
- Use a balanced palette. Avoid one-note purple/blue, beige/brown, or decorative gradient blobs.
- Cards should use 8px radius or less.
- Use clear status chips for mock data and stale quote.
- Avoid stock-photo imagery, cartoon illustration, oversized marketing hero, trading buy/sell buttons, hype language, or anything that looks like personalized investment advice.

Output:
- Generate one high-fidelity desktop dashboard screen.
- Make the design suitable for later implementation in Vue 3 + Vite + TypeScript.
- Keep sections component-friendly: app header, briefing hero, top reaction summary, reaction terminal, feature rail, market placeholder, planning boundary.
```

## Variant Prompts

Use these after the first result if more options are needed.

```text
Create 3 visual variants of the same dashboard while preserving all Korean copy, data, and section structure. Variant A should be compact institutional SaaS, Variant B should be more editorial but still dashboard-first, Variant C should be darker terminal-inspired but not full dark mode.
```

```text
Refine this screen to feel less like a generated template and more like a real Korean fintech analytics product. Increase information density, align numeric values, reduce decorative styling, and make mock/stale statuses more obvious.
```
