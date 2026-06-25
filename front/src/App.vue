<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import {
  fetchRealEstateReactionRankingWithFallback,
  type RealEstateReactionRankingItem
} from './lib/realestate-reactions';
import { currentAuthUser, loadCurrentUser, logout } from './lib/auth-session';
import {
  buildNewsroomFeedItems,
  fetchRealEstateNewsroom,
  type RealEstateContentItem,
  type NewsroomFeedItem
} from './lib/realestate-content';
import {
  currentMonth,
  fetchMarketDataSchedules,
  type MarketDataScheduleEvent
} from './lib/realestate-schedules';
import {
  fetchRealEstateMapLayer,
  type PeriodKey,
  type RealEstateMapLayerTarget
} from './lib/realestate-map';

const railItems = [
  { id: 'watch', label: '관심', shortcut: 'W' },
  { id: 'pulse', label: '반응', shortcut: 'P' },
  { id: 'recent', label: '최근 본', shortcut: 'R' },
  { id: 'live', label: '실시간', shortcut: 'L' }
];

const activeRailItem = ref('watch');
const railExpanded = ref(false);
const newsroomMenuDismissed = ref(false);
const shellRankingItems = ref<RealEstateReactionRankingItem[]>([]);
const shellReactionState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const shellTickerItems = ref<ShellTickerItem[]>([]);
const shellTickerState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const authState = ref<'checking' | 'guest' | 'authenticated'>('checking');
const route = useRoute();
const router = useRouter();
const authUser = currentAuthUser;
const activeRailLabel = computed(() => railItems.find((item) => item.id === activeRailItem.value)?.label ?? '관심');
const newsroomFeeds = [
  { label: '뉴스', feed: 'news' },
  { label: '리포트', feed: 'reports' },
  { label: '영상', feed: 'videos' },
  { label: '블로그·커뮤니티', feed: 'links' }
];
const activeNewsroomFeed = computed(() => {
  if (route.path !== '/newsroom') return '';
  const feed = route.query.feed;
  return Array.isArray(feed) ? feed[0] ?? '' : feed ?? '';
});

const loadShellSignals = async () => {
  shellReactionState.value = 'loading';
  try {
    const ranking = await fetchRealEstateReactionRankingWithFallback({ type: 'region', windowMinutes: 10080, limit: 6 });
    shellRankingItems.value = ranking.items;
    shellReactionState.value = ranking.items.length ? 'live' : 'empty';
  } catch {
    shellRankingItems.value = [];
    shellReactionState.value = 'error';
  }
};

type ShellTickerTone = 'news' | 'policy' | 'report' | 'schedule' | 'up' | 'down' | 'issue' | 'state';

type ShellTickerItem = {
  id: string;
  label: string;
  text: string;
  tone: ShellTickerTone;
  score: number;
};

const tickerContentPageSize = 12;
const tickerContentLimit = 4;
const tickerScheduleLimit = 2;
const tickerTotalLimit = 8;
const tickerMinimumContentImportance = 1;

const loadShellTicker = async () => {
  shellTickerState.value = 'loading';
  const [newsroomResult, schedulesResult, mapLayerResult] = await Promise.allSettled([
    fetchRealEstateNewsroom({ feed: 'all', page: 1, pageSize: tickerContentPageSize }),
    fetchMarketDataSchedules({ month: currentMonth() }),
    fetchRealEstateMapLayer({ layerType: 'sido' })
  ]);

  const items: ShellTickerItem[] = [];

  if (newsroomResult.status === 'fulfilled') {
    items.push(...buildContentTickerItems(newsroomResult.value));
  }
  if (schedulesResult.status === 'fulfilled') {
    items.push(...buildScheduleTickerItems(schedulesResult.value.scheduleEvents));
  }
  if (mapLayerResult.status === 'fulfilled') {
    items.push(...buildMovementTickerItems(mapLayerResult.value.targets));
  }

  shellTickerItems.value = rankShellTickerItems(items).slice(0, tickerTotalLimit);
  shellTickerState.value = shellTickerItems.value.length ? 'live' : 'empty';

  if (newsroomResult.status === 'rejected' && schedulesResult.status === 'rejected' && mapLayerResult.status === 'rejected') {
    shellTickerState.value = 'error';
  }
};

