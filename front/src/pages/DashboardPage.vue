<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import {
  buildNewsroomFeedItems,
  ensureNewsroomCategoryCoverage,
  fetchRealEstateNewsroom,
  type NewsroomCategory,
  type NewsroomFeedItem
} from '../lib/realestate-content';
import {
  dashboardReturnModes
} from '../lib/realestate-dashboard';
import {
  fetchRealEstateReactionRankingWithFallback,
  type RealEstateReactionRanking,
  type RealEstateReactionRankingItem,
  type RealEstateReactionIssue
} from '../lib/realestate-reactions';
import {
  buildMarketSummaryIndicators,
  fetchRealEstateMarketSummary,
  realEstateMarketIndicatorFallbacks,
  type RealEstateMarketIndicatorCard
} from '../lib/realestate-market-facts';
import { sourceIconUrl } from '../lib/source-icons';

const returnTimeModes = dashboardReturnModes;
const marketIndicators = ref<RealEstateMarketIndicatorCard[]>([]);
const dashboardContentItems = ref<NewsroomFeedItem[]>([]);
const dashboardContentLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const dashboardContentFeeds: NewsroomCategory[] = ['news', 'reports', 'videos', 'links'];
const dashboardContentPageSize = 100;
const isRefreshing = ref(false);
const lastRefreshedAt = ref<Date | null>(null);
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
const dashboardReactionRanking = ref<RealEstateReactionRanking | null>(null);
const reactionRankingLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
type ReactionMetric = 'bullish' | 'bearish';
type DailyBriefingItem = {
  id: string;
  text: string;
  tone: string;
};

const topRiser = computed(() => dashboardReactionItems.value[0] ?? null);
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
const topBriefingIssues = computed(() => {
  const scores = new Map<string, number>();
  dashboardReactionItems.value.slice(0, 6).forEach((item) => {
    item.issueMix.forEach((issue) => {
      scores.set(issue.label, (scores.get(issue.label) ?? 0) + item.mentionCount * Math.max(issue.share, 0.05));
    });
  });

  return [...scores.entries()]
    .sort((left, right) => right[1] - left[1])
    .slice(0, 3)
    .map(([label]) => label);
});

const objectParticle = (word: string) => {
  const lastChar = word.trim().at(-1);
  if (!lastChar) return '을';
  const code = lastChar.charCodeAt(0);
  if (code < 0xac00 || code > 0xd7a3) return '을';
  return (code - 0xac00) % 28 === 0 ? '를' : '을';
};

const dailyBriefingItems = computed<DailyBriefingItem[]>(() => {
  const issues = topBriefingIssues.value;
  const topTarget = topRiser.value;
  const issuePhrase = issues.length ? `${issues.join('·')} 쟁점의 ` : '';
  const newsCount = dashboardNewsItems.value.length;
  const reportCount = dashboardReportItems.value.length;
  const videoCount = dashboardVideoItems.value.length;
  const contentSummary = dashboardContentLoadState.value === 'loading'
    ? '최근 뉴스와 리포트 후보를 불러오는 중입니다.'
    : dashboardContentLoadState.value === 'error'
      ? '뉴스룸 수집 상태 확인이 필요합니다.'
      : newsCount + reportCount + videoCount
        ? `뉴스 ${newsCount}건, 리포트 ${reportCount}건, 영상 ${videoCount}건을 우선 확인합니다.`
        : '최근 이슈 후보가 아직 충분히 분리되지 않았습니다.';

  return [
    {
      id: 'reaction',
      text: topTarget
        ? `${topTarget.name}${objectParticle(topTarget.name)} 중심으로 ${issuePhrase}반응이 모이고 있습니다.`
        : '지역 반응 데이터가 아직 충분하지 않아 오늘의 쟁점 후보를 더 모아야 합니다.',
      tone: 'reaction'
    },
    {
      id: 'indicator',
      text: marketIndicators.value.length
        ? `공식 지표는 ${marketIndicators.value.slice(0, 2).map((indicator) => `${indicator.label} ${indicator.value}`).join(', ')} 흐름을 함께 봐야 합니다.`
        : '공식 지표 수집이 아직 대기 중이라 가격 흐름 판단은 보류해야 합니다.',
      tone: 'indicator'
    },
    {
      id: 'issue',
      text: contentSummary,
      tone: 'issue'
    }
  ];
});

const currentSlide = ref(0);
const isPaused = ref(false);
const totalSlides = computed(() => Math.max(dashboardReactionItems.value.length, 1));
let autoSlideTimer: ReturnType<typeof setInterval> | undefined;

