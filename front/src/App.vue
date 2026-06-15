<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import {
  fetchRealEstateReactionRanking,
  type RealEstateReactionRankingItem
} from './lib/realestate-reactions';

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
const route = useRoute();
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
    const ranking = await fetchRealEstateReactionRanking({ type: 'region', windowMinutes: 1440, limit: 6 });
    shellRankingItems.value = ranking.items;
    shellReactionState.value = ranking.items.length ? 'live' : 'empty';
  } catch {
    shellRankingItems.value = [];
    shellReactionState.value = 'error';
  }
};

onMounted(() => {
  void loadShellSignals();
});

const shellStatusLabel = computed(() => {
  if (shellReactionState.value === 'live') return 'reaction API 반영';
  if (shellReactionState.value === 'loading') return 'reaction API 확인 중';
  if (shellReactionState.value === 'empty') return '수집 전/insufficient';
  return 'reaction API 오류';
});

const liveTopics = computed(() => {
  if (!shellRankingItems.value.length) {
    return [
      {
        label: shellReactionState.value === 'loading' ? '확인' : '상태',
        text: shellReactionState.value === 'error'
          ? '지역 반응 API 오류 · 크롤링/스냅샷 배치 확인 필요'
          : '지역 반응 TOP10 수집 전 · 크롤링/스냅샷 배치 대기'
      }
    ];
  }

  return shellRankingItems.value.slice(0, 4).map((item) => ({
    label: item.stale ? 'STALE' : 'LIVE',
    text: `${item.displayName} 언급 ${formatDelta(item.mentionDeltaPct)} · ${issueLabel(item)}`
  }));
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
</script>

<template>
  <div :class="['app-shell', { 'edge-panel-open': railExpanded }]">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand-lockup">
          <RouterLink class="brand-home" data-testid="app-title" to="/dashboard">
            <h1>너나사 <span>YouBuyFirst</span></h1>
          </RouterLink>
          <strong>BETA</strong>
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
          <RouterLink data-testid="nav-map" to="/realestate/map">지도</RouterLink>
          <RouterLink data-testid="nav-region-reactions" to="/realestate/reactions">지역 반응</RouterLink>
          <RouterLink data-testid="nav-indicators" to="/indicators">주요 지표</RouterLink>
          <RouterLink data-testid="nav-watchlist" to="/realestate/watchlist">관심 지역</RouterLink>
        </nav>

        <div class="topbar-status topbar-actions" aria-label="서비스 상태와 계정">
          <span>KST</span>
          <button class="login-button" type="button">로그인</button>
          <span>참고용</span>
        </div>
      </div>

      <div class="topbar-live-strip">
        <section class="live-strip" aria-label="상단 실시간 속보">
          <div class="live-strip-track">
            <span class="live-dot">반응</span>
            <span v-for="topic in liveTopics" :key="`${topic.label}-${topic.text}`" class="live-topic">
              <strong>{{ topic.label }}</strong>
              {{ topic.text }}
            </span>
            <span class="live-edge-test">{{ shellStatusLabel }}</span>
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
              커뮤니티 반응, 지역·단지 언급량, 실거래·전세·매물 상태, 에이전트 근거 로그를 함께 보는 부동산 관찰형 분석 서비스입니다.
              실제 매수·매도 지시나 개인화 부동산 자문을 제공하지 않습니다.
            </p>
            <a href="mailto:yh99cho1@gmail.com">문의 yh99cho1@gmail.com</a>
          </section>

          <section class="footer-column" aria-labelledby="footer-features-title">
            <h3 id="footer-features-title">서비스 특징</h3>
            <span>관심 지역·단지 반응 변화 브리핑</span>
            <span>정책·교통·전세·매물 이벤트 연결</span>
            <span>지역별 상승률과 유사 과거 상황</span>
            <span>AI 에이전트 근거 로그</span>
          </section>

          <section class="footer-column footer-legal" aria-labelledby="footer-notice-title">
            <h3 id="footer-notice-title">유의사항</h3>
            <p>
              모든 가격, 변동률, 반응 지표는 참고용 추정치이며 공공데이터 공개 시점과 다를 수 있습니다.
              본 사이트는 정보 제공과 모의 실험 목적으로만 운영됩니다.
            </p>
            <p>
              어떠한 부동산 매수·매도·청약·대출 행동도 권유하지 않으며, 이용으로 발생한 직·간접 손실에 대해 책임지지 않습니다.
            </p>
          </section>

          <section class="footer-column" aria-labelledby="footer-source-title">
            <h3 id="footer-source-title">데이터 출처</h3>
            <span>국토교통부 공공데이터</span>
            <span>한국부동산원 통계</span>
            <span>공개 커뮤니티·뉴스·컬럼</span>
            <span>비공개·유료 데이터 미사용</span>
          </section>
        </div>

        <div class="site-footer-bottom">
          <span>© 2026 YouBuyFirst · 모든 부동산 지표는 참고용이며 실시간이 아닐 수 있습니다.</span>
          <span>BETA · 관찰형 부동산 인사이트 · 2026.06</span>
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
            <strong>관심 후보 수집 전</strong>
            <p>{{ shellStatusLabel }} · reaction ranking이 쌓이면 이 영역에 TOP 후보가 표시됩니다.</p>
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
            <strong>반응 수집 전</strong>
            <p>{{ shellStatusLabel }} · 커뮤니티 snapshot이 생성되면 쟁점 변화가 표시됩니다.</p>
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
