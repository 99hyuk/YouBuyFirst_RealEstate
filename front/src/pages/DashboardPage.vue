<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import {
  buildNewsroomFeedItems,
  fetchRealEstateNewsroom,
  type NewsroomCategory,
  type NewsroomFeedItem
} from '../lib/realestate-content';
import {
  buildDashboardSpeculationHeat,
  buildRegionalMomentumRows,
  dashboardReturnModeLabel,
  dashboardReturnModes,
  type DashboardRegionalMomentumRow,
  type DashboardReturnMode
} from '../lib/realestate-dashboard';
import { fetchRealEstateMapLayer, type RealEstateMapLayerResponse } from '../lib/realestate-map';
import {
  fetchRealEstateReactionRanking,
  type RealEstateReactionIssue,
  type RealEstateReactionRankingItem
} from '../lib/realestate-reactions';
import {
  buildMarketFactRows,
  buildMarketSummaryIndicators,
  fetchRealEstateMarketFacts,
  fetchRealEstateMarketSummary,
  type RealEstateMarketIndicatorCard,
  type RealEstateMarketFactRow
} from '../lib/realestate-market-facts';
import { sourceIconUrl } from '../lib/source-icons';

const marketFilters = ['전체', '언급 증가', '정책 변화', '공공데이터 stale'];
const returnTimeModes = dashboardReturnModes;
const confirmationNeeded = [
  '지역별 시장 fact coverage 확대',
  '카페/커뮤니티 공개 source 수집 범위 확정',
  '전국·시도·시군구 map layer daily refresh 점검',
  'SerpApi 후보 링크와 EvidenceLog 검수 흐름 확인'
];
const drawerTabs = [
  { id: 'reaction', label: '반응' },
  { id: 'metrics', label: '지표' },
  { id: 'watch', label: '관심' }
];
const activeDrawerTab = ref('reaction');
const activeReturnMode = ref<DashboardReturnMode>('month');
const marketIndicators = ref<RealEstateMarketIndicatorCard[]>([]);
const marketFactRows = ref<RealEstateMarketFactRow[]>(buildMarketFactRows([]));
const marketIndicatorLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const marketFactLoadState = ref<'loading' | 'live' | 'fallback'>('loading');
const dashboardMapLayer = ref<RealEstateMapLayerResponse | null>(null);
const mapLayerLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const dashboardContentItems = ref<NewsroomFeedItem[]>([]);
const dashboardContentLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
type ReactionKeyword = { word: string; weight: number };
type ReactionDriver = { type: string; label: string };
type DashboardReactionItem = {
  targetId: string;
  name: string;
  market: string;
  previousMentionCount: number;
  mentionCount: number;
  mentionDeltaPct: number;
  reactionDirectionRatio: {
    bullish: number;
    bearish: number;
    neutral: number;
  };
  heatScore: number;
  topKeywords: string[];
  issueMix: RealEstateReactionIssue[];
  positiveKeywords: ReactionKeyword[];
  negativeKeywords: ReactionKeyword[];
  positiveLinks: { title: string; source: string }[];
  negativeLinks: { title: string; source: string }[];
  priceStatus: string;
  dataStatus: string;
  reactionDrivers: ReactionDriver[];
  movementReasons: string[];
};
const dashboardReactionItems = ref<DashboardReactionItem[]>([]);
const rawReactionRankingItems = ref<RealEstateReactionRankingItem[]>([]);
const reactionRankingLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
type ReactionMetric = 'bullish' | 'bearish';

const totalMentions = computed(() => dashboardReactionItems.value.reduce((sum, item) => sum + item.mentionCount, 0));
const topRiser = computed(() => dashboardReactionItems.value[0] ?? null);
const risingStars = computed(() => dashboardReactionItems.value.slice(0, 4));
const speculationHeatIndex = computed(() => buildDashboardSpeculationHeat(rawReactionRankingItems.value));
const regionalMomentumRows = computed(() =>
  buildRegionalMomentumRows(dashboardMapLayer.value, activeReturnMode.value, 6)
);
const activeReturnModeLabel = computed(() => dashboardReturnModeLabel(activeReturnMode.value));
const reactionSignalScore = (item: DashboardReactionItem, metric: ReactionMetric) =>
  Math.round(item.mentionCount * item.reactionDirectionRatio[metric]);
const buildReactionGroup = (id: 'positive' | 'negative', label: string, caption: string, metric: ReactionMetric) => ({
  id,
  label,
  caption,
  metric,
  ratioLabel: metric === 'bullish' ? '기대' : '우려',
  items: [...dashboardReactionItems.value]
    .sort((left, right) => reactionSignalScore(right, metric) - reactionSignalScore(left, metric))
    .slice(0, 3)
});
const reactionSignalGroups = computed(() => [
  buildReactionGroup('positive', '언급+기대 TOP 3', '언급량 x 기대', 'bullish'),
  buildReactionGroup('negative', '언급+우려 TOP 3', '언급량 x 우려', 'bearish')
]);

const currentSlide = ref(0);
const isPaused = ref(false);
const totalSlides = computed(() => Math.max(dashboardReactionItems.value.length, 1));
let autoSlideTimer: ReturnType<typeof setInterval> | undefined;

const startTimer = () => {
  if (autoSlideTimer) clearInterval(autoSlideTimer);
  autoSlideTimer = setInterval(() => { currentSlide.value = (currentSlide.value + 1) % totalSlides.value; }, 4500);
};
const refreshMarketFacts = async () => {
  try {
    const facts = await fetchRealEstateMarketFacts();
    marketFactRows.value = buildMarketFactRows(facts);
    marketFactLoadState.value = facts.length ? 'live' : 'fallback';
  } catch {
    marketFactRows.value = buildMarketFactRows([]);
    marketFactLoadState.value = 'fallback';
  }
};
const refreshMarketSummary = async () => {
  marketIndicatorLoadState.value = 'loading';
  try {
    const summary = await fetchRealEstateMarketSummary();
    marketIndicators.value = buildMarketSummaryIndicators(summary);
    marketIndicatorLoadState.value = summary.items.length ? 'live' : 'empty';
  } catch {
    marketIndicators.value = [];
    marketIndicatorLoadState.value = 'error';
  }
};
const reactionKeywordFromIssue = (issue: RealEstateReactionIssue, index: number): ReactionKeyword => ({
  word: issue.label,
  weight: Math.max(1, Math.min(5, Math.round(issue.share * 10) || 5 - index))
});

