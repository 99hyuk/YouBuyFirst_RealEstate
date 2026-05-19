<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import dashboardSummary from '../fixtures/dashboard-summary.json';

type NewsroomFilter = 'all' | 'news' | 'reports' | 'videos' | 'links';
type FeedTone = 'news' | 'report' | 'video' | 'link';

type NewsroomItem = {
  id: string;
  category: Exclude<NewsroomFilter, 'all'>;
  tone: FeedTone;
  title: string;
  source: string;
  iconDomain: string;
  iconClass: string;
  url: string;
  meta: string;
  statusLabel: string;
  rankLabel?: string;
};

const filterIds: NewsroomFilter[] = ['all', 'news', 'reports', 'videos', 'links'];
const filterLabels: Record<NewsroomFilter, string> = {
  all: '종합',
  news: '뉴스',
  reports: '리포트',
  videos: '영상',
  links: '블로그 및 커뮤니티'
};

const pageSize = 15;

const directIconUrls: Record<string, string> = {
  'blog.naver.com': 'https://ssl.pstatic.net/static/blog/icon/favicon.ico',
  'finance.naver.com': 'https://ssl.pstatic.net/imgstock/favi/favicon-96x96.png'
};

const faviconUrl = (domain: string) => directIconUrls[domain] ?? `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;

const hideBrokenIcon = (event: Event) => {
  const image = event.target as HTMLImageElement;
  image.hidden = true;
  image.closest('.site-icon')?.classList.remove('real-icon');
};

const newsIconClass = (tag: string) => {
  const map: Record<string, string> = {
    macro: 'news-macro',
    stock: 'news-stock',
    index: 'news-index',
    community: 'community',
    research: 'news-research',
    strategy: 'news-research',
    disclosure: 'news-stock'
  };

  return map[tag] ?? 'news';
};

const externalIconClass = (item: { type: string; iconDomain?: string }) => {
  if (item.type === 'youtube') return 'youtube';
  if (item.iconDomain === 'blog.naver.com') return 'naver-blog';
  if (item.iconDomain === 'finance.naver.com') return 'naver';
  if (item.iconDomain === 'www.tossinvest.com') return 'toss';
  return item.type;
};

const feedItems: NewsroomItem[] = [
  ...dashboardSummary.liveNews.map((item) => ({
    id: `news-${item.title}`,
    category: 'news' as const,
    tone: 'news' as const,
    title: item.title,
    source: item.source,
    iconDomain: item.iconDomain,
    iconClass: newsIconClass(item.tag),
    url: item.url,
    meta: item.timeLabel,
    statusLabel: item.dataStatus
  })),
  ...dashboardSummary.analystReports.map((item) => ({
    id: `report-${item.title}`,
    category: 'reports' as const,
    tone: 'report' as const,
    title: item.title,
    source: item.source,
    iconDomain: item.iconDomain,
    iconClass: newsIconClass(item.tag),
    url: item.url,
    meta: item.timeLabel,
    statusLabel: item.dataStatus
  })),
  ...dashboardSummary.externalContent.videos.map((item, index) => ({
    id: `video-${item.url}`,
    category: 'videos' as const,
    tone: 'video' as const,
    title: item.title,
    source: item.source,
    iconDomain: item.iconDomain,
    iconClass: externalIconClass(item),
    url: item.url,
    meta: `${item.publishedLabel} · ${item.engagementLabel}`,
    statusLabel: item.dataStatus,
    rankLabel: `${index + 1}위`
  })),
  ...dashboardSummary.externalContent.links.map((item, index) => ({
    id: `link-${item.url}`,
    category: 'links' as const,
    tone: 'link' as const,
    title: item.title,
    source: item.source,
    iconDomain: item.iconDomain,
    iconClass: externalIconClass(item),
    url: item.url,
    meta: `${item.publishedLabel} · ${item.engagementLabel}`,
    statusLabel: item.dataStatus,
    rankLabel: `${index + 1}위`
  })),
  ...[
    {
      id: 'news-extra-dollar-yield',
      category: 'news' as const,
      tone: 'news' as const,
      title: '달러 강세 구간, 환율 민감주 언급 확대',
      source: 'Google Finance',
      iconDomain: 'www.google.com',
      iconClass: 'news-macro',
      url: 'https://www.google.com/finance/',
      meta: '27분 전',
      statusLabel: 'mock'
    },
    {
      id: 'news-extra-ai-supply',
      category: 'news' as const,
      tone: 'news' as const,
      title: 'AI 서버 공급망 이슈로 전력·반도체 키워드 동반 증가',
      source: 'Yahoo Finance',
      iconDomain: 'finance.yahoo.com',
      iconClass: 'news-stock',
      url: 'https://finance.yahoo.com/topic/stock-market-news/',
      meta: '42분 전',
      statusLabel: 'mock'
    },
    {
      id: 'news-extra-market-close',
      category: 'news' as const,
      tone: 'news' as const,
      title: '장 마감 앞두고 코스닥 변동성 확대, 커뮤니티 체감 온도 상승',
      source: 'Investing.com',
      iconDomain: 'www.investing.com',
      iconClass: 'news-index',
      url: 'https://www.investing.com/news/stock-market-news',
      meta: '55분 전',
      statusLabel: 'mock'
    },
    {
      id: 'report-extra-bio',
      category: 'reports' as const,
      tone: 'report' as const,
      title: '바이오 업종 임상 일정과 수급 이벤트 점검',
      source: '증권사 데일리',
      iconDomain: 'finance.naver.com',
      iconClass: 'news-research',
      url: 'https://finance.naver.com/research/',
      meta: '4시간 전',
      statusLabel: 'mock'
    },
    {
      id: 'report-extra-secondary-battery',
      category: 'reports' as const,
      tone: 'report' as const,
      title: '2차전지 밸류체인 재고 부담과 반등 조건 정리',
      source: '네이버페이 증권 리서치',
      iconDomain: 'finance.naver.com',
      iconClass: 'news-research',
      url: 'https://finance.naver.com/research/',
      meta: '5시간 전',
      statusLabel: 'mock'
    },
    {
      id: 'report-extra-semiconductor-cycle',
      category: 'reports' as const,
      tone: 'report' as const,
      title: '반도체 사이클과 커뮤니티 관심도 괴리 점검',
      source: '증권사 테마 리포트',
      iconDomain: 'finance.naver.com',
      iconClass: 'news-research',
      url: 'https://finance.naver.com/research/',
      meta: '6시간 전',
      statusLabel: 'mock'
    },
    {
      id: 'video-extra-opening-bell',
      category: 'videos' as const,
      tone: 'video' as const,
      title: '개장 전 체크할 반도체·환율·금리 변수',
      source: '증권 방송 클립',
      iconDomain: 'www.youtube.com',
      iconClass: 'youtube',
      url: 'https://www.youtube.com/results?search_query=%EC%A6%9D%EA%B6%8C+%EC%A3%BC%EC%8B%9D',
      meta: '3일 전 · 조회 4.8만',
      statusLabel: 'mock',
      rankLabel: '6위'
    },
    {
      id: 'video-extra-earnings',
      category: 'videos' as const,
      tone: 'video' as const,
      title: '실적 발표 시즌, 커뮤니티가 먼저 반응한 업종은?',
      source: '투자 유튜브',
      iconDomain: 'www.youtube.com',
      iconClass: 'youtube',
      url: 'https://www.youtube.com/results?search_query=%EC%8B%A4%EC%A0%81+%EC%A3%BC%EC%8B%9D',
      meta: '4일 전 · 조회 3.6만',
      statusLabel: 'mock',
      rankLabel: '7위'
    },
    {
      id: 'video-extra-market-review',
      category: 'videos' as const,
      tone: 'video' as const,
      title: '오늘 시장에서 언급량이 가장 크게 바뀐 종목 리뷰',
      source: '마켓 리뷰',
      iconDomain: 'www.youtube.com',
      iconClass: 'youtube',
      url: 'https://www.youtube.com/results?search_query=%EC%A3%BC%EC%8B%9D+%EC%8B%9C%EC%9E%A5+%EB%A6%AC%EB%B7%B0',
      meta: '4일 전 · 조회 2.9만',
      statusLabel: 'mock',
      rankLabel: '8위'
    },
    {
      id: 'link-extra-fm-korea',
      category: 'links' as const,
      tone: 'link' as const,
      title: '반도체 장비주 토론 원문 묶음',
      source: '에펨코리아 주식',
      iconDomain: 'www.fmkorea.com',
      iconClass: 'community',
      url: 'https://www.fmkorea.com/',
      meta: '방금 갱신 · 댓글 188',
      statusLabel: 'mock',
      rankLabel: '6위'
    },
    {
      id: 'link-extra-naver-watch',
      category: 'links' as const,
      tone: 'link' as const,
      title: '관심 종목 게시판 반응 변화 원문',
      source: '네이버 종목토론',
      iconDomain: 'finance.naver.com',
      iconClass: 'naver',
      url: 'https://finance.naver.com/',
      meta: '방금 갱신 · 댓글 141',
      statusLabel: 'mock',
      rankLabel: '7위'
    },
    {
      id: 'link-extra-toss-community',
      category: 'links' as const,
      tone: 'link' as const,
      title: '관심 그룹에서 많이 담긴 종목 원문',
      source: '토스증권 커뮤니티',
      iconDomain: 'www.tossinvest.com',
      iconClass: 'toss',
      url: 'https://www.tossinvest.com/',
      meta: '방금 갱신 · 관심 96',
      statusLabel: 'mock',
      rankLabel: '8위'
    }
  ].map((item) => ({
    ...item
  }))
];

const route = useRoute();
const activeFilter = computed<NewsroomFilter>(() => {
  const feed = route.query.feed;
  const value = Array.isArray(feed) ? feed[0] : feed;
  return filterIds.includes(value as NewsroomFilter) ? (value as NewsroomFilter) : 'all';
});

const activeTab = computed(() => filterLabels[activeFilter.value]);
const activeItems = computed(() =>
  activeFilter.value === 'all' ? feedItems : feedItems.filter((item) => item.category === activeFilter.value)
);

const totalPages = computed(() => Math.max(1, Math.ceil(activeItems.value.length / pageSize)));
const activePage = computed(() => {
  const page = route.query.page;
  const rawValue = Array.isArray(page) ? page[0] : page;
  const parsed = Number(rawValue ?? 1);
  const safePage = Number.isFinite(parsed) ? Math.max(1, Math.floor(parsed)) : 1;
  return Math.min(safePage, totalPages.value);
});
const pagedItems = computed(() => {
  const start = (activePage.value - 1) * pageSize;
  return activeItems.value.slice(start, start + pageSize);
});
const pageNumbers = computed(() => Array.from({ length: totalPages.value }, (_, index) => index + 1));

const feedTypeLabels: Record<Exclude<NewsroomFilter, 'all'>, string> = {
  news: '뉴스',
  reports: '리포트',
  videos: '영상',
  links: '블로그·커뮤니티'
};

const itemsByCategory = (category: Exclude<NewsroomFilter, 'all'>) =>
  feedItems.filter((item) => item.category === category);

const overviewColumns = computed(() => [
  {
    id: 'news',
    cardClass: 'newsroom-live-feed-card',
    kicker: 'live feed',
    label: '실시간 뉴스',
    actionLabel: '뉴스만 몰아보기',
    to: { path: '/newsroom', query: { feed: 'news' } },
    items: itemsByCategory('news').slice(0, 8)
  },
  {
    id: 'reports',
    cardClass: 'newsroom-report-feed-card',
    kicker: 'research feed',
    label: '애널리스트 리포트',
    actionLabel: '리포트만 몰아보기',
    to: { path: '/newsroom', query: { feed: 'reports' } },
    items: itemsByCategory('reports').slice(0, 8)
  },
  {
    id: 'videos',
    cardClass: 'newsroom-video-feed-card',
    kicker: 'outside links',
    label: '증권 영상 새 글',
    actionLabel: '영상만 몰아보기',
    to: { path: '/newsroom', query: { feed: 'videos' } },
    items: itemsByCategory('videos').slice(0, 8)
  },
  {
    id: 'links',
    cardClass: 'newsroom-link-feed-card',
    kicker: 'columns · community',
    label: '블로그와 커뮤니티 링크',
    actionLabel: '원문 링크만 몰아보기',
    to: { path: '/newsroom', query: { feed: 'links' } },
    items: itemsByCategory('links').slice(0, 8)
  }
]);

const pageTo = (page: number) =>
  activeFilter.value === 'all'
    ? { path: '/newsroom', query: { page: String(page) } }
    : { path: '/newsroom', query: { feed: activeFilter.value, page: String(page) } };

const clampedPageTo = (page: number) => pageTo(Math.min(Math.max(page, 1), totalPages.value));

const pageRangeLabel = computed(() => {
  const start = activeItems.value.length === 0 ? 0 : (activePage.value - 1) * pageSize + 1;
  const end = Math.min(activePage.value * pageSize, activeItems.value.length);
  return `${start}-${end} / ${activeItems.value.length}`;
});

const listStatusLabel = computed(() =>
  activeFilter.value === 'all' ? '요약 보기' : `${pageRangeLabel.value} · 링크 원문 이동`
);
</script>

<template>
  <section class="newsroom-page">
    <section class="panel content-feed-card newsroom-title-card" aria-labelledby="newsroom-title">
      <div class="panel-header newsroom-title-header">
        <div>
          <p class="label">newsroom</p>
          <h2 id="newsroom-title">뉴스룸</h2>
        </div>
        <span class="status-pill subtle">뉴스 · 리포트 · 영상 · 원문</span>
      </div>
    </section>

    <section v-if="activeFilter === 'all'" class="newsroom-overview-grid" aria-label="뉴스룸 종합 요약">
      <article
        v-for="column in overviewColumns"
        :key="column.id"
        :class="['panel', 'content-feed-card', 'newsroom-overview-card', column.cardClass]"
      >
        <div class="panel-header newsroom-overview-header">
          <div>
            <p class="label">{{ column.kicker }}</p>
            <h3>{{ column.label }}</h3>
          </div>
          <div class="newsroom-overview-actions">
            <RouterLink class="detail-link" :to="column.to">{{ column.actionLabel }} →</RouterLink>
          </div>
        </div>

        <div class="newsroom-list compact-newsroom-list">
          <a
            v-for="item in column.items"
            :key="item.id"
            :class="['feed-row', 'newsroom-row', { 'ranked-feed-row': item.rankLabel }]"
            :href="item.url"
            target="_blank"
            rel="noreferrer noopener"
          >
            <span v-if="item.rankLabel" class="feed-rank">{{ item.rankLabel }}</span>
            <span
              :class="['site-icon', 'real-icon', 'source-badge', item.iconClass]"
              :aria-label="`${item.source} ${item.category}`"
              role="img"
            >
              <img :src="faviconUrl(item.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
            </span>
            <span class="feed-copy">
              <strong :title="item.title">{{ item.title }}</strong>
              <em>{{ feedTypeLabels[item.category] }} · {{ item.source }} · {{ item.meta }}</em>
            </span>
          </a>
        </div>
      </article>
    </section>

    <article v-else class="panel newsroom-feed-panel" aria-labelledby="newsroom-list-title">
      <div class="panel-header newsroom-list-header">
        <div>
          <p class="label">feed list</p>
          <h3 id="newsroom-list-title">{{ activeTab }}</h3>
        </div>
        <span class="status-pill subtle">{{ listStatusLabel }}</span>
      </div>

      <div class="newsroom-list">
        <a
          v-for="item in pagedItems"
          :key="item.id"
          :class="['feed-row', 'newsroom-row', { 'ranked-feed-row': item.rankLabel }]"
          :href="item.url"
          target="_blank"
          rel="noreferrer noopener"
        >
          <span v-if="item.rankLabel" class="feed-rank">{{ item.rankLabel }}</span>
          <span
            :class="['site-icon', 'real-icon', 'source-badge', item.iconClass]"
            :aria-label="`${item.source} ${item.category}`"
            role="img"
          >
            <img :src="faviconUrl(item.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
          </span>
          <span class="feed-copy">
            <strong :title="item.title">{{ item.title }}</strong>
            <em>{{ item.source }} · {{ item.meta }} · {{ item.statusLabel }}</em>
          </span>
        </a>
      </div>

      <nav class="newsroom-pager" aria-label="뉴스룸 페이지">
        <RouterLink
          :class="{ disabled: activePage === 1 }"
          :to="activePage === 1 ? pageTo(activePage) : clampedPageTo(activePage - 1)"
          :aria-disabled="activePage === 1"
        >
          이전
        </RouterLink>
        <div>
          <RouterLink
            v-for="page in pageNumbers"
            :key="page"
            :class="{ active: page === activePage }"
            :to="pageTo(page)"
          >
            {{ page }}
          </RouterLink>
        </div>
        <RouterLink
          :class="{ disabled: activePage === totalPages }"
          :to="activePage === totalPages ? pageTo(activePage) : clampedPageTo(activePage + 1)"
          :aria-disabled="activePage === totalPages"
        >
          다음
        </RouterLink>
      </nav>
    </article>
  </section>
</template>
