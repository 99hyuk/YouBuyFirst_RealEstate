<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import {
  fetchRealEstateReactionRanking,
  type RealEstateReactionIssue,
  type RealEstateReactionRankingItem
} from '../lib/realestate-reactions';

type WatchTone = 'up' | 'down' | 'flat';
type WatchState = '알림 후보' | '관찰' | '확인 필요' | '수집 지연';

type WatchSummaryItem = {
  label: string;
  value: string;
  meta: string;
  tone: WatchTone;
};

type WatchRegionRow = {
  targetId: string;
  name: string;
  scope: string;
  index: string;
  status: string;
  issue: string;
  reaction: string;
  next: string;
  tone: WatchTone;
};

type WatchAction = {
  time: string;
  target: string;
  state: WatchState;
  amount: string;
  reason: string;
};

const rankingItems = ref<RealEstateReactionRankingItem[]>([]);
const loadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');

const refreshWatchCandidates = async () => {
  loadState.value = 'loading';
  rankingItems.value = [];
  try {
    const ranking = await fetchRealEstateReactionRanking({ type: 'region', windowMinutes: 1440, limit: 10 });
    rankingItems.value = ranking.items;
    loadState.value = ranking.items.length ? 'live' : 'empty';
  } catch {
    rankingItems.value = [];
    loadState.value = 'error';
  }
};

onMounted(() => {
  void refreshWatchCandidates();
});

const loadStateLabel = computed(() => {
  if (loadState.value === 'live') return 'reaction API 반영';
  if (loadState.value === 'loading') return 'reaction API 확인 중';
  if (loadState.value === 'empty') return '수집 전/insufficient';
  return 'reaction API 오류';
});

const emptyText = computed(() => {
  if (loadState.value === 'loading') return '관심 후보를 불러오는 중입니다.';
  if (loadState.value === 'error') return '지역 반응 API를 불러오지 못했습니다. 크롤링/스냅샷 배치 상태 확인이 필요합니다.';
  return '저장된 관심 지역 또는 관심 후보가 아직 없습니다. 수집 전/insufficient 상태입니다.';
});

const summary = computed<WatchSummaryItem[]>(() => {
  const rows = rankingItems.value;
  const concernCount = rows.filter((item) => item.reactionDirectionRatio.concern >= item.reactionDirectionRatio.expectation).length;
  const staleCount = rows.filter((item) => item.stale).length;
  const sourceCount = rows.reduce((sum, item) => sum + item.sourceCount, 0);
  const issueCount = new Set(rows.flatMap((item) => item.issueMix.map((issue) => issue.issueKey))).size;

  return [
    { label: '관심 후보', value: `${rows.length}곳`, meta: '최근 24시간 TOP10', tone: rows.length ? 'up' : 'flat' },
    { label: '급증 신호', value: `${rows.filter((item) => item.mentionDeltaPct > 0).length}건`, meta: '언급 증가', tone: 'up' },
    { label: '우려 우세', value: `${concernCount}곳`, meta: '기대보다 우려 높음', tone: concernCount ? 'down' : 'flat' },
    { label: '수집 지연', value: `${staleCount}건`, meta: 'stale 표시', tone: staleCount ? 'down' : 'flat' },
    { label: '출처 합계', value: `${sourceCount}곳`, meta: 'source coverage', tone: sourceCount ? 'flat' : 'down' },
    { label: '쟁점 종류', value: `${issueCount}개`, meta: '교통·전세·정책 등', tone: issueCount ? 'flat' : 'down' }
  ];
});

const watchRegions = computed<WatchRegionRow[]>(() =>
  rankingItems.value.map((item) => {
    const expectation = ratioPct(item.reactionDirectionRatio.expectation);
    const concern = ratioPct(item.reactionDirectionRatio.concern);
    const tone = expectation > concern ? 'up' : concern > expectation ? 'down' : 'flat';
    const issue = issueLabel(item.issueMix);

    return {
      targetId: item.targetId,
      name: item.displayName,
      scope: targetTypeLabel(item.targetType),
      index: formatPct(item.mentionDeltaPct),
      status: item.stale ? 'stale' : freshnessLabel(item.coverageStatus),
      issue,
      reaction: `기대 ${expectation} / 우려 ${concern}`,
      next: item.stale ? '수집 지연 확인' : `${issue} 근거 링크 확인`,
      tone
    };
  })
);

const allocation = computed(() => {
  const weights = new Map<string, { value: number; tone: WatchTone }>();
  for (const item of rankingItems.value) {
    for (const issue of item.issueMix) {
      const current = weights.get(issue.label) ?? { value: 0, tone: issueTone(issue.direction) };
      current.value += issue.share * Math.max(item.mentionCount, 1);
      weights.set(issue.label, current);
    }
  }

  const total = [...weights.values()].reduce((sum, item) => sum + item.value, 0);
  if (!total) return [];

  return [...weights.entries()]
    .sort((left, right) => right[1].value - left[1].value)
    .slice(0, 5)
    .map(([label, item]) => ({
      label,
      value: `${Math.max(6, Math.round((item.value / total) * 100))}%`,
      tone: item.tone
    }));
});

