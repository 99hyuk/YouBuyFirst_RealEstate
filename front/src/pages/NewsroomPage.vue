<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import {
  subscribeRealEstateBatchUpdates,
  type BatchUpdateSubscription
} from '../lib/realestate-batch-updates';
import {
  buildNewsroomFeedItems,
  ensureNewsroomCategoryCoverage,
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

const route = useRoute();
const activeFilter = computed<NewsroomFilter>(() => {
  const feed = route.query.feed;
  const value = Array.isArray(feed) ? feed[0] : feed;
  return filterIds.includes(value as NewsroomFilter) ? (value as NewsroomFilter) : 'all';
});
const feedItems = ref<NewsroomFeedItem[]>([]);
const newsroomLoadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
let batchUpdateSubscription: BatchUpdateSubscription | null = null;

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
    label: '실시간 뉴스',
    actionLabel: '뉴스만 몰아보기',
    to: { path: '/newsroom', query: { feed: 'news' } },
    items: itemsByCategory('news').slice(0, 8)
  },
  {
    id: 'reports',
    cardClass: 'newsroom-report-feed-card',
    label: '정책·통계 리포트',
    actionLabel: '리포트만 몰아보기',
    to: { path: '/newsroom', query: { feed: 'reports' } },
    items: itemsByCategory('reports').slice(0, 8)
  },
  {
    id: 'videos',
    cardClass: 'newsroom-video-feed-card',
    label: '부동산 영상',
    actionLabel: '영상만 몰아보기',
    to: { path: '/newsroom', query: { feed: 'videos' } },
    items: itemsByCategory('videos').slice(0, 8)
  },
  {
    id: 'links',
    cardClass: 'newsroom-link-feed-card',
    label: '블로그·커뮤니티',
    actionLabel: '원문 링크만 몰아보기',
    to: { path: '/newsroom', query: { feed: 'links' } },
    items: itemsByCategory('links').slice(0, 8)
  }
]);

const overviewEmptyText = (columnLabel: string) => {
  if (newsroomLoadState.value === 'loading') return '콘텐츠를 불러오는 중입니다.';
  if (newsroomLoadState.value === 'error') return '콘텐츠를 불러오지 못했습니다. 출처와 기준 시각 확인이 필요합니다.';
  if (feedItems.value.length) {
    return `이번 갱신에서는 ${columnLabel} 유형이 아직 분리되지 않았습니다.`;
  }
  return '수집된 항목이 아직 없습니다. 수집 전/insufficient 상태입니다.';
};

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

const newsroomFetchFeeds = (): Exclude<NewsroomFilter, 'all'>[] =>
  activeFilter.value === 'all'
    ? ['news', 'reports', 'videos', 'links']
    : [activeFilter.value];

const dedupeNewsroomItems = (items: NewsroomFeedItem[]) => {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (seen.has(item.id)) return false;
    seen.add(item.id);
    return true;
  });
};

const refreshNewsroomContent = async () => {
  newsroomLoadState.value = 'loading';
  feedItems.value = [];
  try {
    const groupedItems = await Promise.all(
      newsroomFetchFeeds().map(async (feed) => {
        const contentItems = await fetchRealEstateNewsroom({
          feed,
          page: 1,
          pageSize: 100
        });
        return buildNewsroomFeedItems(contentItems)
          .filter((item) => item.category === feed);
      })
    );
    const mappedItems = ensureNewsroomCategoryCoverage(dedupeNewsroomItems(groupedItems.flat()));
    feedItems.value = mappedItems;
    newsroomLoadState.value = mappedItems.length ? 'live' : 'empty';
  } catch {
    feedItems.value = [];
    newsroomLoadState.value = 'error';
  }
};

onMounted(() => {
  void refreshNewsroomContent();
  batchUpdateSubscription = subscribeRealEstateBatchUpdates((event) => {
    if (event.topic === 'newsroom') {
      void refreshNewsroomContent();
    }
  });
});

onBeforeUnmount(() => {
  batchUpdateSubscription?.close();
  batchUpdateSubscription = null;
});

watch(activeFilter, () => {
  void refreshNewsroomContent();
});
</script>

<template>
  <section class="newsroom-page">
    <section class="newsroom-hero" aria-labelledby="newsroom-title">
      <div>
        <p class="label">콘텐츠 피드</p>
        <h2 id="newsroom-title">뉴스룸</h2>
        <span>뉴스·리포트·영상·블로그·커뮤니티를 원문 링크 기준으로 모아봅니다.</span>
      </div>
    </section>

    <section v-if="activeFilter === 'all'" class="newsroom-overview-grid" aria-label="뉴스룸 종합 요약">
      <article
        v-for="column in overviewColumns"
        :key="column.id"
        :class="['panel', 'content-feed-card', 'newsroom-overview-card', column.cardClass]"
      >
        <div class="panel-header newsroom-overview-header">
          <div class="feed-title-wrap">
            <span class="feed-title-dot" aria-hidden="true"></span>
            <h3 class="feed-panel-title">{{ column.label }}</h3>
          </div>
          <div class="newsroom-overview-actions">
            <RouterLink class="detail-link" :to="column.to">{{ column.actionLabel }} →</RouterLink>
          </div>
        </div>

        <div class="newsroom-list compact-newsroom-list">
          <p v-if="!column.items.length" class="newsroom-empty-state">
            {{ overviewEmptyText(column.label) }}
          </p>
          <a
            v-for="item in column.items"
            :key="item.id"
            class="feed-row newsroom-row"
            :href="item.url"
            target="_blank"
            rel="noreferrer noopener"
          >
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
        <div class="feed-title-wrap">
          <span class="feed-title-dot" aria-hidden="true"></span>
          <h3 id="newsroom-list-title" class="feed-panel-title">{{ activeTab }}</h3>
        </div>
        <span class="status-pill subtle">{{ listStatusLabel }}</span>
      </div>

      <div class="newsroom-list">
        <p v-if="!pagedItems.length" class="newsroom-empty-state">
          {{ newsroomLoadState === 'loading' ? '콘텐츠를 불러오는 중입니다.' : newsroomLoadState === 'error' ? '콘텐츠를 불러오지 못했습니다. 출처와 기준 시각 확인이 필요합니다.' : '선택한 feed에 수집된 항목이 아직 없습니다. 수집 전/insufficient 상태입니다.' }}
        </p>
        <a
          v-for="item in pagedItems"
          :key="item.id"
          class="feed-row newsroom-row"
          :href="item.url"
          target="_blank"
          rel="noreferrer noopener"
        >
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