const loadAuthState = async () => {
  authState.value = 'checking';
  try {
    const user = await loadCurrentUser();
    authState.value = user ? 'authenticated' : 'guest';
  } catch {
    currentAuthUser.value = null;
    authState.value = 'guest';
  }
};

onMounted(() => {
  void loadShellSignals();
  void loadShellTicker();
  void loadAuthState();
});

const shellStatusLabel = computed(() => {
  if (shellReactionState.value === 'live') return '시장 흐름 반영';
  if (shellReactionState.value === 'loading') return '시장 흐름 확인 중';
  if (shellReactionState.value === 'empty') return '시장 데이터 확인 전';
  return '시장 흐름 확인 필요';
});

const liveTopics = computed(() => {
  if (!shellTickerItems.value.length) {
    return [
      {
        id: 'ticker-state',
        label: shellTickerState.value === 'loading' ? '확인' : '상태',
        tone: 'state' as ShellTickerTone,
        text: shellTickerState.value === 'error'
          ? '주요 뉴스·정책·시장 흐름 확인 필요'
          : '최신 뉴스·정책·상승·하락 후보 확인 중'
      }
    ];
  }

  return shellTickerItems.value;
});

const watchTargets = computed(() =>
  shellRankingItems.value.slice(0, 4).map((item) => {
    const concern = item.reactionDirectionRatio.concern;
    const expectation = item.reactionDirectionRatio.expectation;
    return {
      name: item.displayName,
      targetId: item.targetId,
      value: `${item.mentionCount.toLocaleString('ko-KR')}건`,
      change: formatDelta(item.mentionDeltaPct),
      tone: concern > expectation ? 'down' : expectation > concern ? 'up' : 'flat'
    };
  })
);

function formatDelta(value: number): string {
  return `${value > 0 ? '+' : ''}${value.toLocaleString('ko-KR', { maximumFractionDigits: 1 })}%`;
}

function issueLabel(item: RealEstateReactionRankingItem): string {
  const issue = item.issueMix[0]?.label;
  return issue ? `${issue} 쟁점` : '쟁점 확인 필요';
}

function buildContentTickerItems(contentItems: RealEstateContentItem[]): ShellTickerItem[] {
  const displayItems = buildNewsroomFeedItems(contentItems);
  const sourceById = new Map(contentItems.map((item) => [item.contentId, item]));

  const tickerItems: Array<ShellTickerItem | null> = displayItems.map((item) => {
    const source = sourceById.get(item.id);
    const timestamp = timestampValue(source?.publishedAt ?? source?.ingestedAt);
    const isPolicy = isPolicyContent(item, source);
    const isReport = item.category === 'reports';
    const importance = contentImportanceScore(item, source);

    if (importance < tickerMinimumContentImportance) return null;

    return {
      id: `content-${item.id}`,
      label: isPolicy ? '정책' : isReport ? '리포트' : '이슈',
      text: item.title,
      tone: isPolicy ? 'policy' : isReport ? 'report' : 'issue',
      score: timestamp + importance
    } satisfies ShellTickerItem;
  });

  return tickerItems
    .filter((item): item is ShellTickerItem => Boolean(item))
    .sort((left, right) => right.score - left.score)
    .slice(0, tickerContentLimit);
}

function buildScheduleTickerItems(events: MarketDataScheduleEvent[]): ShellTickerItem[] {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();

  return events
    .filter((event) => {
      const time = timestampValue(event.date);
      return time >= startOfToday && !event.stale;
    })
    .map((event) => ({
      id: `schedule-${event.id}`,
      label: '일정',
      text: `${formatScheduleDate(event.date)} ${event.title}`,
      tone: event.tone === 'policy' ? 'policy' : 'schedule',
      score: 3_000_000_000_000 - timestampValue(event.date)
    } satisfies ShellTickerItem))
    .sort((left, right) => right.score - left.score)
    .slice(0, tickerScheduleLimit);
}