const actions = computed<WatchAction[]>(() =>
  rankingItems.value.slice(0, 5).map((item) => {
    const issue = item.issueMix[0];
    const state: WatchState = item.stale
      ? '수집 지연'
      : item.reactionDirectionRatio.concern >= 0.4
        ? '확인 필요'
        : item.mentionDeltaPct > 0
          ? '알림 후보'
          : '관찰';

    return {
      time: '최근 24시간',
      target: item.displayName,
      state,
      amount: issue?.label ?? '쟁점 확인',
      reason: `${formatPct(item.mentionDeltaPct)} 언급 변화와 ${targetTypeLabel(item.targetType)} 반응을 함께 관찰`
    };
  })
);

const ledger = computed(() =>
  rankingItems.value.slice(0, 5).map((item) => ({
    type: item.stale ? '수집 지연' : '반응 갱신',
    detail: `${item.displayName} · ${item.mentionCount.toLocaleString('ko-KR')}건`,
    value: freshnessLabel(item.coverageStatus)
  }))
);

const importPreview = computed(() =>
  rankingItems.value.slice(0, 5).map((item) => ({
    source: 'reaction snapshot',
    target: item.displayName,
    qty: `${item.mentionCount.toLocaleString('ko-KR')}건`,
    avg: `출처 ${item.sourceCount}곳`,
    confidence: Math.round(item.confidence * 100)
  }))
);

const reviews = computed(() => [
  {
    label: '알림 후보',
    value: `${actions.value.filter((item) => item.state === '알림 후보').length}건`,
    note: '사용자 저장 전까지 반응 급증 후보로만 표시',
    tone: 'up' as WatchTone
  },
  {
    label: '우려 점검',
    value: `${actions.value.filter((item) => item.state === '확인 필요').length}건`,
    note: '전세·공급·정책 쟁점은 원문과 시장 fact 대조 필요',
    tone: 'down' as WatchTone
  },
  {
    label: '수집 지연',
    value: `${actions.value.filter((item) => item.state === '수집 지연').length}건`,
    note: 'stale 상태는 실제 관심 지역처럼 확정하지 않음',
    tone: 'flat' as WatchTone
  },
  {
    label: '저장 기능',
    value: '준비 중',
    note: '로그인/사용자 watch API 연결 전까지 후보 목록으로 유지',
    tone: 'flat' as WatchTone
  }
]);

const ratioPct = (value: number) => Math.round(value * 100);
const formatPct = (value: number) => `${value > 0 ? '+' : ''}${value.toLocaleString('ko-KR', { maximumFractionDigits: 1 })}%`;

function issueLabel(issues: RealEstateReactionIssue[]): string {
  if (!issues.length) return '쟁점 확인 필요';
  return issues.slice(0, 3).map((issue) => issue.label).join('·');
}

function issueTone(direction: string): WatchTone {
  if (direction === 'expectation') return 'up';
  if (direction === 'concern') return 'down';
  return 'flat';
}

function targetTypeLabel(targetType: string): string {
  if (targetType === 'complex') return '단지';
  if (targetType === 'living_area') return '생활권';
  if (targetType === 'policy_area') return '정책권';
  return '지역';
}

function freshnessLabel(status: string): string {
  if (status === 'source_skewed') return '출처 편중';
  if (status === 'partial') return '부분 수집';
  if (status === 'ok') return '수집 확인';
  if (status === 'empty') return '수집 전';
  return status || '확인 필요';
}
</script>

