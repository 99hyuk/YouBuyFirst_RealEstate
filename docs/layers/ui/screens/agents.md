# 근거 로그 화면

## Route

- Parent: root
- Route 정보: `/agents`
- 현재 동작: `/realestate/reactions?view=agents`로 redirect

## 화면 목적

AI 에이전트가 지역 반응을 어떻게 판단했는지 추적하는 근거 로그 관점입니다. 독립 화면으로 분리하기 전까지는 지역 반응 화면의 agent view로 연결합니다.

## 현재 섹션 후보

- 판단 로그: 시간, 지역/단지, 에이전트, 상태, 입력값, 판단 key
- 근거 묶음: 공공데이터, 뉴스/리포트, 커뮤니티 원문, alias match
- 신뢰도: 출처 수, 중복 제거 상태, 최근성, 데이터 stale 여부
- 변경 감지: 언급량 급증, 우려 증가, 지표 변화, 정책/교통 이벤트
- 상세 연결: 지역/단지 상세, 지도 리포트, 원문 링크

## 상태와 빈 화면

- loading: 로그 table skeleton을 보여줍니다.
- empty: 아직 판단 로그가 없으면 수집 pipeline과 관찰 대상 설정을 안내합니다.
- error: 에이전트 실행 실패, source 수집 실패, alias match 실패를 분리합니다.
- stale/mock: mock 판단과 실제 수집 기반 판단을 명확히 분리합니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `agentRuns` | agent/backend | 실행 시각, 상태, 대상, 판단 key |
| `evidenceBundles` | agent/community | 판단에 사용된 원문과 지표 묶음 |
| `sourceQuality` | backend/community | 출처별 신뢰도와 stale 상태 |
| `aliasMatches` | community/backend | 지역/단지 별칭 매칭 결과 |
| `decisionSummary` | agent/indicator | 에이전트가 남긴 관찰 요약 |

## 기획 확인 필요

- 에이전트 판단을 별도 화면으로 분리할지, 반응 지표 화면의 탭으로 유지할지.
- 판단 요약에서 매수·매도처럼 보이는 표현을 어떻게 금지할지.
- 근거 원문을 사용자에게 어느 수준까지 노출할지.

## 변경 로그

- 2026-06-01: 기존 전략 로그가 아니라 부동산 반응 판단 근거 로그로 재정의.
- 2026-06-01: `/agents` redirect 대상을 `/realestate/reactions?view=agents`로 변경.