const previousMentionCount = (item: RealEstateReactionRankingItem) => {
  const denominator = 1 + item.mentionDeltaPct / 100;
  if (denominator <= 0) return item.mentionCount;
  return Math.max(0, Math.round(item.mentionCount / denominator));
};

const reactionDriverType = (direction: string) => {
  if (direction === 'expectation') return '기대';
  if (direction === 'concern') return '우려';
  return '쟁점';
};

const movementReasons = (item: RealEstateReactionRankingItem) => {
  const issues = item.issueMix.slice(0, 3);
  if (!issues.length) {
    return [
      '지역 언급량은 집계됐지만 쟁점 분류 표본은 아직 충분하지 않습니다.',
      '실거래·전세 흐름과 연결하려면 다음 배치의 market fact 확인이 필요합니다.'
    ];
  }

  return issues.map((issue) =>
    `${issue.label} 쟁점이 ${reactionDriverType(issue.direction)} 방향으로 묶이며 언급 변화에 기여했습니다.`
  );
};

const dashboardReactionItemFromApi = (item: RealEstateReactionRankingItem): DashboardReactionItem => {
  const expectationIssues = item.issueMix.filter((issue) => issue.direction === 'expectation');
  const concernIssues = item.issueMix.filter((issue) => issue.direction === 'concern');
  const topIssues = item.issueMix.length ? item.issueMix : [
    { issueKey: 'unknown', label: '쟁점 확인 필요', share: 0.5, direction: 'neutral', confidence: item.confidence }
  ];

  return {
    targetId: item.targetId,
    name: item.displayName,
    market: item.targetType === 'complex' ? '단지' : item.targetType === 'living_area' ? '생활권' : '지역',
    previousMentionCount: previousMentionCount(item),
    mentionCount: item.mentionCount,
    mentionDeltaPct: item.mentionDeltaPct,
    reactionDirectionRatio: {
      bullish: item.reactionDirectionRatio.expectation,
      bearish: item.reactionDirectionRatio.concern,
      neutral: item.reactionDirectionRatio.neutral
    },
    heatScore: Math.round(item.heatScore),
    issueMix: item.issueMix,
    topKeywords: topIssues.slice(0, 3).map((issue) => issue.label),
    positiveKeywords: (expectationIssues.length ? expectationIssues : topIssues)
      .slice(0, 5)
      .map(reactionKeywordFromIssue),
    negativeKeywords: (concernIssues.length ? concernIssues : topIssues)
      .slice(0, 5)
      .map(reactionKeywordFromIssue),
    positiveLinks: [
      { title: `기대 쟁점: ${(expectationIssues[0] ?? topIssues[0]).label}`, source: 'reaction snapshot' },
      { title: `표본 신뢰도 ${Math.round(item.confidence * 100)}%`, source: item.coverageStatus }
    ],
    negativeLinks: [
      { title: `우려 쟁점: ${(concernIssues[0] ?? topIssues[0]).label}`, source: 'reaction snapshot' },
      { title: item.stale ? '수집 지연 가능' : `출처 ${item.sourceCount}곳`, source: item.stale ? 'stale' : 'source coverage' }
    ],
    priceStatus: item.stale ? 'reaction snapshot stale' : 'market fact separate',
    dataStatus: item.stale ? 'stale' : item.coverageStatus,
    reactionDrivers: topIssues.slice(0, 4).map((issue) => ({
      type: reactionDriverType(issue.direction),
      label: issue.label
    })),
    movementReasons: movementReasons(item)
  };
};

const refreshDashboardReactions = async () => {
  reactionRankingLoadState.value = 'loading';
  dashboardReactionItems.value = [];
  rawReactionRankingItems.value = [];
  currentSlide.value = 0;
  try {
    const ranking = await fetchRealEstateReactionRanking({ type: 'region', windowMinutes: 1440, limit: 10 });
    rawReactionRankingItems.value = ranking.items;
    dashboardReactionItems.value = ranking.items.map(dashboardReactionItemFromApi);
    reactionRankingLoadState.value = dashboardReactionItems.value.length ? 'live' : 'empty';
  } catch {
    rawReactionRankingItems.value = [];
    dashboardReactionItems.value = [];
    reactionRankingLoadState.value = 'error';
  }
};
const refreshDashboardMapLayer = async () => {
  mapLayerLoadState.value = 'loading';
  dashboardMapLayer.value = null;
  try {
    const layer = await fetchRealEstateMapLayer({ layerType: 'sido' });
    dashboardMapLayer.value = layer;
    mapLayerLoadState.value = layer.targets.length ? 'live' : 'empty';
  } catch {
    dashboardMapLayer.value = null;
    mapLayerLoadState.value = 'error';
  }
};
const refreshDashboardContent = async () => {
  dashboardContentLoadState.value = 'loading';
  dashboardContentItems.value = [];
  try {
    const contentItems = await fetchRealEstateNewsroom({ feed: 'all', page: 1, pageSize: 40 });
    const mappedItems = buildNewsroomFeedItems(contentItems);
    dashboardContentItems.value = mappedItems;
    dashboardContentLoadState.value = mappedItems.length ? 'live' : 'empty';
  } catch {
    dashboardContentItems.value = [];
    dashboardContentLoadState.value = 'error';
  }
};
const resetTimer = () => { if (!isPaused.value) startTimer(); };
const prevSlide = () => { currentSlide.value = (currentSlide.value - 1 + totalSlides.value) % totalSlides.value; resetTimer(); };
const nextSlide = () => { currentSlide.value = (currentSlide.value + 1) % totalSlides.value; resetTimer(); };
const goToSlide = (i: number) => { currentSlide.value = i; resetTimer(); };
const togglePause = () => {
  isPaused.value = !isPaused.value;
  if (isPaused.value) { clearInterval(autoSlideTimer); autoSlideTimer = undefined; }
  else startTimer();
};
// Word-cloud placement: grid candidates sorted center-first, then collision-test each word
const CLOUD_W = 218, CLOUD_H = 92;
const CLOUD_CANDIDATES: [number, number][] = (() => {
  const pts: [number, number][] = [];
  for (let y = 4; y <= CLOUD_H - 10; y += 11)
    for (let x = 4; x <= CLOUD_W - 8; x += 16) pts.push([x, y]);
  return pts.sort((a, b) =>
    Math.hypot(a[0] - CLOUD_W / 2, a[1] - CLOUD_H / 2) -
    Math.hypot(b[0] - CLOUD_W / 2, b[1] - CLOUD_H / 2)
  );
})();