const startTimer = () => {
  if (autoSlideTimer) clearInterval(autoSlideTimer);
  autoSlideTimer = setInterval(() => { currentSlide.value = (currentSlide.value + 1) % totalSlides.value; }, 4500);
};
const refreshMarketSummary = async () => {
  try {
    const summary = await fetchRealEstateMarketSummary();
    marketIndicators.value = buildMarketSummaryIndicators(summary, realEstateMarketIndicatorFallbacks);
  } catch {
    marketIndicators.value = [];
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
      '실거래·전세 흐름과 연결하려면 다음 배치의 시장 사실 확인이 필요합니다.'
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
      { title: `기대 쟁점: ${(expectationIssues[0] ?? topIssues[0]).label}`, source: '반응 스냅샷' },
      { title: `표본 신뢰도 ${Math.round(item.confidence * 100)}%`, source: coverageStatusLabel(item.coverageStatus) }
    ],
    negativeLinks: [
      { title: `우려 쟁점: ${(concernIssues[0] ?? topIssues[0]).label}`, source: '반응 스냅샷' },
      { title: item.stale ? '수집 지연 가능' : `출처 ${item.sourceCount}곳`, source: item.stale ? '갱신 지연' : '출처 범위' }
    ],
    priceStatus: item.stale ? '반응 스냅샷 갱신 지연' : '시장 사실 별도 확인',
    dataStatus: item.stale ? '갱신 지연' : coverageStatusLabel(item.coverageStatus),
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
  dashboardReactionRanking.value = null;
  currentSlide.value = 0;
  try {
    const ranking = await fetchRealEstateReactionRankingWithFallback({ type: 'region', windowMinutes: 10080, limit: 10 });
    dashboardReactionRanking.value = ranking;
    dashboardReactionItems.value = ranking.items.map(dashboardReactionItemFromApi);
    reactionRankingLoadState.value = dashboardReactionItems.value.length ? 'live' : 'empty';
  } catch {
    dashboardReactionItems.value = [];
    dashboardReactionRanking.value = null;
    reactionRankingLoadState.value = 'error';
  }
};
const refreshDashboardContent = async () => {
  dashboardContentLoadState.value = 'loading';
  dashboardContentItems.value = [];
  try {
    const groupedItems = await Promise.all(
      dashboardContentFeeds.map(async (feed) => {
        const contentItems = await fetchRealEstateNewsroom({ feed, page: 1, pageSize: dashboardContentPageSize });
        return buildNewsroomFeedItems(contentItems)
          .filter((item) => item.category === feed)
          .slice(0, 5);
      })
    );
    const mappedItems = ensureNewsroomCategoryCoverage(groupedItems.flat());
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

const refreshAll = async () => {
  if (isRefreshing.value) return;
  isRefreshing.value = true;
  try {
    await Promise.allSettled([
      refreshDashboardReactions(),
      refreshMarketSummary(),
      refreshDashboardContent()
    ]);
    lastRefreshedAt.value = new Date();
  } finally {
    isRefreshing.value = false;
  }
};

onMounted(() => {
  startTimer();
  void refreshAll();
});
onUnmounted(() => clearInterval(autoSlideTimer));

const refreshButtonLabel = computed(() => (isRefreshing.value ? '불러오는 중…' : '실시간 데이터 불러오기'));
const lastRefreshedLabel = computed(() => {
  if (isRefreshing.value) return '갱신 중';
  if (!lastRefreshedAt.value) return '갱신 전';
  return `${lastRefreshedAt.value.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })} 기준`;
});

const formatPct = (value: number | null) => value === null ? '최신' : `${value > 0 ? '+' : ''}${value}%`;
const ratioPct = (value: number) => `${Math.round(value * 100)}%`;
const coverageStatusLabel = (status: string) => {
  if (status === 'source_skewed') return '출처 편중';
  if (status === 'partial') return '부분 반영';
  if (status === 'low_sample') return '표본 부족';
  if (status === 'ok') return '수집 확인';
  if (status === 'empty' || status === 'insufficient' || status === 'mock') return '수집 전';
  if (status === 'stale') return '갱신 지연';
  return status || '확인 필요';
};
const dashboardReactionEmptyText = computed(() => {
  if (reactionRankingLoadState.value === 'loading') return '지역 반응 TOP10을 불러오는 중입니다.';
  if (reactionRankingLoadState.value === 'error') return '지역 반응 데이터를 불러오지 못했습니다. 크롤링/반응 집계 배치 상태 확인이 필요합니다.';
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
  if (dashboardContentLoadState.value === 'error') return '콘텐츠를 불러오지 못했습니다. 출처와 기준 시각 확인이 필요합니다.';
  return '수집된 항목이 아직 없습니다. 수집 전/insufficient 상태입니다.';
});
const dashboardFeedEmptyText = (feedLabel: string) => {
  if (dashboardContentLoadState.value === 'loading') return '콘텐츠를 불러오는 중입니다.';
  if (dashboardContentLoadState.value === 'error') return '콘텐츠를 불러오지 못했습니다. 출처와 기준 시각 확인이 필요합니다.';
  if (feedLabel === '영상') {
    return '이번 갱신에서는 검증된 부동산 분석 채널 영상 후보가 없습니다. 매물 홍보형 영상은 제외했습니다.';
  }
  if (dashboardContentItems.value.length) {
    return `이번 갱신에서는 ${feedLabel} 유형이 아직 분리되지 않았습니다. 뉴스룸의 최근 이슈 후보에서 확인할 수 있습니다.`;
  }
  return dashboardContentEmptyText.value;
};
const hideBrokenIcon = (event: Event) => {
  const image = event.target as HTMLImageElement;
  image.hidden = true;
  image.closest('.site-icon')?.classList.remove('real-icon');
};
</script>

<template>
  <section class="dashboard-page">
    <section class="standalone-search" aria-label="대시보드 검색과 필터">
      <div class="dashboard-brand-hero" aria-label="너나사 YouBuyFirst 당신을 위한 부동산 인사이트">
        <h2><em>너나사</em> YouBuyFirst</h2>
        <p class="dashboard-brand-tagline">당신을 위한 부동산 인사이트, <strong>너나사</strong></p>
      </div>
      <div class="search-line">
        <div class="search-primary-row">
          <button class="dashboard-search-control" type="button" disabled>
            <span class="search-icon" aria-hidden="true"></span>
            <strong>/</strong>
            <span>지역이나 단지 검색</span>
          </button>
        </div>
      </div>
    </section>

    <section class="dashboard-main-layout">
      <div class="dashboard-content-flow">
        <section class="insight-grid">
          <article class="daily-briefing-card" aria-labelledby="daily-briefing-title">
            <div class="daily-briefing-header">
              <div>
                <p class="label">AI briefing</p>
                <h3 id="daily-briefing-title">
                  <span class="briefing-title-accent">Today</span> 3줄 브리핑
                </h3>
              </div>
              <RouterLink class="daily-briefing-cta" to="/newsroom">자세한 분석 보러가기 →</RouterLink>
            </div>

            <div class="daily-briefing-body" aria-label="오늘의 핵심 부동산 상황 요약">
              <ol class="daily-briefing-list">
                <li
                  v-for="item in dailyBriefingItems"
                  :key="item.id"
                  :class="['daily-briefing-item', item.tone]"
                >
                  <strong>{{ item.text }}</strong>
                </li>
              </ol>
            </div>

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

        <section class="news-macro-grid">
          <article class="panel news-feed content-feed-card live-feed-card" aria-labelledby="news-title">
            <div class="panel-header">
              <div class="feed-title-wrap">
                <span class="feed-title-dot" aria-hidden="true"></span>
                <h3 id="news-title" class="feed-panel-title">실시간 뉴스</h3>
              </div>
              <div class="section-actions">
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'news' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <p v-if="!dashboardNewsItems.length" class="newsroom-empty-state">{{ dashboardFeedEmptyText('뉴스') }}</p>
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
              <div class="feed-title-wrap">
                <span class="feed-title-dot" aria-hidden="true"></span>
                <h3 id="analyst-title" class="feed-panel-title">정책·통계 리포트</h3>
              </div>
              <div class="section-actions">
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'reports' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <p v-if="!dashboardReportItems.length" class="newsroom-empty-state">{{ dashboardFeedEmptyText('리포트') }}</p>
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
              <div class="feed-title-wrap">
                <span class="feed-title-dot" aria-hidden="true"></span>
                <h3 id="external-video-title" class="feed-panel-title">부동산 영상</h3>
              </div>
              <div class="section-actions">
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'videos' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <p v-if="!dashboardVideoItems.length" class="newsroom-empty-state">{{ dashboardFeedEmptyText('영상') }}</p>
              <a
                v-for="video in dashboardVideoItems"
                :key="video.id"
                class="feed-row"
                :href="video.url"
                target="_blank"
                rel="noreferrer noopener"
              >
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
              <div class="feed-title-wrap">
                <span class="feed-title-dot" aria-hidden="true"></span>
                <h3 id="external-link-title" class="feed-panel-title">블로그·커뮤니티</h3>
              </div>
              <div class="section-actions">
                <RouterLink class="detail-link" :to="{ path: '/newsroom', query: { feed: 'links' } }">자세히 보기 →</RouterLink>
              </div>
            </div>
            <div class="feed-list">
              <p v-if="!dashboardLinkItems.length" class="newsroom-empty-state">{{ dashboardFeedEmptyText('블로그·커뮤니티') }}</p>
              <a
                v-for="link in dashboardLinkItems"
                :key="link.id"
                class="feed-row"
                :href="link.url"
                target="_blank"
                rel="noreferrer noopener"
              >
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

      </div>

      <aside class="side-drawer" aria-label="오른쪽 빠른 패널">
        <section class="drawer-tab-screen drawer-reaction-screen">
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
        </section>
      </aside>
    </section>
  </section>
</template>
