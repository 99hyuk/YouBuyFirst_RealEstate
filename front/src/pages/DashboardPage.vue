<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  buildNewsroomFeedItems,
  ensureNewsroomCategoryCoverage,
  fetchRealEstateNewsroom,
  type NewsroomCategory,
  type NewsroomFeedItem
} from '../lib/realestate-content';
import {
  subscribeRealEstateBatchUpdates,
  type BatchUpdateSubscription
} from '../lib/realestate-batch-updates';
import {
  fetchLatestRealEstateDailyBriefing,
  type RealEstateDailyBriefing
} from '../lib/realestate-daily-briefing';
import {
  buildRegionalMomentumRows,
  type DashboardRegionalMomentumRow
} from '../lib/realestate-dashboard';
import { fetchRealEstateMapLayer } from '../lib/realestate-map';
import {
  fetchRealEstateRegionalReport,
  type RealEstateRegionalReport
} from '../lib/realestate-regional-reports';
import {
  buildMarketSummaryIndicators,
  fetchRealEstateMarketSummary,
  realEstateMarketIndicatorFallbacks,
  type RealEstateMarketIndicatorCard
} from '../lib/realestate-market-facts';
import {
  fetchRealEstateTargetSuggestions,
  MIN_TARGET_SEARCH_LENGTH,
  normalizeTargetSearchText,
  TARGET_SEARCH_LIMIT,
  type RealEstateTargetSearchResult
} from '../lib/realestate-target-search';
import { sourceIconUrl } from '../lib/source-icons';

const router = useRouter();
const marketIndicators = ref<RealEstateMarketIndicatorCard[]>([]);
const dashboardContentItems = ref<NewsroomFeedItem[]>([]);
const dashboardContentLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const latestDailyBriefing = ref<RealEstateDailyBriefing | null>(null);
const dailyBriefingLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const weeklyPriceRows = ref<DashboardRegionalMomentumRow[]>([]);
const weeklyPriceRiserLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const dashboardContentFeeds: NewsroomCategory[] = ['news', 'reports', 'videos', 'links'];
const dashboardContentPageSize = 100;
const isRefreshing = ref(false);
const lastRefreshedAt = ref<Date | null>(null);
type ReportPoint = { id: string; text: string };
type TopWeeklyRegionItem = {
  targetId: string;
  rank: number;
  name: string;
  changePct: number;
  changeLabel: string;
  reportPath: string;
  expectationPoints: ReportPoint[];
  concernPoints: ReportPoint[];
};
const topWeeklyRegionItems = ref<TopWeeklyRegionItem[]>([]);
const topWeeklyRegionLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const searchQuery = ref('');
const searchSuggestions = ref<RealEstateTargetSearchResult[]>([]);
const searchLoadState = ref<'idle' | 'loading' | 'live' | 'empty' | 'error'>('idle');
const isSearchFocused = ref(false);
type DailyBriefingItem = {
  id: string;
  text: string;
  role: string;
};
const headlineRoles = ['핵심 신호', '지역 흐름', '시장 변수'];