const kwWordBox = (kw: { word: string; weight: number }) => {
  const fs = [9, 11, 14, 18, 22][Math.min(kw.weight - 1, 4)];
  return { w: kw.word.length * fs * 0.94 + 6, h: fs * 1.45, fs };
};

const placeWords = (keywords: { word: string; weight: number }[]) => {
  const GAP = 5;
  const placed: { x: number; y: number; w: number; h: number }[] = [];
  const hits = (x: number, y: number, w: number, h: number) =>
    placed.some(p => x < p.x + p.w + GAP && x + w + GAP > p.x && y < p.y + p.h + GAP && y + h + GAP > p.y);

  // heaviest word placed first so it gets the prime center spot
  const sorted = [...keywords].map((kw, i) => ({ kw, i })).sort((a, b) => b.kw.weight - a.kw.weight);
  const styles: Record<number, Record<string, string>> = {};

  sorted.forEach(({ kw, i }, rank) => {
    const { w, h, fs } = kwWordBox(kw);
    let px = 0, py = 0;
    for (const [cx, cy] of CLOUD_CANDIDATES) {
      const x = Math.max(0, Math.min(cx, CLOUD_W - w));
      const y = Math.max(0, Math.min(cy, CLOUD_H - h));
      if (!hits(x, y, w, h)) { px = x; py = y; break; }
    }
    placed.push({ x: px, y: py, w, h });
    styles[i] = {
      position: 'absolute',
      left: `${px}px`,
      top: `${py}px`,
      fontSize: `${fs}px`,
      '--kw-opacity': String(0.5 + kw.weight * 0.10),
      animationDelay: `${rank * 120}ms`,
    };
  });

  return (idx: number) => styles[idx] ?? {};
};

const kwWordStyles = computed(() => Object.fromEntries(
  dashboardReactionItems.value.map(item => [
    item.targetId,
    { pos: placeWords(item.positiveKeywords), neg: placeWords(item.negativeKeywords) },
  ])
));

onMounted(() => {
  startTimer();
  void refreshDashboardReactions();
  void refreshDashboardMapLayer();
  void refreshMarketSummary();
  void refreshMarketFacts();
  void refreshDashboardContent();
});
onUnmounted(() => clearInterval(autoSlideTimer));

const formatPct = (value: number | null) => value === null ? '최신' : `${value > 0 ? '+' : ''}${value}%`;
const ratioPct = (value: number) => `${Math.round(value * 100)}%`;
const trendClass = (trend: string) => (trend === 'down' ? 'down' : 'up');
const marketIndicatorStatusLabel = () => {
  if (marketIndicatorLoadState.value === 'live') return 'API 반영';
  if (marketIndicatorLoadState.value === 'loading') return '불러오는 중';
  if (marketIndicatorLoadState.value === 'empty') return '수집 전/insufficient';
  return 'market summary API 오류';
};
const dashboardHeadline = computed(() => {
  if (reactionRankingLoadState.value === 'loading') return '지역 반응과 시장 지표를 불러오는 중입니다';
  if (reactionRankingLoadState.value === 'error') return '지역 반응 API 확인이 필요합니다';
  if (!topRiser.value) return '수집 전 상태입니다. 지역 반응 배치가 생성되면 이곳에 최신 관심 지역이 표시됩니다';
  return `${topRiser.value.name}에 최근 24시간 반응이 가장 많이 몰렸습니다`;
});
const regionalMomentumStatusLabel = computed(() => {
  if (activeReturnMode.value === 'year') return '연간 수집 전';
  if (mapLayerLoadState.value === 'live' && regionalMomentumRows.value.length) return 'map layer API 반영';
  if (mapLayerLoadState.value === 'loading') return 'map layer 확인 중';
  if (mapLayerLoadState.value === 'error') return 'map layer API 오류';
  return '수집 전/insufficient';
});
const regionalMomentumEmptyText = computed(() => {
  if (activeReturnMode.value === 'year') return '연간 지역 상승률 snapshot은 아직 수집 전입니다.';
  if (mapLayerLoadState.value === 'loading') return '지역별 상승률 snapshot을 불러오는 중입니다.';
  if (mapLayerLoadState.value === 'error') return '지도 레이어 API를 불러오지 못했습니다. map layer refresh 상태 확인이 필요합니다.';
  return '표시할 지역별 상승률 snapshot이 아직 없습니다. 수집 전/insufficient 상태입니다.';
});
const regionalMomentumNote = computed(() => {
  if (!regionalMomentumRows.value.length) return regionalMomentumEmptyText.value;
  const staleCount = regionalMomentumRows.value.filter((row) => row.stale).length;
  const source = dashboardMapLayer.value?.sourceLabel ?? 'map_layer_snapshots';
  const asOf = dashboardMapLayer.value?.asOf ?? regionalMomentumRows.value[0]?.asOf ?? '기준 시각 확인 필요';
  return `${activeReturnModeLabel.value} · ${source} · 기준 ${asOf} · stale ${staleCount}곳 · 부동산 자문 아님`;
});
const regionalMomentumStatusClass = (row: DashboardRegionalMomentumRow) =>
  row.stale || row.dataStatus === 'mock' ? 'warning' : '';