function buildMovementTickerItems(targets: RealEstateMapLayerTarget[]): ShellTickerItem[] {
  const movements = targets
    .map((target) => {
      const period = latestUsablePeriod(target);
      return period ? { target, changePct: period.changePct, asOf: timestampValue(period.asOf) } : null;
    })
    .filter((item): item is { target: RealEstateMapLayerTarget; changePct: number; asOf: number } => Boolean(item));
  const highestGain = movements.filter((item) => item.changePct > 0).sort((left, right) => right.changePct - left.changePct)[0];
  const largestDrop = movements.filter((item) => item.changePct < 0).sort((left, right) => left.changePct - right.changePct)[0];

  const tickerItems: Array<ShellTickerItem | null> = [
    highestGain
      ? {
          id: `movement-up-${highestGain.target.targetId}`,
          label: '상승',
          text: `${highestGain.target.displayName} ${formatPct(highestGain.changePct)}`,
          tone: 'up',
          score: highestGain.asOf + Math.abs(highestGain.changePct) * 100
        } satisfies ShellTickerItem
      : null,
    largestDrop
      ? {
          id: `movement-down-${largestDrop.target.targetId}`,
          label: '하락',
          text: `${largestDrop.target.displayName} ${formatPct(largestDrop.changePct)}`,
          tone: 'down',
          score: largestDrop.asOf + Math.abs(largestDrop.changePct) * 100
        } satisfies ShellTickerItem
      : null
  ];

  return tickerItems.filter((item): item is ShellTickerItem => Boolean(item));
}