const topWeeklyPriceGainer = computed(() =>
  weeklyPriceRows.value.find((row) => row.changePct > 0) ?? null
);
const topWeeklyPriceDecliner = computed(() =>
  [...weeklyPriceRows.value].reverse().find((row) => row.changePct < 0) ?? null
);
const parentTargetIdByRegionCodePrefix: Record<string, string> = {
  '11': 'region-seoul',
  '21': 'region-busan',
  '22': 'region-daegu',
  '23': 'region-incheon',
  '24': 'region-gwangju',
  '25': 'region-daejeon',
  '26': 'region-busan',
  '27': 'region-daegu',
  '28': 'region-incheon',
  '29': 'region-gwangju',
  '30': 'region-daejeon',
  '31': 'region-gyeonggi',
  '32': 'region-gangwon',
  '33': 'region-chungbuk',
  '34': 'region-chungnam',
  '35': 'region-jeonbuk',
  '36': 'region-sejong',
  '37': 'region-gyeongbuk',
  '38': 'region-gyeongnam',
  '39': 'region-jeju',
  '41': 'region-gyeonggi',
  '43': 'region-chungbuk',
  '44': 'region-chungnam',
  '46': 'region-jeonnam',
  '47': 'region-gyeongbuk',
  '48': 'region-gyeongnam',
  '50': 'region-jeju',
  '51': 'region-gangwon',
  '52': 'region-jeonbuk'
};
const inferParentTargetId = (row: DashboardRegionalMomentumRow) => {
  const regionPrefix = row.regionCode.slice(0, 2);
  const parentFromRegionCode = parentTargetIdByRegionCodePrefix[regionPrefix];
  if (parentFromRegionCode) return parentFromRegionCode;

  const [type, sido] = row.targetId.split('-');
  if (type === 'region' && sido) return `region-${sido}`;

  return 'region-seoul';
};
const targetReportPath = (row: DashboardRegionalMomentumRow) => {
  const parentTargetId = row.parentTargetId ?? inferParentTargetId(row);
  const selectedRegionCode = row.geometryId ?? row.regionCode;
  const params = new URLSearchParams({
    selectedTargetId: row.targetId,
    selectedRegionCode,
    period: 'week'
  });

  return `/realestate/map/${encodeURIComponent(parentTargetId)}?${params.toString()}`;
};
const dailyBriefingItems = computed<DailyBriefingItem[]>(() => {
  if (latestDailyBriefing.value?.summaryHeadlines.length === 3) {
    return latestDailyBriefing.value.summaryHeadlines.map((headline, index) => ({
      id: `daily-briefing-${index + 1}`,
      text: headline,
      role: headlineRoles[index] ?? '핵심'
    }));
  }
  if (dailyBriefingLoadState.value === 'loading') {
    return [{ id: 'daily-briefing-loading', text: '브리핑 생성 대기', role: '대기' }];
  }
  if (dailyBriefingLoadState.value === 'error') {
    return [{ id: 'daily-briefing-error', text: '브리핑 갱신 확인 필요', role: '확인 필요' }];
  }
  return [{ id: 'daily-briefing-empty', text: '브리핑 생성 대기', role: '대기' }];
});

const currentSlide = ref(0);
const isPaused = ref(false);
const totalSlides = computed(() => Math.max(topWeeklyRegionItems.value.length, 1));
let autoSlideTimer: ReturnType<typeof setInterval> | undefined;
let searchRequestToken = 0;
let searchSelectionTargetId: string | null = null;
let batchUpdateSubscription: BatchUpdateSubscription | null = null;

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
const refreshWeeklyPriceRiser = async () => {
  weeklyPriceRiserLoadState.value = 'loading';
  topWeeklyRegionLoadState.value = 'loading';
  weeklyPriceRows.value = [];
  topWeeklyRegionItems.value = [];
  currentSlide.value = 0;
  try {
    const layer = await fetchRealEstateMapLayer({ layerType: 'sigungu' });
    weeklyPriceRows.value = buildRegionalMomentumRows(layer, 'week', Number.MAX_SAFE_INTEGER);
    weeklyPriceRiserLoadState.value = weeklyPriceRows.value.length ? 'live' : 'empty';
    await refreshTopWeeklyRegionItems(weeklyPriceRows.value);
  } catch {
    weeklyPriceRows.value = [];
    topWeeklyRegionItems.value = [];
    weeklyPriceRiserLoadState.value = 'error';
    topWeeklyRegionLoadState.value = 'error';
  }
};