const regionalMomentumStatusText = (row: DashboardRegionalMomentumRow) => {
  if (row.stale) return 'stale';
  if (row.dataStatus === 'ok') return '공공데이터 반영';
  if (row.dataStatus === 'mock') return 'mock';
  if (row.dataStatus === 'empty') return '수집 전';
  return row.dataStatus;
};
const dashboardContentStatusLabel = computed(() => {
  if (dashboardContentLoadState.value === 'live') return 'content API 반영';
  if (dashboardContentLoadState.value === 'loading') return 'content API 확인 중';
  if (dashboardContentLoadState.value === 'empty') return '수집 전/insufficient';
  return 'content API 오류';
});
const reactionStatusLabel = computed(() => {
  if (reactionRankingLoadState.value === 'live') return 'reaction API 반영';
  if (reactionRankingLoadState.value === 'loading') return 'reaction API 확인 중';
  if (reactionRankingLoadState.value === 'empty') return '수집 전/insufficient';
  return 'reaction API 오류';
});
const dashboardReactionEmptyText = computed(() => {
  if (reactionRankingLoadState.value === 'loading') return '지역 반응 TOP10을 불러오는 중입니다.';
  if (reactionRankingLoadState.value === 'error') return '지역 반응 API를 불러오지 못했습니다. 크롤링/스냅샷 배치 상태 확인이 필요합니다.';
  return '수집된 지역 반응 TOP10이 아직 없습니다. 수집 전/insufficient 상태입니다.';
});
const contentItemsByCategory = (category: NewsroomCategory) =>
  computed(() => dashboardContentItems.value.filter((item) => item.category === category).slice(0, 5));
const dashboardNewsItems = contentItemsByCategory('news');
const dashboardReportItems = contentItemsByCategory('reports');
const dashboardVideoItems = contentItemsByCategory('videos');
const dashboardLinkItems = contentItemsByCategory('links');
const dashboardContentEmptyText = computed(() => {
  if (dashboardContentLoadState.value === 'loading') return '콘텐츠를 불러오는 중입니다.';
  if (dashboardContentLoadState.value === 'error') return '콘텐츠 API를 불러오지 못했습니다. provider/asOf 확인이 필요합니다.';
  return '수집된 항목이 아직 없습니다. 수집 전/insufficient 상태입니다.';
});
const hideBrokenIcon = (event: Event) => {
  const image = event.target as HTMLImageElement;
  image.hidden = true;
  image.closest('.site-icon')?.classList.remove('real-icon');
};
const gaugeCenter = { x: 92, y: 92 };
const gaugeRadius = 70;
const gaugePoint = (value: number, radius = gaugeRadius) => {
  const angle = (180 - value * 1.8) * (Math.PI / 180);

  return {
    x: Math.round((gaugeCenter.x + Math.cos(angle) * radius) * 10) / 10,
    y: Math.round((gaugeCenter.y - Math.sin(angle) * radius) * 10) / 10
  };
};
const gaugeArcPath = (start: number, end: number) => {
  const startPoint = gaugePoint(start);
  const endPoint = gaugePoint(end);
  const largeArcFlag = end - start > 50 ? 1 : 0;

  return `M ${startPoint.x} ${startPoint.y} A ${gaugeRadius} ${gaugeRadius} 0 ${largeArcFlag} 1 ${endPoint.x} ${endPoint.y}`;
};
const needleEnd = computed(() => gaugePoint(speculationHeatIndex.value.value, 56));
</script>