<template>
  <section class="surface-page watchlist-page watchlist-ledger-page">
    <section class="watchlist-command-hero" aria-labelledby="watchlist-title">
      <div>
        <p class="label">watchlist candidates</p>
        <h2 id="watchlist-title">관심 지역</h2>
        <span>저장 기능 전까지 지역 반응 TOP10을 관심 후보로 보고, 실제 사용자 watchlist와 분리해 표시합니다.</span>
      </div>
      <div class="watchlist-hero-badges">
        <span class="status-pill warning">부동산 자문 아님</span>
        <span :class="['status-pill', loadState === 'live' ? '' : 'warning']">{{ loadStateLabel }}</span>
      </div>
    </section>

    <section class="watchlist-kpi-strip watchlist-target-grid" aria-label="관심 지역 요약">
      <article v-for="item in summary" :key="item.label" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <em>{{ item.meta }}</em>
      </article>
    </section>

    <section class="watchlist-workbench">
      <article class="watchlist-targets-panel">
        <div class="section-band-title">
          <div>
            <p class="label">watch candidates</p>
            <h3>관심 후보와 반응 연결</h3>
          </div>
          <RouterLink class="detail-link" :to="{ path: '/realestate/reactions', query: { view: 'agents' } }">근거 로그 보기</RouterLink>
        </div>

        <div class="watchlist-target-head">
          <span>지역/단지</span>
          <span>범위</span>
          <span>언급 변화</span>
          <span>상태</span>
          <span>쟁점</span>
          <span>반응</span>
          <span>다음 확인</span>
        </div>
        <p v-if="!watchRegions.length" class="newsroom-empty-state watchlist-empty-state">{{ emptyText }}</p>
        <article v-for="region in watchRegions" :key="region.targetId" class="watchlist-target-row">
          <strong>
            <RouterLink :to="`/realestate/targets/${region.targetId}`">{{ region.name }}</RouterLink>
          </strong>
          <span>{{ region.scope }}</span>
          <span>{{ region.index }}</span>
          <span>{{ region.status }}</span>
          <em :class="region.tone">{{ region.issue }}</em>
          <span>{{ region.reaction }}</span>
          <small>{{ region.next }}</small>
        </article>
      </article>

      <aside class="watchlist-sync-panel">
        <p class="label">source sync</p>
        <h3>커뮤니티 원문 · 별칭 DB 연결 준비</h3>
        <p>카페 글, 블로그, 공공데이터 후보는 아직 사용자 관심 목록으로 저장하지 않습니다. 공개 원문 후보는 민감정보를 제외한 뒤 근거 링크로만 연결합니다.</p>
        <button type="button" disabled>사용자 저장 기능 준비 중</button>
        <div class="watchlist-sync-rule">
          <span>민감정보 마스킹</span>
          <strong>필수</strong>
        </div>
        <div class="watchlist-sync-rule">
          <span>지역 별칭 매칭</span>
          <strong>{{ loadState === 'live' ? '반응 기준' : '대기' }}</strong>
        </div>
        <div v-if="allocation.length" class="allocation-stack" aria-label="관심 지역 분포">
          <article v-for="item in allocation" :key="item.label" :class="item.tone">
            <span>{{ item.label }}</span>
            <i><mark :style="{ width: item.value }"></mark></i>
            <strong>{{ item.value }}</strong>
          </article>
        </div>
        <p v-else class="newsroom-empty-state watchlist-empty-state">{{ emptyText }}</p>
      </aside>
    </section>

    <section class="watchlist-dense-grid">
      <article class="watchlist-import-panel">
        <div class="section-band-title compact">
          <div>
            <p class="label">source preview</p>
            <h3>원문/공공데이터 후보</h3>
          </div>
          <span>{{ loadStateLabel }}</span>
        </div>
        <p v-if="!importPreview.length" class="newsroom-empty-state watchlist-empty-state">{{ emptyText }}</p>
        <article v-for="item in importPreview" :key="`${item.source}-${item.target}`">
          <span>{{ item.source }}</span>
          <strong>{{ item.target }}</strong>
          <em>{{ item.qty }} · {{ item.avg }}</em>
          <b>{{ item.confidence }}%</b>
        </article>
      </article>

      <article class="watchlist-alerts-panel">
        <div class="section-band-title compact">
          <div>
            <p class="label">alerts</p>
            <h3>알림 판단 내역</h3>
          </div>
        </div>
        <p v-if="!actions.length" class="newsroom-empty-state watchlist-empty-state">{{ emptyText }}</p>
        <article v-for="action in actions" :key="`${action.time}-${action.target}`">
          <time>{{ action.time }}</time>
          <strong>{{ action.target }} · {{ action.amount }}</strong>
          <span>{{ action.state }}</span>
          <em>{{ action.reason }}</em>
        </article>
      </article>

      <article class="watchlist-ledger-panel">
        <div class="section-band-title compact">
          <div>
            <p class="label">ledger</p>
            <h3>관찰 로그</h3>
          </div>
        </div>
        <p v-if="!ledger.length" class="newsroom-empty-state watchlist-empty-state">{{ emptyText }}</p>
        <article v-for="entry in ledger" :key="`${entry.type}-${entry.detail}`">
          <span>{{ entry.type }}</span>
          <strong>{{ entry.detail }}</strong>
          <em>{{ entry.value }}</em>
        </article>
      </article>
    </section>

    <section class="watchlist-review-strip" aria-label="알림 후 복기">
      <div>
        <p class="label">post-alert review</p>
        <h3>알림 후 복기</h3>
      </div>
      <article v-for="review in reviews" :key="review.label" :class="review.tone">
        <span>{{ review.label }}</span>
        <strong>{{ review.value }}</strong>
        <em>{{ review.note }}</em>
      </article>
    </section>
  </section>
</template>
