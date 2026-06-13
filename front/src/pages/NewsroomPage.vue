<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import dashboardSummary from '../fixtures/dashboard-summary.json';
import {
  buildNewsroomFeedItems,
  fetchRealEstateNewsroom,
  type NewsroomFeedItem,
  type NewsroomFilter
} from '../lib/realestate-content';
import { sourceIconUrl } from '../lib/source-icons';

const filterIds: NewsroomFilter[] = ['all', 'news', 'reports', 'videos', 'links'];
const filterLabels: Record<NewsroomFilter, string> = {
  all: '종합',
  news: '뉴스',
  reports: '리포트',
  videos: '영상',
  links: '블로그 및 커뮤니티'
};

const pageSize = 15;

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

const externalIconClass = (item: { type: string; iconDomain?: string }) => {
  if (item.type === 'youtube') return 'youtube';
  if (item.iconDomain === 'blog.naver.com') return 'naver-blog';
  if (item.iconDomain === 'finance.naver.com') return 'naver';
  if (item.iconDomain === 'www.tossinvest.com') return 'toss';
  return item.type;
};

const fallbackFeedItems: NewsroomFeedItem[] = [
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
      id: 'news-extra-rate-policy',
      category: 'news' as const,
      tone: 'news' as const,
      title: '주담대 금리 관망 구간, 전세 우려 댓글 확대',
      source: '정책 브리핑',
      iconDomain: 'www.korea.kr',
      iconClass: 'news-macro',
      url: 'https://www.korea.kr/',
      meta: '27분 전',
      statusLabel: 'mock'
    },
    {
      id: 'news-extra-supply',
      category: 'news' as const,
      tone: 'news' as const,
      title: '입주 물량 감소 이슈로 전세 키워드 동반 증가',
      source: '한국부동산원',
      iconDomain: 'www.reb.or.kr',
      iconClass: 'news-market',
      url: 'https://www.reb.or.kr/',
      meta: '42분 전',
      statusLabel: 'mock'
    },
    {
      id: 'news-extra-transport',
      category: 'news' as const,
      tone: 'news' as const,
      title: '교통 호재 발표 뒤 생활권 커뮤니티 체감 온도 상승',
      source: '국토교통부',
      iconDomain: 'www.molit.go.kr',
      iconClass: 'news-index',
      url: 'https://www.molit.go.kr/',
      meta: '55분 전',
      statusLabel: 'mock'
    },
    {
      id: 'report-extra-jeonse',
      category: 'reports' as const,
      tone: 'report' as const,
      title: '전세 지수와 매물 체감 반응의 괴리 구간 점검',
      source: '한국부동산원 통계',
      iconDomain: 'www.reb.or.kr',
      iconClass: 'news-research',
      url: 'https://www.reb.or.kr/',
      meta: '4시간 전',
      statusLabel: 'mock'
    },
    {
      id: 'report-extra-public-data',
      category: 'reports' as const,
      tone: 'report' as const,
      title: '실거래 공개 지연과 커뮤니티 선행 반응 비교',
      source: '공공데이터포털',
      iconDomain: 'www.data.go.kr',
      iconClass: 'news-research',
      url: 'https://www.data.go.kr/',
      meta: '5시간 전',
      statusLabel: 'mock'
    },
    {
      id: 'report-extra-policy-cycle',
      category: 'reports' as const,
      tone: 'report' as const,
      title: '정책 이벤트와 지역별 관심도 괴리 점검',
      source: '부동산 리서치',
      iconDomain: 'www.reb.or.kr',
      iconClass: 'news-research',
      url: 'https://www.reb.or.kr/',
      meta: '6시간 전',
      statusLabel: 'mock'
    },
    {
      id: 'video-extra-jeonse',
      category: 'videos' as const,
      tone: 'video' as const,
      title: '전세가 움직이는 지역을 장전에 확인하는 법',
      source: '부동산 방송 클립',
      iconDomain: 'www.youtube.com',
      iconClass: 'youtube',
      url: 'https://www.youtube.com/results?search_query=%EC%A0%84%EC%84%B8+%EC%A7%80%EC%97%AD+%EB%B6%80%EB%8F%99%EC%82%B0',
      meta: '3일 전 · 조회 4.8만',
      statusLabel: 'mock',
      rankLabel: '6위'
    },
    {
      id: 'video-extra-policy',
      category: 'videos' as const,
      tone: 'video' as const,
      title: '정책 발표 시즌, 커뮤니티가 먼저 반응한 지역은?',
      source: '부동산 유튜브',
      iconDomain: 'www.youtube.com',
      iconClass: 'youtube',
      url: 'https://www.youtube.com/results?search_query=%EB%B6%80%EB%8F%99%EC%82%B0+%EC%A0%95%EC%B1%85+%EC%A7%80%EC%97%AD',
      meta: '4일 전 · 조회 3.6만',
      statusLabel: 'mock',
      rankLabel: '7위'
    },
    {
      id: 'video-extra-region-review',
      category: 'videos' as const,
      tone: 'video' as const,
      title: '오늘 언급량이 가장 크게 바뀐 지역 리뷰',
      source: '지역 리뷰',
      iconDomain: 'www.youtube.com',
      iconClass: 'youtube',
      url: 'https://www.youtube.com/results?search_query=%EB%B6%80%EB%8F%99%EC%82%B0+%EC%A7%80%EC%97%AD+%EB%A6%AC%EB%B7%B0',
      meta: '4일 전 · 조회 2.9만',
      statusLabel: 'mock',
      rankLabel: '8위'
    },
    {
      id: 'link-extra-naver-cafe',
      category: 'links' as const,
      tone: 'link' as const,
      title: '전세 매물 체감 토론 원문 묶음',
      source: '네이버 카페',
      iconDomain: 'cafe.naver.com',
      iconClass: 'community',
      url: 'https://section.cafe.naver.com/',
      meta: '방금 갱신 · 댓글 188',
      statusLabel: 'mock',
      rankLabel: '6위'
    },
    {
      id: 'link-extra-daum-cafe',
      category: 'links' as const,
      tone: 'link' as const,
      title: '관심 지역 게시판 반응 변화 원문',
      source: '다음 카페',
      iconDomain: 'cafe.daum.net',
      iconClass: 'naver',
      url: 'https://cafe.daum.net/',
      meta: '방금 갱신 · 댓글 141',
      statusLabel: 'mock',
      rankLabel: '7위'
    },
    {
      id: 'link-extra-land-community',
      category: 'links' as const,
      tone: 'link' as const,
      title: '관심 생활권에서 많이 언급된 단지 원문',
      source: '부동산 커뮤니티',
      iconDomain: 'new.land.naver.com',
      iconClass: 'toss',
      url: 'https://new.land.naver.com/',
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
const feedItems = ref<NewsroomFeedItem[]>(fallbackFeedItems);
const newsroomLoadState = ref<'loading' | 'live' | 'fallback'>('loading');

const activeTab = computed(() => filterLabels[activeFilter.value]);
const activeItems = computed(() =>
  activeFilter.value === 'all'
    ? feedItems.value
    : feedItems.value.filter((item) => item.category === activeFilter.value)
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
  feedItems.value.filter((item) => item.category === category);

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
    label: '정책·통계 리포트',
    actionLabel: '리포트만 몰아보기',
    to: { path: '/newsroom', query: { feed: 'reports' } },
    items: itemsByCategory('reports').slice(0, 8)
  },
  {
    id: 'videos',
    cardClass: 'newsroom-video-feed-card',
    kicker: 'outside links',
    label: '부동산 영상 새 글',
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

const newsroomSourceLabel = computed(() => {
  if (newsroomLoadState.value === 'live') return 'content API 반영';
  if (newsroomLoadState.value === 'loading') return 'content API 확인 중';
  return 'mock fallback';
});

const titleStatusLabel = computed(() => `뉴스 · 리포트 · 영상 · 원문 · ${newsroomSourceLabel.value}`);

const refreshNewsroomContent = async () => {
  newsroomLoadState.value = 'loading';
  try {
    const contentItems = await fetchRealEstateNewsroom({
      feed: activeFilter.value,
      page: 1,
      pageSize: 100
    });
    const mappedItems = buildNewsroomFeedItems(contentItems);
    feedItems.value = mappedItems.length ? mappedItems : fallbackFeedItems;
    newsroomLoadState.value = mappedItems.length ? 'live' : 'fallback';
  } catch {
    feedItems.value = fallbackFeedItems;
    newsroomLoadState.value = 'fallback';
  }
};

onMounted(() => {
  void refreshNewsroomContent();
});

watch(activeFilter, () => {
  void refreshNewsroomContent();
});
</script>

<template>
  <section class="newsroom-page">
    <section class="panel content-feed-card newsroom-title-card" aria-labelledby="newsroom-title">
      <div class="panel-header newsroom-title-header">
        <div>
          <p class="label">newsroom</p>
          <h2 id="newsroom-title">뉴스룸</h2>
        </div>
        <span class="status-pill subtle">{{ titleStatusLabel }}</span>
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
              <img :src="sourceIconUrl(item.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
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
            <img :src="sourceIconUrl(item.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
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
