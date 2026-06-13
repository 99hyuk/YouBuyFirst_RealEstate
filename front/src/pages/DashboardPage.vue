<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import dashboardSummary from '../fixtures/dashboard-summary.json';
import reactionRanking from '../fixtures/reaction-ranking.json';
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
const returnTimeModes = ['주', '월', '6개월', '년'];
const drawerTabs = [
  { id: 'reaction', label: '반응' },
  { id: 'metrics', label: '지표' },
  { id: 'watch', label: '관심' }
];
const activeDrawerTab = ref('reaction');
const speculationHeatIndex = dashboardSummary.speculationHeatIndex;
const topRiser = dashboardSummary.risingStars[0];
const totalMentions = reactionRanking.items.reduce((sum, item) => sum + item.mentionCount, 0);
const marketIndicators = ref<RealEstateMarketIndicatorCard[]>(dashboardSummary.marketIndicators);
const marketFactRows = ref<RealEstateMarketFactRow[]>(buildMarketFactRows([]));
const marketIndicatorLoadState = ref<'loading' | 'live' | 'fallback'>('loading');
const marketFactLoadState = ref<'loading' | 'live' | 'fallback'>('loading');
type ReactionRankingItem = (typeof reactionRanking.items)[number];
type ReactionMetric = 'bullish' | 'bearish';

const reactionSignalScore = (item: ReactionRankingItem, metric: ReactionMetric) =>
  Math.round(item.mentionCount * item.reactionDirectionRatio[metric]);
const buildReactionGroup = (id: 'positive' | 'negative', label: string, caption: string, metric: ReactionMetric) => ({
  id,
  label,
  caption,
  metric,
  ratioLabel: metric === 'bullish' ? '기대' : '우려',
  items: [...reactionRanking.items]
    .sort((left, right) => reactionSignalScore(right, metric) - reactionSignalScore(left, metric))
    .slice(0, 3)
});
const reactionSignalGroups = [
  buildReactionGroup('positive', '언급+기대 TOP 3', '언급량 x 기대', 'bullish'),
  buildReactionGroup('negative', '언급+우려 TOP 3', '언급량 x 우려', 'bearish')
];

const currentSlide = ref(0);
const isPaused = ref(false);
const totalSlides = reactionRanking.items.length;
let autoSlideTimer: ReturnType<typeof setInterval> | undefined;

const startTimer = () => {
  if (autoSlideTimer) clearInterval(autoSlideTimer);
  autoSlideTimer = setInterval(() => { currentSlide.value = (currentSlide.value + 1) % totalSlides; }, 4500);
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
  try {
    const summary = await fetchRealEstateMarketSummary();
    marketIndicators.value = buildMarketSummaryIndicators(summary, dashboardSummary.marketIndicators);
    marketIndicatorLoadState.value = summary.items.length ? 'live' : 'fallback';
  } catch {
    marketIndicators.value = dashboardSummary.marketIndicators;
    marketIndicatorLoadState.value = 'fallback';
  }
};
const resetTimer = () => { if (!isPaused.value) startTimer(); };
const prevSlide = () => { currentSlide.value = (currentSlide.value - 1 + totalSlides) % totalSlides; resetTimer(); };
const nextSlide = () => { currentSlide.value = (currentSlide.value + 1) % totalSlides; resetTimer(); };
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

const kwWordStyles = Object.fromEntries(
  reactionRanking.items.map(item => [
    item.targetId,
    { pos: placeWords(item.positiveKeywords), neg: placeWords(item.negativeKeywords) },
  ])
);

onMounted(() => {
  startTimer();
  void refreshMarketSummary();
  void refreshMarketFacts();
});
onUnmounted(() => clearInterval(autoSlideTimer));

type TooltipPoint = { x: number; y: number; value: number; color: string; region: string } | null;
const hoveredPoint = ref<TooltipPoint>(null);

const formatPct = (value: number | null) => value === null ? '최신' : `${value > 0 ? '+' : ''}${value}%`;
const ratioPct = (value: number) => `${Math.round(value * 100)}%`;
const trendClass = (trend: string) => (trend === 'down' ? 'down' : 'up');
const marketIndicatorStatusLabel = () => {
  if (marketIndicatorLoadState.value === 'live') return 'API 반영';
  if (marketIndicatorLoadState.value === 'loading') return '불러오는 중';
  return 'mock fallback';
};
const hideBrokenIcon = (event: Event) => {
  const image = event.target as HTMLImageElement;
  image.hidden = true;
  image.closest('.site-icon')?.classList.remove('real-icon');
};
const newsIconClass = (tag: string) => {
  const map: Record<string, string> = {
    macro: 'news-macro',
    index: 'news-index',
    community: 'community',
    research: 'news-research',
    strategy: 'news-research',
    disclosure: 'news-market'
  };

  return map[tag] ?? 'news';
};
const externalIconClass = (item: { type: string; source?: string; iconDomain?: string }) => {
  if (item.type === 'youtube') return 'youtube';
  if (item.iconDomain === 'blog.naver.com') return 'naver-blog';
  if (item.iconDomain === 'finance.naver.com') return 'naver';
  if (item.iconDomain === 'www.tossinvest.com') return 'toss';
  return item.type;
};
type SeriesPoint = { x: number; y: number };