const refreshTopWeeklyRegionItems = async (rows: DashboardRegionalMomentumRow[]) => {
  const topRows = rows.filter((row) => row.changePct > 0).slice(0, 5);
  if (!topRows.length) {
    topWeeklyRegionItems.value = [];
    topWeeklyRegionLoadState.value = 'empty';
    return;
  }

  const reports = await Promise.all(
    topRows.map((row) => fetchRealEstateRegionalReport(row.targetId).catch(() => null))
  );

  topWeeklyRegionItems.value = topRows.map((row, index) =>
    buildTopWeeklyRegionItem(row, reports[index], index)
  );
  topWeeklyRegionLoadState.value = topWeeklyRegionItems.value.length ? 'live' : 'empty';
};

const buildTopWeeklyRegionItem = (
  row: DashboardRegionalMomentumRow,
  report: RealEstateRegionalReport | null,
  index: number
): TopWeeklyRegionItem => {
  const pointPair = reportPointPair(report);
  return {
    targetId: row.targetId,
    rank: index + 1,
    name: row.name,
    changePct: row.changePct,
    changeLabel: formatSignedPct(row.changePct),
    reportPath: targetReportPath(row),
    expectationPoints: pointPair.expectation,
    concernPoints: pointPair.concern
  };
};

const reportPointPair = (
  report: RealEstateRegionalReport | null
): { expectation: ReportPoint[]; concern: ReportPoint[] } => {
  if (!report) {
    return {
      expectation: buildReportPoints(['주간 상승률 확인 지역']),
      concern: buildReportPoints(['최신 리포트 적재 대기'])
    };
  }

  return {
    expectation: buildReportPoints(report.expectationPoints.length ? report.expectationPoints : [report.headline]),
    concern: buildReportPoints(report.concernPoints.length ? report.concernPoints : [report.summary])
  };
};

const buildReportPoints = (points: string[]): ReportPoint[] =>
  points
    .map(normalizeReportPoint)
    .filter((point, index, list) => point.length > 0 && list.indexOf(point) === index)
    .slice(0, 3)
    .map((text, index) => ({ id: `point-${index + 1}-${text.slice(0, 12)}`, text }));

const normalizeReportPoint = (point: string) =>
  point
    .replace(/\*\*/g, '')
    .replace(/^(기대|우려)\s*[:：-]\s*/g, '')
    .replace(/\s+/g, ' ')
    .trim();
