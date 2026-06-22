<script setup lang="ts">
type StatusTone = 'up' | 'down' | 'flat';

type SummaryItem = {
  label: string;
  value: string;
  meta: string;
  tone: StatusTone;
};

type ChangeItem = {
  title: string;
  state: string;
  detail: string;
};

type AlertRule = {
  title: string;
  state: string;
  detail: string;
};

type MemoExample = {
  target: string;
  memo: string;
};

const summaryItems: SummaryItem[] = [
  {
    label: '저장 대상',
    value: '0곳',
    meta: '로그인 후 사용자 저장 목록 표시',
    tone: 'flat'
  },
  {
    label: '최근 변화',
    value: '확인 전',
    meta: '지난 방문 이후 변경점은 로그인 후 계산',
    tone: 'flat'
  },
  {
    label: '알림 조건',
    value: '준비 중',
    meta: '거래·전세·일정·정책 조건 관리 예정',
    tone: 'down'
  },
  {
    label: '개인 메모',
    value: '0건',
    meta: '지역별 관찰 메모는 사용자 계정 기준',
    tone: 'flat'
  }
];

const savedTags = ['실거주', '전세', '청약', '투자관찰', '교통', '재건축', '공급'];

const changeItems: ChangeItem[] = [
  {
    title: '새 실거래·전세 거래',
    state: '로그인 후 확인',
    detail: '저장한 지역이나 단지에 새 거래가 들어왔는지 비교합니다.'
  },
  {
    title: '주요 일정 도래',
    state: '데이터 확인 전',
    detail: '가격지수, 청약, 금리, 정책 발표 일정을 저장 대상 기준으로 묶습니다.'
  },
  {
    title: '정책·공급·청약 이슈',
    state: '준비 중',
    detail: '저장한 지역과 연결된 정책, 공급, 청약 변화를 표시합니다.'
  },
  {
    title: '근거 브리핑 갱신',
    state: '준비 중',
    detail: 'AI 브리핑이 생성되면 이전 방문 이후 바뀐 근거를 비교합니다.'
  },
  {
    title: '공식 데이터 없음',
    state: '데이터 확인 전',
    detail: '공식 지표가 없는 지역은 저장 목록에서도 별도 상태로 구분합니다.'
  }
];

const alertRules: AlertRule[] = [
  {
    title: '거래 변화',
    state: '알림 조건 준비 중',
    detail: '최근 실거래나 전세 거래가 들어왔을 때 확인하도록 설정합니다.'
  },
  {
    title: '전세 압력',
    state: '알림 조건 준비 중',
    detail: '전세 지표와 거래 흐름이 바뀌는 구간을 관찰합니다.'
  },
  {
    title: '주요 일정',
    state: '알림 조건 준비 중',
    detail: '공식 통계, 청약, 정책 발표 일정이 다가오면 알려줍니다.'
  },
  {
    title: '정책·공급 이벤트',
    state: '알림 조건 준비 중',
    detail: '저장 대상과 연결된 정책, 공급, 교통 이벤트를 묶어 봅니다.'
  }
];

const memoExamples: MemoExample[] = [
  {
    target: '전세 위주로 보기',
    memo: '전세가와 매매가 흐름을 따로 체크해야 하는 지역'
  },
  {
    target: '청약 일정 체크',
    memo: '공급 일정과 당첨자 발표일을 놓치지 않기 위한 메모'
  },
  {
    target: '실거주 후보',
    memo: '통근, 학군, 생활 편의성을 함께 볼 후보 지역'
  }
];

const compareColumns = ['실거래', '전세', '공급', '일정', '근거'];
</script>

<template>
  <section class="surface-page watchlist-page watchlist-ledger-page mypage-page">
    <section class="watchlist-command-hero mypage-command-hero" aria-labelledby="mypage-title">
      <div>
        <p class="label">개인 관찰 공간</p>
        <h2 id="mypage-title">내 부동산 관찰 보드</h2>
        <span>사용자가 저장한 지역을 관리하고, 지난 방문 이후 바뀐 시장 사실을 확인하는 개인화 공간입니다.</span>
      </div>
      <button type="button" disabled>로그인 연동 준비 중</button>
    </section>

    <section class="watchlist-kpi-strip watchlist-target-grid mypage-status-strip" aria-label="마이페이지 상태 요약">
      <article v-for="item in summaryItems" :key="item.label" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <em>{{ item.meta }}</em>
      </article>
    </section>

    <section class="watchlist-workbench mypage-workbench">
      <article class="watchlist-targets-panel mypage-saved-panel">
        <div class="section-band-title">
          <div>
            <p class="label">저장 목록</p>
            <h3>내 저장 지역·단지</h3>
          </div>
          <RouterLink class="detail-link" to="/realestate/map">지역 분석에서 찾기</RouterLink>
        </div>

        <div class="mypage-empty-card">
          <strong>저장된 지역이나 단지가 아직 없습니다</strong>
          <p>
            로그인 기능이 연결되면 사용자가 직접 저장한 대상만 이곳에 표시합니다.
            실제 저장 목록처럼 보이는 임시 데이터는 넣지 않습니다.
          </p>
          <div class="mypage-tag-row" aria-label="저장 태그 예시">
            <span v-for="tag in savedTags" :key="tag">{{ tag }}</span>
          </div>
        </div>
      </article>

      <aside class="watchlist-sync-panel mypage-change-panel">
        <p class="label">방문 이후 변화</p>
        <h3>지난 방문 이후 바뀐 것</h3>
        <p>저장 대상이 생기면 새 거래, 전세 흐름, 주요 일정, 정책·공급 이슈를 방문 시점 기준으로 비교합니다.</p>
        <div class="mypage-change-list">
          <article v-for="item in changeItems" :key="item.title">
            <strong>{{ item.title }}</strong>
            <span>{{ item.state }}</span>
            <p>{{ item.detail }}</p>
          </article>
        </div>
      </aside>
    </section>

    <section class="watchlist-dense-grid mypage-dense-grid">
      <article class="watchlist-alerts-panel mypage-alert-panel">
        <div class="section-band-title compact">
          <div>
            <p class="label">조건 관리</p>
            <h3>내 알림 조건</h3>
          </div>
        </div>
        <article v-for="rule in alertRules" :key="rule.title">
          <strong>{{ rule.title }}</strong>
          <span>{{ rule.state }}</span>
          <em>{{ rule.detail }}</em>
        </article>
      </article>

      <article class="watchlist-ledger-panel mypage-memo-panel">
        <div class="section-band-title compact">
          <div>
            <p class="label">개인 메모</p>
            <h3>지역별 관찰 메모</h3>
          </div>
        </div>
        <article v-for="memo in memoExamples" :key="memo.target">
          <span>{{ memo.target }}</span>
          <strong>{{ memo.memo }}</strong>
          <em>로그인 후 직접 작성</em>
        </article>
      </article>
    </section>

    <section class="watchlist-review-strip mypage-compare-panel" aria-label="저장 지역 비교">
      <div>
        <p class="label">비교 보기</p>
        <h3>저장 지역 비교</h3>
      </div>
      <article v-for="column in compareColumns" :key="column">
        <span>{{ column }}</span>
        <strong>확인 전</strong>
        <em>저장 지역을 선택하면 비교가 시작됩니다</em>
      </article>
    </section>
  </section>
</template>