const wideX = (x: number) => Math.round(50 + x * 3.65);
const wideY = (y: number) => Math.round(54 + (y - 58) * 8);
const widePointString = (pointString: string) =>
  pointString
    .split(' ')
    .map((pair) => {
      const [x, y] = pair.split(',').map(Number);
      return `${wideX(x)},${wideY(y)}`;
    })
    .join(' ');
const endLabelX = (points: SeriesPoint[]) => Math.min(wideX(points[points.length - 1]?.x ?? 0) + 8, 1138);
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
const needleEnd = gaugePoint(speculationHeatIndex.value, 56);
</script>

<template>
  <section class="dashboard-page">
    <section class="standalone-search" aria-label="대시보드 검색과 필터">
      <p class="eyebrow">{{ reactionRanking.windowLabel }} · mock data</p>
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
          <button class="mock-search" type="button" disabled>
            <span class="search-icon" aria-hidden="true"></span>
            <strong>/</strong>
            <span>지역이나 단지 검색</span>
          </button>
        </div>
        <p>{{ dashboardSummary.headline }}</p>
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
        <span>관찰 <strong>{{ reactionRanking.items.length }}곳</strong></span>
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
                <span class="status-pill warning">mock</span>
                <RouterLink class="detail-link" to="/realestate/map">지도에서 보기 →</RouterLink>
              </div>
            </div>

            <div class="community-graph regional-graph" aria-label="핵심 지역별 상승률 그래프">
              <div class="community-graph-topline">
                <div class="return-range-tabs in-graph-tabs" aria-label="지역 상승률 기간">
                  <button
                    v-for="mode in returnTimeModes"
                    :key="mode"
                    type="button"
                    :class="{ active: mode === '월' }"
                  >
                    {{ mode }}
                  </button>
                </div>
                <div class="graph-legend in-graph" aria-label="지역별 색상 범례">
                  <div v-for="series in dashboardSummary.regionalReturnSeries" :key="series.region" class="legend-item">
                    <span class="legend-swatch" :style="`--swatch: ${series.color}`"></span>
                    <strong>{{ series.region }}</strong>
                  </div>
                </div>
              </div>
              <svg viewBox="0 0 1200 900" preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby="return-title">
                <text class="axis-title" x="50" y="50">price change (%)</text>
                <line class="chart-grid" x1="50" x2="1142" y1="90" y2="90" />
                <line class="chart-grid" x1="50" x2="1142" y1="250" y2="250" />
                <line class="chart-grid" x1="50" x2="1142" y1="410" y2="410" />
                <line class="chart-grid" x1="50" x2="1142" y1="570" y2="570" />
                <line class="chart-grid" x1="50" x2="1142" y1="730" y2="730" />
                <line class="chart-grid vertical" x1="320" x2="320" y1="90" y2="780" />
                <line class="chart-grid vertical" x1="525" x2="525" y1="90" y2="780" />
                <line class="chart-grid vertical" x1="729" x2="729" y1="90" y2="780" />
                <line class="chart-grid vertical" x1="933" x2="933" y1="90" y2="780" />
                <line class="chart-grid vertical" x1="1138" x2="1138" y1="90" y2="780" />
                <line class="chart-y-axis" x1="50" x2="50" y1="90" y2="780" />
                <line class="chart-x-axis" x1="50" x2="1142" y1="780" y2="780" />
                <line class="chart-zero-line" x1="50" x2="1142" y1="570" y2="570" />
                <text class="axis-label" x="0" y="100">+6%</text>
                <text class="axis-label" x="18" y="580">0</text>
                <text class="axis-label" x="0" y="790">-2%</text>
                <text class="axis-label y-axis-right" x="1152" y="100">+6.0</text>
                <text class="axis-label y-axis-right" x="1152" y="580">0.0</text>
                <text class="axis-label y-axis-right" x="1152" y="790">-2.0</text>
                <text class="axis-label x-axis" x="116" y="850">D-30</text>
                <text class="axis-label x-axis" x="320" y="850">D-21</text>
                <text class="axis-label x-axis" x="525" y="850">D-14</text>
                <text class="axis-label x-axis" x="729" y="850">D-7</text>
                <text class="axis-label x-axis" x="933" y="850">D-3</text>
                <text class="axis-label x-axis" x="1138" y="850">현재</text>
                <polyline
                  v-for="series in dashboardSummary.regionalReturnSeries"
                  :key="`${series.region}-line`"
                  class="return-line"
                  :points="widePointString(series.pointString)"
                  :stroke="series.color"
                />
                <g v-for="series in dashboardSummary.regionalReturnSeries" :key="`${series.region}-points`">
                  <circle
                    v-for="point in series.points"
                    :key="`${series.region}-${point.x}-${point.y}`"
                    class="return-dot"
                    :cx="wideX(point.x)"
                    :cy="wideY(point.y)"
                    r="10"
                    :fill="series.color"
                    pointer-events="none"
                  />
                  <!-- transparent hit area for easier hover -->
                  <circle
                    v-for="point in series.points"
                    :key="`hit-${series.region}-${point.x}-${point.y}`"
                    :cx="wideX(point.x)"
                    :cy="wideY(point.y)"
                    r="24"
                    fill="transparent"
                    style="cursor: crosshair"
                    @mouseenter="hoveredPoint = { x: wideX(point.x), y: wideY(point.y), value: point.value, color: series.color, region: series.region }"
                    @mouseleave="hoveredPoint = null"
                  />
                </g>
                <text
                  v-for="series in dashboardSummary.regionalReturnSeries"
                  :key="`${series.region}-end-label`"
                  class="series-end-label"
                  :x="endLabelX(series.points)"
                  :y="wideY(series.points[series.points.length - 1].y) + 8"
                  :fill="series.color"
                >
                  {{ formatPct(series.returnPct) }}
                </text>

                <!-- hover tooltip -->
                <g
                  v-if="hoveredPoint"
                  :transform="`translate(${hoveredPoint.x}, ${hoveredPoint.y})`"
                  class="chart-tooltip-group"
                  pointer-events="none"
                >
                  <template v-if="hoveredPoint.y >= 120">
                    <path d="M -11,-22 L 0,-7 L 11,-22 Z" :fill="hoveredPoint.color"/>
                    <rect x="-88" y="-96" width="176" height="74" rx="10" :fill="hoveredPoint.color" opacity="0.94"/>
                    <text x="0" y="-72" text-anchor="middle" class="tooltip-region-text">{{ hoveredPoint.region }}</text>
                    <text x="0" y="-40" text-anchor="middle" class="tooltip-value-text">{{ formatPct(hoveredPoint.value) }}</text>
                  </template>
                  <template v-else>
                    <path d="M -11,22 L 0,7 L 11,22 Z" :fill="hoveredPoint.color"/>
                    <rect x="-88" y="24" width="176" height="74" rx="10" :fill="hoveredPoint.color" opacity="0.94"/>
                    <text x="0" y="48" text-anchor="middle" class="tooltip-region-text">{{ hoveredPoint.region }}</text>
                    <text x="0" y="80" text-anchor="middle" class="tooltip-value-text">{{ formatPct(hoveredPoint.value) }}</text>
                  </template>
                </g>
              </svg>
            </div>

            <p class="chart-note">핵심 지역별 상승률 fixture · 실거래 신고 지연 보정 전 · 부동산 자문 아님</p>
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
                    v-for="period in dashboardSummary.moodPeriods"
                    :key="period"
                    type="button"
                    :class="{ active: period === dashboardSummary.activeMoodPeriod }"
                  >
                    {{ period }}
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
              <div class="carousel-track-wrap">
                <div class="carousel-track" :style="{ transform: `translateX(-${currentSlide * 100}%)` }">
                  <article
                    v-for="item in reactionRanking.items"
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
                            :style="kwWordStyles[item.targetId].pos(idx)"
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
                            :style="kwWordStyles[item.targetId].neg(idx)"
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

            <div class="carousel-controls">
              <button class="carousel-btn" type="button" @click="prevSlide" aria-label="이전 지역">
                <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3 L5 8 L10 13"/></svg>
              </button>
              <div class="carousel-dots" role="tablist" aria-label="슬라이드 선택">
                <button
                  v-for="(item, i) in reactionRanking.items"
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
                  :key="`indicator-${mode}`"
                  type="button"
                  :class="{ active: mode === '월' }"
                >
                  {{ mode }}
                </button>
              </div>
              <span :class="['status-pill', marketIndicatorLoadState === 'live' ? '' : 'warning']">
                {{ marketIndicatorStatusLabel() }}
              </span>
              <RouterLink class="detail-link" to="/indicators">자세히 보기 →</RouterLink>
            </div>
          </div>

          <div class="indicator-grid">
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
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'news' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <a
                v-for="news in dashboardSummary.liveNews.slice(0, 5)"
                :key="news.title"
                class="feed-row"
                :href="news.url"
                target="_blank"
                rel="noreferrer noopener"
              >
                <span
                  :class="['site-icon', 'real-icon', 'news-source', newsIconClass(news.tag)]"
                  :aria-label="`${news.source} ${news.tag}`"
                  role="img"
                >
                  <img :src="sourceIconUrl(news.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
                </span>
                <span class="feed-copy">
                  <strong :title="news.title">{{ news.title }}</strong>
                  <em>{{ news.source }} · {{ news.timeLabel }}</em>
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
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'reports' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <a
                v-for="report in dashboardSummary.analystReports.slice(0, 5)"
                :key="report.title"
                class="feed-row"
                :href="report.url"
                target="_blank"
                rel="noreferrer noopener"
              >
                <span
                  :class="['site-icon', 'real-icon', 'news-source', newsIconClass(report.tag)]"
                  :aria-label="`${report.source} ${report.tag}`"
                  role="img"
                >
                  <img :src="sourceIconUrl(report.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
                </span>
                <span class="feed-copy">
                  <strong :title="report.title">{{ report.title }}</strong>
                  <em>{{ report.source }} · {{ report.timeLabel }}</em>
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
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'videos' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <a
                v-for="(video, index) in dashboardSummary.externalContent.videos.slice(0, 5)"
                :key="video.url"
                class="feed-row ranked-feed-row"
                :href="video.url"
                target="_blank"
                rel="noreferrer noopener"
              >
                <span class="feed-rank">{{ index + 1 }}위</span>
                <span
                  :class="['site-icon', 'real-icon', 'source-badge', externalIconClass(video)]"
                  :aria-label="`${video.source} ${video.typeLabel}`"
                  role="img"
                >
                  <img :src="sourceIconUrl(video.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
                </span>
                <span class="feed-copy">
                  <strong :title="video.title">{{ video.title }}</strong>
                  <em>{{ video.source }} · {{ video.publishedLabel }} · {{ video.engagementLabel }}</em>
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
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'links' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <a
                v-for="(link, index) in dashboardSummary.externalContent.links.slice(0, 5)"
                :key="link.url"
                class="feed-row ranked-feed-row"
                :href="link.url"
                target="_blank"
                rel="noreferrer noopener"
              >
                <span class="feed-rank">{{ index + 1 }}위</span>
                <span
                  :class="['site-icon', 'real-icon', 'source-badge', externalIconClass(link)]"
                  :aria-label="`${link.source} ${link.typeLabel}`"
                  role="img"
                >
                  <img :src="sourceIconUrl(link.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
                </span>
                <span class="feed-copy">
                  <strong :title="link.title">{{ link.title }}</strong>
                  <em>{{ link.source }} · {{ link.publishedLabel }} · {{ link.engagementLabel }}</em>
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
              <li v-for="item in dashboardSummary.confirmationNeeded" :key="item">{{ item }}</li>
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
          <div class="drawer-card hot-region-panel" aria-labelledby="hot-region-title">
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
          <div class="drawer-card drawer-rising-stars" aria-labelledby="drawer-rising-title">
            <div class="drawer-section-title">
              <p class="label">early signal</p>
              <h3 id="drawer-rising-title">라이징 스타</h3>
              <RouterLink class="detail-link" to="/realestate/targets/region-seoul-mapo">자세히 보기 →</RouterLink>
            </div>
            <div class="drawer-rising-list">
              <article v-for="item in dashboardSummary.risingStars" :key="item.targetId">
                <strong>{{ item.name }}</strong>
                <span>{{ item.targetId }} · 언급 {{ item.previousMentionCount }} → {{ item.mentionCount }}</span>
                <em>{{ formatPct(item.mentionDeltaPct) }}</em>
              </article>
            </div>
          </div>
          <div class="drawer-feed">
            <div v-for="indicator in dashboardSummary.marketIndicators.slice(0, 3)" :key="indicator.label">
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
            <div v-for="indicator in dashboardSummary.marketIndicators.slice(0, 4)" :key="`${indicator.label}-bar`">
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
            <article v-for="item in reactionRanking.items.slice(0, 4)" :key="`${item.targetId}-watch`">
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