const refreshDashboardContent = async () => {
  dashboardContentLoadState.value = 'loading';
  dashboardContentItems.value = [];
  const groupedItems = await Promise.all(
    dashboardContentFeeds.map(async (feed) => {
      try {
        const contentItems = await fetchRealEstateNewsroom({ feed, page: 1, pageSize: dashboardContentPageSize });
        return {
          failed: false,
          items: buildNewsroomFeedItems(contentItems)
            .filter((item) => item.category === feed)
            .slice(0, 5)
        };
      } catch {
        return {
          failed: true,
          items: [] as NewsroomFeedItem[]
        };
      }
    })
  );
  const mappedItems = ensureNewsroomCategoryCoverage(groupedItems.flatMap((group) => group.items));
  const failedFeedCount = groupedItems.filter((group) => group.failed).length;
  dashboardContentItems.value = mappedItems;
  dashboardContentLoadState.value = mappedItems.length
    ? 'live'
    : failedFeedCount === dashboardContentFeeds.length
      ? 'error'
      : 'empty';
};
const refreshDailyBriefing = async () => {
  dailyBriefingLoadState.value = 'loading';
  try {
    const briefing = await fetchLatestRealEstateDailyBriefing();
    latestDailyBriefing.value = briefing;
    dailyBriefingLoadState.value = briefing?.summaryHeadlines.length === 3 ? 'live' : 'empty';
  } catch {
    latestDailyBriefing.value = null;
    dailyBriefingLoadState.value = 'error';
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
const openTopWeeklyRegionReport = (path: string, event: MouseEvent) => {
  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  void router.push(path);
};
const isSearchReady = computed(() => normalizeTargetSearchText(searchQuery.value).length >= MIN_TARGET_SEARCH_LENGTH);
const showSearchSuggestions = computed(() =>
  isSearchFocused.value
  && isSearchReady.value
  && ['loading', 'live', 'empty', 'error'].includes(searchLoadState.value)
);
const clearDashboardSearch = () => {
  searchQuery.value = '';
  searchSuggestions.value = [];
  searchLoadState.value = 'idle';
};
const targetTypeLabel = (item: RealEstateTargetSearchResult) => {
  if (item.targetType === 'complex') return '실거래 단지';
  if (item.targetType === 'living_area') return '생활권';
  if (item.regionLevel === 'sido') return '광역';
  if (item.regionLevel === 'eupmyeondong') return '실거래 지역';
  return '지역 분석';
};
const targetSearchMeta = (item: RealEstateTargetSearchResult) => {
  const code = item.legalDongCode ?? item.regionCode;
  const status = item.dataStatus && item.dataStatus !== 'ok' ? item.dataStatus : '';
  return [code, status].filter(Boolean).join(' · ') || '근거 확인';
};
const transactionRegionCode = (item: RealEstateTargetSearchResult) =>
  (item.legalDongCode || item.regionCode || '').slice(0, 5);
const terminalRegionName = (displayName: string) => {
  const parts = displayName.trim().split(/\s+/).filter(Boolean);
  return parts.at(-1) ?? displayName;
};
const dashboardSearchRoute = (item: RealEstateTargetSearchResult) => {
  if (item.targetType === 'complex' || item.regionLevel === 'eupmyeondong') {
    const regionCode = transactionRegionCode(item);
    return {
      path: '/realestate/transactions',
      query: {
        ...(regionCode ? { region: regionCode } : {}),
        q: item.regionLevel === 'eupmyeondong' ? terminalRegionName(item.displayName) : item.displayName
      }
    };
  }

  const parentTargetId = item.regionLevel === 'sido'
    ? item.targetId
    : item.parentTargetId || item.targetId;
  const selectedRegionCode = item.regionCode || item.legalDongCode || item.targetId;
  return {
    path: `/realestate/map/${encodeURIComponent(parentTargetId)}`,
    query: {
      selectedTargetId: item.targetId,
      selectedRegionCode,
      period: 'week'
    }
  };
};
const openSearchSuggestion = (item: RealEstateTargetSearchResult) => {
  if (searchSelectionTargetId === item.targetId) return;

  searchSelectionTargetId = item.targetId;
  searchRequestToken += 1;
  isSearchFocused.value = false;
  searchSuggestions.value = [];
  searchLoadState.value = 'idle';
  void Promise.resolve(router.push(dashboardSearchRoute(item))).finally(() => {
    if (searchSelectionTargetId === item.targetId) {
      searchSelectionTargetId = null;
    }
  });
};
const submitDashboardSearch = () => {
  const first = searchSuggestions.value[0];
  if (first) {
    openSearchSuggestion(first);
  }
};
const requestDashboardTargetSearch = (value: string) => {
  const requestToken = ++searchRequestToken;
  searchSuggestions.value = [];
  if (normalizeTargetSearchText(value).length < MIN_TARGET_SEARCH_LENGTH) {
    searchLoadState.value = 'idle';
    return;
  }

  searchLoadState.value = 'loading';
  void fetchRealEstateTargetSuggestions(value, { limit: TARGET_SEARCH_LIMIT })
    .then((items) => {
      if (requestToken !== searchRequestToken) return;
      searchSuggestions.value = items;
      searchLoadState.value = items.length ? 'live' : 'empty';
    })
    .catch(() => {
      if (requestToken !== searchRequestToken) return;
      searchSuggestions.value = [];
      searchLoadState.value = 'error';
    });
};
const commitDashboardSearchInput = (event: Event) => {
  const value = (event.target as HTMLInputElement).value;
  if (searchQuery.value !== value) {
    searchQuery.value = value;
  }
};
const syncDashboardSearchInput = (event: Event) => {
  const value = (event.target as HTMLInputElement).value;
  if (searchQuery.value !== value) {
    searchQuery.value = value;
  }
};
const refreshAll = async () => {
  if (isRefreshing.value) return;
  isRefreshing.value = true;
  try {
    await Promise.allSettled([
      refreshDailyBriefing(),
      refreshWeeklyPriceRiser(),
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
  batchUpdateSubscription = subscribeRealEstateBatchUpdates((event) => {
    if (event.topic === 'newsroom') {
      void refreshDashboardContent();
    }
    if (event.topic === 'daily_briefing') {
      void refreshDailyBriefing();
    }
    if (event.topic === 'map-layers') {
      void refreshWeeklyPriceRiser();
    }
  });
});
onUnmounted(() => {
  clearInterval(autoSlideTimer);
  batchUpdateSubscription?.close();
  batchUpdateSubscription = null;
});

watch(searchQuery, requestDashboardTargetSearch);

const refreshButtonLabel = computed(() => (isRefreshing.value ? '불러오는 중…' : '실시간 데이터 불러오기'));
const lastRefreshedLabel = computed(() => {
  if (isRefreshing.value) return '갱신 중';
  if (!lastRefreshedAt.value) return '갱신 전';
  return `${lastRefreshedAt.value.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })} 기준`;
});

const formatSignedPct = (value: number) => {
  const rounded = Math.round(value * 100) / 100;
  const text = Number.isInteger(rounded)
    ? rounded.toLocaleString('ko-KR')
    : rounded.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
  return `${rounded > 0 ? '+' : ''}${text}%`;
};
const formatDateOnly = (value: string) => {
  const trimmed = value.trim();
  if (!trimmed) return '기준일 확인 필요';
  return trimmed.includes('T') ? trimmed.slice(0, 10) : trimmed;
};
const weeklyPriceReferenceLabel = computed(() => {
  const referenceRow = topWeeklyPriceGainer.value ?? topWeeklyPriceDecliner.value;
  return referenceRow ? `최근 1주 · ${formatDateOnly(referenceRow.asOf)} 기준` : '최근 1주 · 기준일 확인 필요';
});
const weeklyPriceRiserEmptyText = computed(() => {
  if (weeklyPriceRiserLoadState.value === 'loading') return '주간 가격 상승 세부지역을 불러오는 중입니다.';
  if (weeklyPriceRiserLoadState.value === 'error') return '주간 가격 데이터를 불러오지 못했습니다. 지도 layer 배치 상태 확인이 필요합니다.';
  return '주간 가격 상승·하락 세부지역이 아직 없습니다. 수집 전/insufficient 상태입니다.';
});
const dashboardReactionEmptyText = computed(() => {
  if (topWeeklyRegionLoadState.value === 'loading') return '주간 상승률 TOP5와 지역 리포트 키워드를 불러오는 중입니다.';
  if (topWeeklyRegionLoadState.value === 'error') return '주간 상승률 데이터를 불러오지 못했습니다. 지도 layer 배치 상태 확인이 필요합니다.';
  return '주간 상승률이 양수인 세부지역이 아직 없습니다. 수집 전/insufficient 상태입니다.';
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
        <form class="search-primary-row" role="search" @submit.prevent="submitDashboardSearch">
          <label class="dashboard-search-control">
            <span class="search-icon" aria-hidden="true"></span>
            <strong>/</strong>
            <input
              v-model="searchQuery"
              data-testid="dashboard-search-input"
              type="search"
              placeholder="지역·단지·법정동 검색"
              autocomplete="off"
              aria-label="지역이나 단지 검색"
              @focus="isSearchFocused = true"
              @input="syncDashboardSearchInput"
              @compositionend="commitDashboardSearchInput"
            />
            <button
              v-if="searchQuery"
              class="dashboard-search-clear"
              type="button"
              aria-label="검색어 지우기"
              @click="clearDashboardSearch"
            >
              ×
            </button>
          </label>
        </form>
        <div
          v-if="showSearchSuggestions"
          class="dashboard-search-suggestions"
          data-testid="dashboard-search-suggestions"
        >
          <button
            v-for="item in searchSuggestions"
            :key="item.targetId"
            class="dashboard-search-suggestion"
            type="button"
            :data-testid="`dashboard-search-result-${item.targetId}`"
            @pointerdown.prevent="openSearchSuggestion(item)"
            @mousedown.prevent
            @click.prevent="openSearchSuggestion(item)"
          >
            <span>{{ targetTypeLabel(item) }}</span>
            <strong>{{ item.displayName }}</strong>
            <em>{{ targetSearchMeta(item) }}</em>
          </button>
          <p v-if="searchLoadState === 'loading'" class="dashboard-search-state">검색 중</p>
          <p v-else-if="searchLoadState === 'empty'" class="dashboard-search-state">검색 결과 없음</p>
          <p v-else-if="searchLoadState === 'error'" class="dashboard-search-state">검색 확인 필요</p>
        </div>
      </div>
    </section>

    <section class="dashboard-main-layout">
      <div class="dashboard-content-flow">
        <section class="insight-grid">
          <article class="daily-briefing-card" aria-labelledby="daily-briefing-title">
            <div class="daily-briefing-header">
              <div>
                <p class="label">Daily briefing</p>
                <h3 id="daily-briefing-title">3줄 브리핑</h3>
              </div>
              <RouterLink class="daily-briefing-cta" to="/realestate/daily-briefing">
                <span>전체 브리핑</span>
                <strong>자세한 분석 보러가기</strong>
              </RouterLink>
            </div>

            <section class="daily-briefing-headline-grid daily-briefing-dashboard-headlines" aria-label="오늘의 핵심 부동산 상황 요약">
              <article
                v-for="(item, index) in dailyBriefingItems"
                :key="item.id"
                class="daily-briefing-headline-card"
              >
                <span class="daily-briefing-headline-index">{{ dailyBriefingItems.length === 3 ? String(index + 1).padStart(2, '0') : '—' }}</span>
                <div>
                  <small>{{ item.role }}</small>
                  <strong>{{ item.text }}</strong>
                </div>
              </article>
            </section>

          </article>

          <section class="mood-board region-bubble-section reaction-panel" aria-labelledby="mood-title">
            <div class="mood-header">
              <div>
                <p class="label">주간 상승률 TOP5</p>
                <h3 id="mood-title">지역·단지 반응 한눈에</h3>
              </div>
            </div>

            <div class="reaction-carousel" aria-label="주간 상승률 상위 지역 슬라이드">
              <p v-if="!topWeeklyRegionItems.length" class="newsroom-empty-state dashboard-reaction-empty">
                {{ dashboardReactionEmptyText }}
              </p>
              <div class="carousel-track-wrap">
                <div class="carousel-track" :style="{ transform: `translateX(-${currentSlide * 100}%)` }">
                  <a
                    v-for="item in topWeeklyRegionItems"
                    :key="item.targetId"
                    :href="item.reportPath"
                    class="reaction-carousel-card"
                    data-tone="positive"
                    :aria-label="`${item.name} 지역 분석 열기`"
                    @click="openTopWeeklyRegionReport(item.reportPath, $event)"
                  >
                    <div class="carousel-card-header">
                      <div class="carousel-card-title">
                        <strong class="carousel-region-name">{{ item.name }}</strong>
                      </div>
                      <div class="carousel-change-badge" aria-label="주간 상승률">
                        <span>주간</span>
                        <em>{{ item.changeLabel }}</em>
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
                        <ul class="report-point-list report-point-list-positive">
                          <li
                            v-for="point in item.expectationPoints"
                            :key="point.id"
                            class="report-point-item"
                          >{{ point.text }}</li>
                        </ul>
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
                        <ul class="report-point-list report-point-list-negative">
                          <li
                            v-for="point in item.concernPoints"
                            :key="point.id"
                            class="report-point-item"
                          >{{ point.text }}</li>
                        </ul>
                      </div>
                    </div>

                  </a>
                </div>
              </div>
            </div>

            <div v-if="topWeeklyRegionItems.length" class="carousel-controls">
              <button class="carousel-btn" type="button" @click="prevSlide" aria-label="이전 지역">
                <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3 L5 8 L10 13"/></svg>
              </button>
              <div class="carousel-dots" role="tablist" aria-label="슬라이드 선택">
                <button
                  v-for="(item, i) in topWeeklyRegionItems"
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
                  <img :src="sourceIconUrl(news.iconDomain, news.tone)" alt="" loading="lazy" @error="hideBrokenIcon" />
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
                  <img :src="sourceIconUrl(report.iconDomain, report.tone)" alt="" loading="lazy" @error="hideBrokenIcon" />
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
                  <img :src="sourceIconUrl(video.iconDomain, video.tone)" alt="" loading="lazy" @error="hideBrokenIcon" />
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
                  <img :src="sourceIconUrl(link.iconDomain, link.tone)" alt="" loading="lazy" @error="hideBrokenIcon" />
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
          <div class="hot-region-shell">
            <div v-if="topWeeklyPriceGainer || topWeeklyPriceDecliner" class="drawer-card hot-region-panel" aria-labelledby="hot-region-title">
              <p id="hot-region-title" class="hot-region-title-band">라이브 패널 · 주간 가격 흐름</p>
              <div class="hot-region-movement-grid">
                <RouterLink
                  v-if="topWeeklyPriceGainer"
                  class="hot-region-movement hot-region-movement-up"
                  :to="targetReportPath(topWeeklyPriceGainer)"
                  :aria-label="`${topWeeklyPriceGainer.name} 지역 분석 보고서 보기`"
                >
                  <span>이번주 가장 많이 상승한 지역</span>
                  <h3>{{ topWeeklyPriceGainer.name }}</h3>
                  <strong>{{ formatSignedPct(topWeeklyPriceGainer.changePct) }}</strong>
                </RouterLink>
                <div v-else class="hot-region-movement hot-region-movement-up hot-region-movement-empty" aria-disabled="true">
                  <span>이번주 가장 많이 상승한 지역</span>
                  <h3>확인 필요</h3>
                  <strong>수집 전</strong>
                </div>
                <div class="hot-region-divider" aria-hidden="true"></div>
                <RouterLink
                  v-if="topWeeklyPriceDecliner"
                  class="hot-region-movement hot-region-movement-down"
                  :to="targetReportPath(topWeeklyPriceDecliner)"
                  :aria-label="`${topWeeklyPriceDecliner.name} 지역 분석 보고서 보기`"
                >
                  <span>이번주 가장 많이 하락한 지역</span>
                  <h3>{{ topWeeklyPriceDecliner.name }}</h3>
                  <strong>{{ formatSignedPct(topWeeklyPriceDecliner.changePct) }}</strong>
                </RouterLink>
                <div v-else class="hot-region-movement hot-region-movement-down hot-region-movement-empty" aria-disabled="true">
                  <span>이번주 가장 많이 하락한 지역</span>
                  <h3>확인 필요</h3>
                  <strong>수집 전</strong>
                </div>
              </div>
              <span class="hot-region-reference">{{ weeklyPriceReferenceLabel }}</span>
            </div>
            <div v-else class="drawer-card hot-region-panel" aria-labelledby="hot-region-title-empty">
              <p id="hot-region-title-empty" class="hot-region-title-band">라이브 패널 · 주간 가격 흐름</p>
              <h3>수집 전</h3>
              <strong>insufficient</strong>
              <span>{{ weeklyPriceRiserEmptyText }}</span>
            </div>
          </div>
        </section>
      </aside>
    </section>
  </section>
</template>