<template>
  <section class="dashboard-page">
    <section class="standalone-search" aria-label="대시보드 검색과 필터">
      <p class="eyebrow">최근 24시간 · {{ reactionStatusLabel }}</p>
      <div class="search-line">
        <div class="search-primary-row">
          <aside class="speculation-heat-gauge-card" aria-label="부동산 투기 과열 지표">
            <div class="speculation-heat-copy">
              <span>{{ speculationHeatIndex.label }}</span>
              <strong>{{ speculationHeatIndex.value }}<small>{{ speculationHeatIndex.unit }}</small></strong>
              <em>{{ speculationHeatIndex.status }} · {{ speculationHeatIndex.changeLabel }} {{ formatPct(speculationHeatIndex.changePct) }}</em>
              <div class="speculation-heat-keywords" aria-label="대표 반응 키워드">
                <span v-for="keyword in speculationHeatIndex.keywords.slice(0, 2)" :key="keyword">{{ keyword }}</span>
              </div>
            </div>
            <div class="speculation-gauge-wrap">
              <svg class="speculation-gauge" viewBox="0 0 184 104" role="img" :aria-label="`${speculationHeatIndex.label} ${speculationHeatIndex.value}${speculationHeatIndex.unit}`">
                <path class="gauge-base" :d="gaugeArcPath(0, 100)" />
                <path
                  v-for="segment in speculationHeatIndex.segments"
                  :key="segment.label"
                  class="gauge-segment"
                  :d="gaugeArcPath(segment.start, segment.end)"
                  :stroke="segment.color"
                />
                <line class="gauge-needle" :x1="gaugeCenter.x" :y1="gaugeCenter.y" :x2="needleEnd.x" :y2="needleEnd.y" />
                <circle class="gauge-hub" :cx="gaugeCenter.x" :cy="gaugeCenter.y" r="4.6" />
              </svg>
              <div class="speculation-gauge-scale" aria-hidden="true">
                <span>냉각</span>
                <span>주의</span>
                <span>과열</span>
              </div>
            </div>
          </aside>
          <button class="dashboard-search-control" type="button" disabled>
            <span class="search-icon" aria-hidden="true"></span>
            <strong>/</strong>
            <span>지역이나 단지 검색</span>
          </button>
        </div>
        <p>{{ dashboardHeadline }}</p>
      </div>
      <div class="market-filter-row" aria-label="지금 뜨는 반응 필터">
        <span class="market-title">지금 뜨는 반응</span>
        <button
          v-for="filter in marketFilters"
          :key="filter"
          type="button"
          :class="{ active: filter === '전체' }"
        >
          {{ filter }}
        </button>
        <span class="status-pill warning">실시간 아님</span>
      </div>
      <div class="dashboard-meta-strip" aria-label="대시보드 집계 메타">
        <span>언급 합계 <strong>{{ totalMentions }}</strong></span>
        <span>지연 지표 <strong>{{ marketFactRows.filter((row) => row.stale).length }}건</strong></span>
        <span>관찰 <strong>{{ dashboardReactionItems.length }}곳</strong></span>
        <span>부동산 자문 아님</span>
      </div>
    </section>

    <section class="dashboard-main-layout">
      <div class="dashboard-content-flow">
        <section class="insight-grid">
          <article class="return-chart" aria-labelledby="return-title">
            <div class="panel-header">
              <div>
                <p class="label">regional momentum</p>
                <h3 id="return-title">핵심 지역별 상승률</h3>
              </div>
              <div class="section-actions">
                <span :class="['status-pill', mapLayerLoadState === 'live' && regionalMomentumRows.length ? '' : 'warning']">
                  {{ regionalMomentumStatusLabel }}
                </span>
                <RouterLink class="detail-link" to="/realestate/map">지도에서 보기 →</RouterLink>
              </div>
            </div>

            <div class="community-graph regional-graph" aria-label="핵심 지역별 상승률 그래프">
              <div class="community-graph-topline">
                <div class="return-range-tabs in-graph-tabs" aria-label="지역 상승률 기간">
                  <button
                    v-for="mode in returnTimeModes"
                    :key="mode.id"
                    type="button"
                    :class="{ active: mode.id === activeReturnMode }"
                    @click="activeReturnMode = mode.id"
                  >
                    {{ mode.label }}
                  </button>
                </div>
                <div class="graph-legend in-graph" aria-label="지역별 색상 범례">
                  <div class="legend-item">
                    <span class="legend-swatch return-up"></span>
                    <strong>상승</strong>
                  </div>
                  <div class="legend-item">
                    <span class="legend-swatch return-down"></span>
                    <strong>하락</strong>
                  </div>
                </div>
              </div>
              <div v-if="!regionalMomentumRows.length" class="newsroom-empty-state dashboard-chart-empty">
                {{ regionalMomentumEmptyText }}
              </div>
              <div v-else class="regional-momentum-list">
                <article
                  v-for="row in regionalMomentumRows"
                  :key="`${row.targetId}-${activeReturnMode}`"
                  :class="['regional-momentum-row', row.tone]"
                >
                  <div class="regional-momentum-copy">
                    <strong>{{ row.name }}</strong>
                    <span>{{ row.provider }} · 표본 {{ row.sampleCount.toLocaleString('ko-KR') }}건 · 신뢰 {{ Math.round(row.confidence) }}%</span>
                  </div>
                  <div class="regional-momentum-bar-track" aria-hidden="true">
                    <i :style="`--bar-pct: ${row.barPct}%`"></i>
                  </div>
                  <strong class="regional-momentum-value">{{ formatPct(row.changePct) }}</strong>
                  <span :class="['status-pill', regionalMomentumStatusClass(row)]">
                    {{ regionalMomentumStatusText(row) }}
                  </span>
                </article>
              </div>
            </div>

            <p class="chart-note">{{ regionalMomentumNote }}</p>
          </article>

          <section class="mood-board region-bubble-section reaction-panel" aria-labelledby="mood-title">
            <div class="mood-header">
              <div>
                <p class="label">지금 뜨는 반응</p>
                <h3 id="mood-title">지역·단지 반응 한눈에</h3>
              </div>
              <div class="section-actions">
                <div class="period-tabs mood-period-tabs" aria-label="지역·단지별 반응 비교 기간">
                  <button
                    v-for="period in returnTimeModes"
                    :key="`mood-${period.id}`"
                    type="button"
                    :class="{ active: period.id === 'month' }"
                  >
                    {{ period.label }}
                  </button>
                </div>
                <RouterLink class="detail-link" to="/realestate/targets/region-seoul-mapo">자세히 보기 →</RouterLink>
              </div>
            </div>

            <div class="reaction-legend" aria-label="반응 아이콘 설명">
              <span>
                <svg class="reaction-icon" viewBox="0 0 20 20" aria-hidden="true">
                  <circle class="face-bg positive-bg" cx="10" cy="10" r="9.5"/>
                  <circle cx="7.2" cy="8.2" r="1.3" class="face-feature"/>
                  <circle cx="12.8" cy="8.2" r="1.3" class="face-feature"/>
                  <path d="M 6.5 12 Q 10 15.5 13.5 12" class="face-mouth"/>
                </svg>
                기대 반응
              </span>
              <span>
                <svg class="reaction-icon" viewBox="0 0 20 20" aria-hidden="true">
                  <circle class="face-bg negative-bg" cx="10" cy="10" r="9.5"/>
                  <circle cx="7.2" cy="8.2" r="1.3" class="face-feature"/>
                  <circle cx="12.8" cy="8.2" r="1.3" class="face-feature"/>
                  <path d="M 5.5 6.8 Q 7 5.5 8.5 6.8" class="face-brow"/>
                  <path d="M 11.5 6.8 Q 13 5.5 14.5 6.8" class="face-brow"/>
                  <path d="M 6.5 14 Q 10 11 13.5 14" class="face-mouth"/>
                </svg>
                우려 반응
              </span>
              <span>
                <svg class="reaction-icon" viewBox="0 0 20 20" aria-hidden="true">
                  <circle class="face-bg neutral-bg" cx="10" cy="10" r="9.5"/>
                  <circle cx="7.2" cy="8.2" r="1.3" class="face-feature"/>
                  <circle cx="12.8" cy="8.2" r="1.3" class="face-feature"/>
                  <line x1="7" y1="13" x2="13" y2="13" class="face-mouth face-neutral-mouth"/>
                </svg>
                중립·기타
              </span>
            </div>

            <div class="reaction-carousel" aria-label="지역별 반응 슬라이드">
              <p v-if="!dashboardReactionItems.length" class="newsroom-empty-state dashboard-reaction-empty">
                {{ dashboardReactionEmptyText }}
              </p>
              <div class="carousel-track-wrap">
                <div class="carousel-track" :style="{ transform: `translateX(-${currentSlide * 100}%)` }">
                  <article
                    v-for="item in dashboardReactionItems"
                    :key="item.targetId"
                    class="reaction-carousel-card"
                    :data-tone="item.reactionDirectionRatio.bullish >= item.reactionDirectionRatio.bearish ? 'positive' : 'negative'"
                  >
                    <div class="carousel-card-header">
                      <div class="carousel-card-title">
                        <strong class="carousel-region-name">{{ item.name }}</strong>
                        <span class="carousel-region-meta">{{ item.market }} · 열기 {{ item.heatScore }}</span>
                      </div>
                      <div class="carousel-mention-badge">
                        <em>{{ item.mentionCount }}</em>
                        <span>언급</span>
                      </div>
                    </div>

                    <div class="carousel-kw-columns">
                      <div class="kw-col kw-col-positive">
                        <div class="kw-col-label">
                          <svg class="reaction-icon" viewBox="0 0 20 20" aria-hidden="true">
                            <circle class="face-bg positive-bg" cx="10" cy="10" r="9.5"/>
                            <circle cx="7.2" cy="8.2" r="1.3" class="face-feature"/>
                            <circle cx="12.8" cy="8.2" r="1.3" class="face-feature"/>
                            <path d="M 6.5 12 Q 10 15.5 13.5 12" class="face-mouth"/>
                          </svg>
                          <span>기대</span>
                        </div>
                        <div :key="`pos-${currentSlide}`" class="kw-cloud">
                          <span
                            v-for="(kw, idx) in item.positiveKeywords"
                            :key="kw.word"
                            class="kw-word kw-word-positive"
                            :style="kwWordStyles[item.targetId]?.pos(idx)"
                          >{{ kw.word }}</span>
                        </div>
                      </div>
                      <div class="kw-divider" aria-hidden="true"></div>
                      <div class="kw-col kw-col-negative">
                        <div class="kw-col-label">
                          <svg class="reaction-icon" viewBox="0 0 20 20" aria-hidden="true">
                            <circle class="face-bg negative-bg" cx="10" cy="10" r="9.5"/>
                            <circle cx="7.2" cy="8.2" r="1.3" class="face-feature"/>
                            <circle cx="12.8" cy="8.2" r="1.3" class="face-feature"/>
                            <path d="M 5.5 6.8 Q 7 5.5 8.5 6.8" class="face-brow"/>
                            <path d="M 11.5 6.8 Q 13 5.5 14.5 6.8" class="face-brow"/>
                            <path d="M 6.5 14 Q 10 11 13.5 14" class="face-mouth"/>
                          </svg>
                          <span>우려</span>
                        </div>
                        <div :key="`neg-${currentSlide}`" class="kw-cloud">
                          <span
                            v-for="(kw, idx) in item.negativeKeywords"
                            :key="kw.word"
                            class="kw-word kw-word-negative"
                            :style="kwWordStyles[item.targetId]?.neg(idx)"
                          >{{ kw.word }}</span>
                        </div>
                      </div>
                    </div>

                    <div class="carousel-link-section">
                      <div class="carousel-link-col link-col-positive">
                        <span class="link-col-heading">기대 관련</span>
                        <a
                          v-for="link in item.positiveLinks"
                          :key="link.title"
                          class="carousel-link-row"
                          href="#"
                          @click.prevent
                        >
                          <span class="link-source">{{ link.source }}</span>
                          <span class="link-title">{{ link.title }}</span>
                        </a>
                      </div>
                      <div class="carousel-link-divider" aria-hidden="true"></div>
                      <div class="carousel-link-col link-col-negative">
                        <span class="link-col-heading">우려 관련</span>
                        <a
                          v-for="link in item.negativeLinks"
                          :key="link.title"
                          class="carousel-link-row"
                          href="#"
                          @click.prevent
                        >
                          <span class="link-source">{{ link.source }}</span>
                          <span class="link-title">{{ link.title }}</span>
                        </a>
                      </div>
                    </div>

                    <div class="reaction-track-wrap">
                      <div class="reaction-tooltip" aria-hidden="true">
                        <span class="st-positive">😊 기대 {{ ratioPct(item.reactionDirectionRatio.bullish) }}</span>
                        <span class="st-divider">·</span>
                        <span class="st-negative">😟 우려 {{ ratioPct(item.reactionDirectionRatio.bearish) }}</span>
                        <span class="st-divider">·</span>
                        <span class="st-neutral">중립 {{ ratioPct(item.reactionDirectionRatio.neutral) }}</span>
                      </div>
                      <div class="reaction-track" aria-label="긍정 부정 중립 비율">
                        <i class="positive" :style="`width: ${ratioPct(item.reactionDirectionRatio.bullish)}`"></i>
                        <i class="negative" :style="`width: ${ratioPct(item.reactionDirectionRatio.bearish)}`"></i>
                        <i class="neutral" :style="`width: ${ratioPct(item.reactionDirectionRatio.neutral)}`"></i>
                      </div>
                    </div>
                  </article>
                </div>
              </div>
            </div>

            <div v-if="dashboardReactionItems.length" class="carousel-controls">
              <button class="carousel-btn" type="button" @click="prevSlide" aria-label="이전 지역">
                <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3 L5 8 L10 13"/></svg>
              </button>
              <div class="carousel-dots" role="tablist" aria-label="슬라이드 선택">
                <button
                  v-for="(item, i) in dashboardReactionItems"
                  :key="`dot-${item.targetId}`"
                  :class="['carousel-dot', { active: i === currentSlide }]"
                  type="button"
                  role="tab"
                  :aria-selected="i === currentSlide"
                  :aria-label="`${item.name} 슬라이드`"
                  @click="goToSlide(i)"
                >{{ i + 1 }}</button>
              </div>
              <button class="carousel-btn" type="button" @click="nextSlide" aria-label="다음 지역">
                <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3 L11 8 L6 13"/></svg>
              </button>
              <button
                :class="['carousel-btn', 'carousel-pause-btn', { paused: isPaused }]"
                type="button"
                @click="togglePause"
                :aria-label="isPaused ? '자동 재생' : '슬라이드 고정'"
              >
                <svg v-if="isPaused" viewBox="0 0 16 16" aria-hidden="true">
                  <path d="M5 3 L13 8 L5 13 Z" class="play-triangle"/>
                </svg>
                <svg v-else viewBox="0 0 16 16" aria-hidden="true">
                  <rect x="4" y="3" width="3" height="10" rx="1" class="pause-bar"/>
                  <rect x="9" y="3" width="3" height="10" rx="1" class="pause-bar"/>
                </svg>
              </button>
            </div>
          </section>
        </section>

        <section class="indicator-section" aria-labelledby="indicator-title">
          <div class="section-title-row">
            <div>
              <p class="label">real estate pulse</p>
              <h3 id="indicator-title">주요 부동산 지표</h3>
            </div>
            <div class="section-actions">
              <div class="period-tabs indicator-period-tabs" aria-label="주요 부동산 지표 기간">
                <button
                  v-for="mode in returnTimeModes"
                  :key="`indicator-${mode.id}`"
                  type="button"
                  :class="{ active: mode.id === 'month' }"
                >
                  {{ mode.label }}
                </button>
              </div>
              <span :class="['status-pill', marketIndicatorLoadState === 'live' ? '' : 'warning']">
                {{ marketIndicatorStatusLabel() }}
              </span>
              <RouterLink class="detail-link" to="/indicators">자세히 보기 →</RouterLink>
            </div>
          </div>

          <div class="indicator-grid">
            <p v-if="!marketIndicators.length" class="newsroom-empty-state dashboard-indicator-empty">
              {{
                marketIndicatorLoadState === 'loading'
                  ? '주요 지표를 불러오는 중입니다.'
                  : marketIndicatorLoadState === 'error'
                    ? '시장 요약 API를 불러오지 못했습니다. provider/asOf 확인이 필요합니다.'
                    : '수집된 주요 지표가 아직 없습니다. 수집 전/insufficient 상태입니다.'
              }}
            </p>
            <article
              v-for="indicator in marketIndicators"
              :key="indicator.label"
              :class="['indicator-card', trendClass(indicator.trend)]"
            >
              <div class="indicator-copy">
                <span>{{ indicator.label }}</span>
                <strong>{{ indicator.value }}</strong>
                <em>{{ formatPct(indicator.changePct) }}</em>
              </div>
              <small>{{ indicator.updatedLabel }}</small>
            </article>
          </div>
        </section>

        <section class="news-macro-grid">
          <article class="panel news-feed content-feed-card live-feed-card" aria-labelledby="news-title">
            <div class="panel-header">
              <div>
                <p class="label">live feed</p>
                <h3 id="news-title">실시간 뉴스</h3>
              </div>
              <div class="section-actions">
                <span class="status-pill subtle">{{ dashboardContentStatusLabel }}</span>
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'news' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <p v-if="!dashboardNewsItems.length" class="newsroom-empty-state">{{ dashboardContentEmptyText }}</p>
              <a
                v-for="news in dashboardNewsItems"
                :key="news.id"
                class="feed-row"
                :href="news.url"
                target="_blank"
                rel="noreferrer noopener"
              >
                <span
                  :class="['site-icon', 'real-icon', 'news-source', news.iconClass]"
                  :aria-label="`${news.source} ${news.category}`"
                  role="img"
                >
                  <img :src="sourceIconUrl(news.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
                </span>
                <span class="feed-copy">
                  <strong :title="news.title">{{ news.title }}</strong>
                  <em>{{ news.source }} · {{ news.meta }} · {{ news.statusLabel }}</em>
                </span>
              </a>
            </div>
          </article>

          <article class="panel news-feed analyst-feed content-feed-card report-feed-card" aria-labelledby="analyst-title">
            <div class="panel-header">
              <div>
                <p class="label">research feed</p>
                <h3 id="analyst-title">정책·통계 리포트</h3>
              </div>
              <div class="section-actions">
                <span class="status-pill subtle">{{ dashboardContentStatusLabel }}</span>
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'reports' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <p v-if="!dashboardReportItems.length" class="newsroom-empty-state">{{ dashboardContentEmptyText }}</p>
              <a
                v-for="report in dashboardReportItems"
                :key="report.id"
                class="feed-row"
                :href="report.url"
                target="_blank"
                rel="noreferrer noopener"
              >
                <span
                  :class="['site-icon', 'real-icon', 'news-source', report.iconClass]"
                  :aria-label="`${report.source} ${report.category}`"
                  role="img"
                >
                  <img :src="sourceIconUrl(report.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
                </span>
                <span class="feed-copy">
                  <strong :title="report.title">{{ report.title }}</strong>
                  <em>{{ report.source }} · {{ report.meta }} · {{ report.statusLabel }}</em>
                </span>
              </a>
            </div>
          </article>

          <article class="panel external-content-panel content-feed-card video-feed-card" aria-labelledby="external-video-title">
            <div class="panel-header">
              <div>
                <p class="label">outside links</p>
                <h3 id="external-video-title">부동산 영상 새 글</h3>
              </div>
              <div class="section-actions">
                <span class="status-pill subtle">{{ dashboardContentStatusLabel }}</span>
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'videos' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <p v-if="!dashboardVideoItems.length" class="newsroom-empty-state">{{ dashboardContentEmptyText }}</p>
              <a
                v-for="(video, index) in dashboardVideoItems"
                :key="video.id"
                class="feed-row ranked-feed-row"
                :href="video.url"
                target="_blank"
                rel="noreferrer noopener"
              >
                <span class="feed-rank">{{ video.rankLabel ?? `${index + 1}위` }}</span>
                <span
                  :class="['site-icon', 'real-icon', 'source-badge', video.iconClass]"
                  :aria-label="`${video.source} ${video.category}`"
                  role="img"
                >
                  <img :src="sourceIconUrl(video.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
                </span>
                <span class="feed-copy">
                  <strong :title="video.title">{{ video.title }}</strong>
                  <em>{{ video.source }} · {{ video.meta }} · {{ video.statusLabel }}</em>
                </span>
              </a>
            </div>
          </article>

          <article class="panel external-content-panel content-feed-card link-feed-card" aria-labelledby="external-link-title">
            <div class="panel-header">
              <div>
                <p class="label">columns · community</p>
                <h3 id="external-link-title">블로그와 커뮤니티 링크</h3>
              </div>
              <div class="section-actions">
                <span class="status-pill subtle">{{ dashboardContentStatusLabel }}</span>
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'links' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <p v-if="!dashboardLinkItems.length" class="newsroom-empty-state">{{ dashboardContentEmptyText }}</p>
              <a
                v-for="(link, index) in dashboardLinkItems"
                :key="link.id"
                class="feed-row ranked-feed-row"
                :href="link.url"
                target="_blank"
                rel="noreferrer noopener"
              >
                <span class="feed-rank">{{ link.rankLabel ?? `${index + 1}위` }}</span>
                <span
                  :class="['site-icon', 'real-icon', 'source-badge', link.iconClass]"
                  :aria-label="`${link.source} ${link.category}`"
                  role="img"
                >
                  <img :src="sourceIconUrl(link.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
                </span>
                <span class="feed-copy">
                  <strong :title="link.title">{{ link.title }}</strong>
                  <em>{{ link.source }} · {{ link.meta }} · {{ link.statusLabel }}</em>
                </span>
              </a>
            </div>
          </article>
        </section>

        <section class="page-grid">
          <article class="panel" aria-labelledby="market-facts-title">
            <div class="panel-header">
              <div>
                <p class="label">market facts</p>
                <h3 id="market-facts-title">실거래·지표 상태</h3>
              </div>
              <div class="section-actions">
                <span :class="['status-pill', marketFactLoadState === 'live' ? '' : 'warning']">
                  {{ marketFactLoadState === 'live' ? 'API 반영' : '공공데이터 대기' }}
                </span>
                <RouterLink class="detail-link" to="/indicators">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="compact-list">
              <div v-for="row in marketFactRows" :key="row.id" class="compact-row market-fact-row">
                <strong>{{ row.name }}</strong>
                <span>{{ row.value }}</span>
                <em>{{ row.meta }}</em>
                <span :class="['status-pill', row.stale ? 'warning' : '']">
                  {{ row.statusLabel }}
                </span>
              </div>
            </div>
          </article>

          <article class="panel planning-boundary compact-boundary" aria-labelledby="confirm-title">
            <div>
              <p class="label">planning</p>
              <h3 id="confirm-title">확인 필요</h3>
            </div>
            <ul class="check-list compact-check-list">
              <li v-for="item in confirmationNeeded" :key="item">{{ item }}</li>
            </ul>
          </article>
        </section>
      </div>

      <aside class="side-drawer" aria-label="오른쪽 빠른 패널">
        <div class="drawer-tabs" aria-label="라이브 패널 탭" role="tablist">
          <button
            v-for="tab in drawerTabs"
            :key="tab.id"
            :class="['drawer-tab', { active: activeDrawerTab === tab.id }]"
            type="button"
            role="tab"
            :aria-selected="activeDrawerTab === tab.id"
            @click="activeDrawerTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <section v-show="activeDrawerTab === 'reaction'" class="drawer-tab-screen drawer-reaction-screen">
          <div v-if="topRiser" class="drawer-card hot-region-panel" aria-labelledby="hot-region-title">
            <p class="label">라이브 패널 · 지금 언급 급상승 지역</p>
            <h3 id="hot-region-title">{{ topRiser.name }}</h3>
            <strong>{{ formatPct(topRiser.mentionDeltaPct) }}</strong>
            <span>{{ topRiser.targetId }} · 언급 {{ topRiser.previousMentionCount }} → {{ topRiser.mentionCount }}</span>
            <div class="hot-region-metrics">
              <div>
                <span>열기</span>
                <em>{{ topRiser.heatScore }}</em>
              </div>
              <div>
                <span>시장</span>
                <em>{{ topRiser.market }}</em>
              </div>
            </div>
            <div class="hot-region-drivers" aria-label="이 지역 반응이 움직인 이유">
              <p>왜 움직였나</p>
              <div>
                <span v-for="driver in topRiser.reactionDrivers" :key="`${driver.type}-${driver.label}`" class="hot-region-driver">
                  <small>{{ driver.type }}</small>
                  {{ driver.label }}
                </span>
              </div>
            </div>
            <ul class="movement-reasons">
              <li v-for="reason in topRiser.movementReasons" :key="reason">{{ reason }}</li>
            </ul>
          </div>
          <div v-else class="drawer-card hot-region-panel" aria-labelledby="hot-region-title-empty">
            <p class="label">라이브 패널 · 지금 언급 급상승 지역</p>
            <h3 id="hot-region-title-empty">수집 전</h3>
            <strong>insufficient</strong>
            <span>{{ dashboardReactionEmptyText }}</span>
          </div>
          <div class="drawer-card drawer-rising-stars" aria-labelledby="drawer-rising-title">
            <div class="drawer-section-title">
              <p class="label">early signal</p>
              <h3 id="drawer-rising-title">라이징 스타</h3>
              <RouterLink class="detail-link" to="/realestate/targets/region-seoul-mapo">자세히 보기 →</RouterLink>
            </div>
            <div class="drawer-rising-list">
              <p v-if="!risingStars.length" class="newsroom-empty-state">
                {{ dashboardReactionEmptyText }}
              </p>
              <article v-for="item in risingStars" :key="item.targetId">
                <strong>{{ item.name }}</strong>
                <span>{{ item.targetId }} · 언급 {{ item.previousMentionCount }} → {{ item.mentionCount }}</span>
                <em>{{ formatPct(item.mentionDeltaPct) }}</em>
              </article>
            </div>
          </div>
          <div class="drawer-feed">
            <p v-if="!marketIndicators.length" class="newsroom-empty-state">
              {{ marketIndicatorStatusLabel() }}
            </p>
            <div v-for="indicator in marketIndicators.slice(0, 3)" :key="indicator.label">
              <span>{{ indicator.label }}</span>
              <strong>{{ indicator.value }}</strong>
              <em :class="trendClass(indicator.trend)">{{ formatPct(indicator.changePct) }}</em>
            </div>
          </div>
        </section>

        <section
          v-show="activeDrawerTab === 'metrics'"
          class="drawer-tab-panel drawer-metric-panel"
          aria-label="지표 탭 미리보기"
        >
          <div class="drawer-section-title compact">
            <p class="label">indices</p>
            <h3>지표</h3>
          </div>
          <div class="drawer-mini-bars">
            <p v-if="!marketIndicators.length" class="newsroom-empty-state">
              {{ marketIndicatorStatusLabel() }}
            </p>
            <div v-for="indicator in marketIndicators.slice(0, 4)" :key="`${indicator.label}-bar`">
              <span>{{ indicator.label }}</span>
              <i :class="trendClass(indicator.trend)"></i>
              <strong>{{ formatPct(indicator.changePct) }}</strong>
            </div>
          </div>
        </section>

        <section
          v-show="activeDrawerTab === 'watch'"
          class="drawer-tab-panel drawer-watch-panel"
          aria-label="관심 탭 미리보기"
        >
          <div class="drawer-section-title compact">
            <p class="label">watch</p>
            <h3>관심</h3>
          </div>
          <div class="drawer-watch-list">
            <p v-if="!dashboardReactionItems.length" class="newsroom-empty-state">
              {{ dashboardReactionEmptyText }}
            </p>
            <article v-for="item in dashboardReactionItems.slice(0, 4)" :key="`${item.targetId}-watch`">
              <strong>{{ item.name }}</strong>
              <span>{{ item.targetId }}</span>
              <em>{{ formatPct(item.mentionDeltaPct) }}</em>
            </article>
          </div>
        </section>
      </aside>
    </section>
  </section>
</template>
