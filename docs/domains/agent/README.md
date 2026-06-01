# agent

## 역할

부동산 에이전트는 지역/단지 반응 지표와 시장 사실 데이터를 읽어 사용자용 평가, 유사 과거 비교 설명, 근거 로그를 만듭니다. 행동 지시가 아니라 관찰 가능한 데이터의 요약과 caveat를 남기는 계층입니다.

## 담당 범위

- 지역/단지 평가 summary
- evidence log 저장 후보
- 유사 과거 상황 비교 설명
- 데이터 품질 caveat
- evaluation key와 중복 실행 방지
- 사용자용 짧은 근거 문구

## 평가 입력 후보

- `RealEstateReactionSnapshot`
- `issueMix`
- `RealEstateMarketFact`
- 정책/개발/교통 event timeline
- 뉴스/컬럼 metadata
- source coverage와 stale 상태
- 유사 과거 window 후보

## EvidenceLog 후보

| 필드 | 의미 |
| --- | --- |
| `targetType` | `REGION` 또는 `COMPLEX` |
| `targetId` | 지역/단지 식별자 |
| `evaluatedAt` | 평가 시각 |
| `evaluationVersion` | 평가 규칙 버전 |
| `summary` | 사용자용 짧은 평가 |
| `evidenceJson` | 근거 데이터 묶음 |
| `caveatsJson` | 표본 부족, source skew, stale 등 주의점 |
| `skipReason` | 평가를 만들지 않은 이유 |

## 현재 우선순위

1. evidence log contract 설계
2. 지역/단지 평가 입력 field 정의
3. 유사 과거 상황 설명 방식 정리
4. 행동 지시처럼 보이는 문구 금지 기준 정리
5. evaluationVersion과 skipReason 관리 기준 정리

## 문구 기준

써도 되는 표현:

- 관찰
- 분석
- 반응 지표
- 관심 급등
- 우려 증가
- 쟁점 비율
- 표본 신뢰도
- 유사 과거 상황
- 이후 시장 흐름
- 근거 로그
- 확인 필요
- 데이터 지연
- 출처 기준

피해야 하는 표현:

- 추천
- 사라
- 팔아라
- 매수 기회
- 매도 신호
- 수익 보장
- 진입
- 시그널 확정
- 오를 지역
- 무조건 오른다
- 청약 넣어라
- 대출 받아라
- 지금 사야 한다

## 다른 도메인과의 접점

- `realestate`: 지역/단지 target, market fact, 정책 이벤트 정본을 제공합니다.
- `community`: 제한 저장된 원문과 반응 후보를 제공합니다.
- `indicator`: reaction snapshot, issueMix, 표본 신뢰도를 제공합니다.
- `layers/ui`: 평가와 근거 로그를 화면에 보여줍니다.

## 하지 않는 일

- 실제 거래, 청약, 대출 행동 결정
- 내부 추론 전문 저장 또는 노출
- source별 성향 우열을 공개 결론으로 만들기
- 원문 전문 재게시
