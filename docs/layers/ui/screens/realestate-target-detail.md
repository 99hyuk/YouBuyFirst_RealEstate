# 지역/단지 상세

## Route

- Parent: `realestate-dashboard`
- Route 후보: `/realestate/targets/:targetId`
- Child screens: evidence log drawer, source link drawer, similar history panel

## 화면 목적

사용자가 특정 지역/단지에 대해 사람들이 무엇을 기대하고 걱정하는지, 어떤 시장 사실이 함께 관찰되는지, 비슷한 과거 상황과 이후 흐름이 어땠는지 확인합니다.

## 현재 섹션

- target header: 지역/단지명, type, alias, 데이터 상태
- evaluation summary: 에이전트 평가, 근거 chip, caveat
- reaction snapshot: 기대/우려/중립, mention count, confidence
- issue mix: 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책
- market fact timeline: 실거래, 전세, 매물, 정책, 공급, 뉴스
- source evidence: 제한 snippet, 제목, 링크, 작성 시각, source
- similar history: 유사 과거 반응과 이후 시장 흐름
- data quality: provider/asOf/stale, source skew, 표본 부족

## 상태와 빈 화면

- loading: header와 snapshot skeleton 분리
- empty: target은 있으나 mention 또는 market fact 없음
- error: source/evidence/timeline 영역별 실패 표시
- stale/mock: provider와 `asOf`를 항상 같이 표시

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `target` | realestate | region/complex 기본 정보 |
| `aliases[]` | realestate | 별칭과 review state |
| `reactionSnapshot` | indicator | target/window 반응 지표 |
| `issueMix[]` | indicator | 쟁점 라벨, share, direction, confidence |
| `timeline[]` | realestate/community | market fact, 뉴스/컬럼, 커뮤니티 이벤트 |
| `evidenceLogs[]` | agent | 평가와 근거 로그 |
| `similarWindows[]` | indicator/agent | 유사 과거 상황 후보 |

## 기획자 확인 필요

- 지역과 단지를 같은 상세 화면에서 처리할지, type별 섹션을 다르게 둘지
- 유사 과거 상황을 기본 노출할지 하위 panel로 둘지
- 평가 문구의 톤을 neutral/dry/watch/sharp 중 어디까지 허용할지

## 변경 로그

- 2026-06-01: 지역/단지 상세 Screen Brief 생성