function rankShellTickerItems(items: ShellTickerItem[]): ShellTickerItem[] {
  const seen = new Set<string>();

  return items
    .sort((left, right) => right.score - left.score)
    .filter((item) => {
      const key = `${item.label}:${item.text}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

function isPolicyContent(item: NewsroomFeedItem, source?: RealEstateContentItem): boolean {
  const searchable = `${item.title} ${source?.snippet ?? ''} ${source?.metricLabel ?? ''}`.toLowerCase();
  return /정책|공급|청약|대출|금융|공시|규제|국토부|금융위|lh|sh|gh|ih|hug/.test(searchable);
}

function contentImportanceScore(item: NewsroomFeedItem, source?: RealEstateContentItem): number {
  const searchable = `${item.title} ${source?.snippet ?? ''} ${source?.metricLabel ?? ''}`.toLowerCase();
  const isReport = item.category === 'reports';
  const marketIssueMatches = searchable.match(/정책|공급|청약|대출|금리|금융|가계부채|세제|규제|공시|pf|미분양|전세|월세|실거래|거래량|가격|분양|주택시장|통계|지수|보고서|리포트|재건축|재개발/g)?.length ?? 0;
  const fillerPenalty = /이벤트|할인|제휴|프로모션|광고|브랜드|수상|채용|앱 출시|해외사업|온도차|실적/.test(searchable) ? 120 : 0;

  return (isPolicyContent(item, source) ? 90 : 0) + (isReport ? 70 : 0) + marketIssueMatches * 15 - fillerPenalty;
}

function latestUsablePeriod(target: RealEstateMapLayerTarget) {
  const periodOrder: PeriodKey[] = ['week', 'month', 'quarter', 'halfYear', 'year'];
  return periodOrder
    .map((period) => target.periods[period])
    .find((period) => period && period.dataStatus !== 'mock' && !period.stale) ?? null;
}

function timestampValue(value?: string | null): number {
  if (!value) return 0;
  const parsed = new Date(value).getTime();
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatScheduleDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat('ko-KR', { month: '2-digit', day: '2-digit' }).format(parsed);
}

function formatPct(value: number): string {
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
}

const openRail = (id: string) => {
  activeRailItem.value = id;
  railExpanded.value = true;
};

const dismissNewsroomMenu = () => {
  newsroomMenuDismissed.value = true;
  window.setTimeout(() => {
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
  }, 0);
};

const handleLogout = async () => {
  await logout();
  authState.value = 'guest';
  if (route.path === '/realestate/mypage') {
    void router.push('/auth/login');
  }
};
</script>

<template>
  <div :class="['app-shell', { 'edge-panel-open': railExpanded }]">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand-lockup">
          <RouterLink class="brand-home" data-testid="app-title" to="/dashboard">
            <h1>너나사 <span>YouBuyFirst</span></h1>
          </RouterLink>
        </div>

        <nav class="main-nav" aria-label="주요 화면">
          <RouterLink data-testid="nav-dashboard" to="/dashboard">대시보드</RouterLink>
          <span
            :class="['nav-menu-parent', { 'menu-dismissed': newsroomMenuDismissed }]"
            @pointerenter="newsroomMenuDismissed = false"
            @pointerleave="newsroomMenuDismissed = false"
            @focusin="newsroomMenuDismissed = false"
          >
            <RouterLink data-testid="nav-newsroom" to="/newsroom" @click="dismissNewsroomMenu">뉴스룸</RouterLink>
            <span class="nav-submenu" aria-label="뉴스룸 하위 피드">
              <RouterLink
                v-for="feed in newsroomFeeds"
                :key="feed.feed"
                :class="{ active: activeNewsroomFeed === feed.feed }"
                :to="{ path: '/newsroom', query: { feed: feed.feed } }"
                @click="dismissNewsroomMenu"
              >
                {{ feed.label }}
              </RouterLink>
            </span>
          </span>
          <RouterLink data-testid="nav-map" to="/realestate/map">지역 분석</RouterLink>
          <RouterLink data-testid="nav-transactions" to="/realestate/transactions">실거래</RouterLink>
          <RouterLink data-testid="nav-indicators" to="/indicators">주요 일정</RouterLink>
          <RouterLink data-testid="nav-watchlist" to="/realestate/mypage">마이페이지</RouterLink>
        </nav>

        <div class="topbar-status topbar-actions" aria-label="서비스 상태와 계정">
          <span>KST</span>
          <span v-if="authUser" class="auth-greeting" data-testid="auth-greeting">
            {{ authUser.displayName }}님 안녕하세요
          </span>
          <button
            v-if="authUser"
            class="login-button"
            data-testid="logout-button"
            type="button"
            @click="handleLogout"
          >
            로그아웃
          </button>
          <RouterLink
            v-else
            class="login-button"
            data-testid="auth-entry"
            to="/auth/login"
          >
            로그인
          </RouterLink>
        </div>
      </div>

      <div class="topbar-live-strip">
        <section class="live-strip" aria-label="상단 실시간 속보">
          <div class="live-strip-track">
            <div
              v-for="cycle in 4"
              :key="`ticker-cycle-${cycle}`"
              class="live-strip-sequence"
              :aria-hidden="cycle > 1"
            >
              <span
                v-for="topic in liveTopics"
                :key="`${cycle}-${topic.id}`"
                :class="['live-topic', `tone-${topic.tone}`]"
              >
                <strong>{{ topic.label }}</strong>
                {{ topic.text }}
              </span>
            </div>
          </div>
        </section>
      </div>
    </header>

    <main class="page-frame">
      <RouterView />
    </main>

    <footer class="site-footer" aria-labelledby="site-footer-title">
      <div class="site-footer-inner">
        <div class="site-footer-grid">
          <section class="site-footer-brand">
            <h2 id="site-footer-title">너나사<span>YouBuyFirst</span></h2>
            <p>
              실거래·전세 흐름, 지도 기반 지역 변화, 주요 일정, 뉴스·리포트 이슈를 함께 보는 부동산 인사이트 서비스입니다.
              실제 매수·매도·청약 판단을 대신하지 않습니다.
            </p>
            <a href="mailto:yh99cho1@gmail.com">문의 yh99cho1@gmail.com</a>
          </section>

          <section class="footer-column" aria-labelledby="footer-features-title">
            <h3 id="footer-features-title">서비스 특징</h3>
            <span>Daily briefing</span>
            <span>실거래·전세 흐름 확인</span>
            <span>전국·지역 지도 탐색</span>
            <span>주요 일정·뉴스·리포트 정리</span>
          </section>

          <section class="footer-column footer-legal" aria-labelledby="footer-notice-title">
            <h3 id="footer-notice-title">유의사항</h3>
            <p>
              가격, 거래, 일정 정보는 공개 지연이나 신고 보정으로 달라질 수 있습니다.
              본 사이트는 시장 정보를 정리해 보여주는 관찰용 서비스입니다.
            </p>
            <p>
              매수·매도·청약·대출 행동을 권유하지 않으며, 지도 색상과 요약은 확정 전망이 아닙니다.
            </p>
          </section>

          <section class="footer-column" aria-labelledby="footer-source-title">
            <h3 id="footer-source-title">데이터 출처</h3>
            <span>국토교통부 공공데이터</span>
            <span>한국부동산원 통계</span>
            <span>국토교통부 실거래가 공개시스템</span>
            <span>한국은행·청약Home 등 공식 출처</span>
          </section>
        </div>

        <div class="site-footer-bottom">
          <span>© 2026 YouBuyFirst · 모든 부동산 지표는 참고용이며 실시간이 아닐 수 있습니다.</span>
          <span>관찰형 부동산 인사이트 · 2026.06</span>
        </div>
      </div>
    </footer>

    <aside :class="['edge-panel', { open: railExpanded }]" aria-label="오른쪽 확장 패널">
      <section class="edge-panel-screen">
        <div class="edge-panel-header">
          <div>
            <p class="label">quick panel</p>
            <h2>{{ activeRailLabel }}</h2>
          </div>
          <span class="panel-mini-badge">{{ shellStatusLabel }}</span>
        </div>

        <div v-if="activeRailItem === 'watch'" class="edge-watch-list">
          <div v-if="!watchTargets.length" class="edge-empty-state">
            <strong>저장 지역 준비 중</strong>
            <p>{{ shellStatusLabel }} · 저장 기능이 연결되면 이 영역에 저장 지역이 표시됩니다.</p>
          </div>
          <article v-for="target in watchTargets" :key="target.targetId" class="edge-watch-row">
            <span class="edge-initial">{{ target.name.slice(0, 1) }}</span>
            <div>
              <strong>{{ target.name }}</strong>
              <p>{{ target.targetId }}</p>
            </div>
            <div class="edge-price">
              <strong>{{ target.value }}</strong>
              <em :class="target.tone">{{ target.change }}</em>
            </div>
          </article>
        </div>

        <div v-else-if="activeRailItem === 'pulse'" class="edge-live-list">
          <div v-if="!shellRankingItems.length" class="edge-empty-state">
            <strong>시장 데이터 확인 전</strong>
            <p>{{ shellStatusLabel }} · 시장 데이터가 갱신되면 주요 변화가 표시됩니다.</p>
          </div>
          <article v-for="item in shellRankingItems.slice(0, 3)" :key="item.targetId">
            <span>{{ issueLabel(item) }}</span>
            <strong>{{ item.displayName }}</strong>
            <em :class="item.reactionDirectionRatio.concern > item.reactionDirectionRatio.expectation ? 'down' : 'up'">
              {{ formatDelta(item.mentionDeltaPct) }}
            </em>
          </article>
        </div>

        <div v-else class="edge-empty-state">
          <strong>{{ activeRailLabel }} 패널</strong>
          <p>{{ shellStatusLabel }} · 해당 패널의 실제 API가 열리면 항목을 표시합니다.</p>
        </div>
      </section>
    </aside>

    <aside class="edge-rail" aria-label="오른쪽 고정 탭">
      <button
        class="rail-expand"
        type="button"
        :aria-expanded="railExpanded"
        aria-label="오른쪽 패널 열고 닫기"
        @click="railExpanded = !railExpanded"
      >
        <span>{{ railExpanded ? '»' : '«' }}</span>
        <em>{{ railExpanded ? '닫기' : '열기' }}</em>
      </button>
      <button
        v-for="item in railItems"
        :key="item.id"
        type="button"
        :class="{ active: railExpanded && activeRailItem === item.id }"
        :aria-pressed="railExpanded && activeRailItem === item.id"
        @click="openRail(item.id)"
      >
        <span>{{ item.shortcut }}</span>
        <em>{{ item.label }}</em>
      </button>
      <button class="theme-toggle" type="button" aria-label="라이트 다크 모드 전환">
        <span>◐</span>
        <em>다크모드</em>
      </button>
    </aside>
  </div>
</template>
