<script setup lang="ts">
import { ref } from 'vue';
import dashboardSummary from '../fixtures/dashboard-summary.json';
import quoteSnapshots from '../fixtures/quote-snapshots.json';
import reactionRanking from '../fixtures/reaction-ranking.json';

const marketFilters = ['전체', '언급 증가', '심리 변화', '가격 stale'];
const returnTimeModes = ['일', '주', '월', '년'];
const drawerTabs = [
  { id: 'reaction', label: '반응' },
  { id: 'metrics', label: '지표' },
  { id: 'watch', label: '관심' }
];
const activeDrawerTab = ref('reaction');
const retailSentimentIndex = dashboardSummary.retailSentimentIndex;
const topRiser = dashboardSummary.risingStars[0];
const totalMentions = reactionRanking.items.reduce((sum, item) => sum + item.mentionCount, 0);
const staleQuoteCount = quoteSnapshots.items.filter((quote) => quote.stale).length;
type ReactionRankingItem = (typeof reactionRanking.items)[number];
type ReactionMetric = 'bullish' | 'bearish';

const reactionSignalScore = (item: ReactionRankingItem, metric: ReactionMetric) =>
  Math.round(item.mentionCount * item.reactionDirectionRatio[metric]);
const buildReactionGroup = (id: 'positive' | 'negative', label: string, caption: string, metric: ReactionMetric) => ({
  id,
  label,
  caption,
  metric,
  ratioLabel: metric === 'bullish' ? '긍정' : '부정',
  items: [...reactionRanking.items]
    .sort((left, right) => reactionSignalScore(right, metric) - reactionSignalScore(left, metric))
    .slice(0, 3)
});
const reactionSignalGroups = [
  buildReactionGroup('positive', '언급+긍정 TOP 3', '언급량 x 긍정', 'bullish'),
  buildReactionGroup('negative', '언급+부정 TOP 3', '언급량 x 부정', 'bearish')
];

const formatPct = (value: number) => `${value > 0 ? '+' : ''}${value}%`;
const ratioPct = (value: number) => `${Math.round(value * 100)}%`;
const trendClass = (trend: string) => (trend === 'down' ? 'down' : 'up');
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
const externalIconClass = (item: { type: string; source?: string; iconDomain?: string }) => {
  if (item.type === 'youtube') return 'youtube';
  if (item.iconDomain === 'blog.naver.com') return 'naver-blog';
  if (item.iconDomain === 'finance.naver.com') return 'naver';
  if (item.iconDomain === 'www.tossinvest.com') return 'toss';
  return item.type;
};
const areaPointString = (pointString: string) => {
  const pairs = pointString.split(' ');
  const firstX = pairs[0]?.split(',')[0] ?? '0';
  const lastX = pairs[pairs.length - 1]?.split(',')[0] ?? '128';
  return `${pointString} ${lastX},46 ${firstX},46`;
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
const needleEnd = gaugePoint(retailSentimentIndex.value, 56);
</script>

<template>
  <section class="dashboard-page">
    <section class="standalone-search" aria-label="대시보드 검색과 필터">
      <p class="eyebrow">{{ reactionRanking.windowLabel }} · mock data</p>
      <div class="search-line">
        <div class="search-primary-row">
          <aside class="retail-sentiment-gauge-card" aria-label="개미 심리 지수">
            <div class="retail-sentiment-copy">
              <span>{{ retailSentimentIndex.label }}</span>
              <strong>{{ retailSentimentIndex.value }}<small>{{ retailSentimentIndex.unit }}</small></strong>
              <em>{{ retailSentimentIndex.status }} · {{ retailSentimentIndex.changeLabel }} {{ formatPct(retailSentimentIndex.changePct) }}</em>
              <div class="retail-sentiment-keywords" aria-label="대표 반응 키워드">
                <span v-for="keyword in retailSentimentIndex.keywords.slice(0, 2)" :key="keyword">{{ keyword }}</span>
              </div>
            </div>
            <div class="retail-gauge-wrap">
              <svg class="retail-gauge" viewBox="0 0 184 104" role="img" :aria-label="`${retailSentimentIndex.label} ${retailSentimentIndex.value}${retailSentimentIndex.unit}`">
                <path class="gauge-base" :d="gaugeArcPath(0, 100)" />
                <path
                  v-for="segment in retailSentimentIndex.segments"
                  :key="segment.label"
                  class="gauge-segment"
                  :d="gaugeArcPath(segment.start, segment.end)"
                  :stroke="segment.color"
                />
                <line class="gauge-needle" :x1="gaugeCenter.x" :y1="gaugeCenter.y" :x2="needleEnd.x" :y2="needleEnd.y" />
                <circle class="gauge-hub" :cx="gaugeCenter.x" :cy="gaugeCenter.y" r="4.6" />
              </svg>
              <div class="retail-gauge-scale" aria-hidden="true">
                <span>공포</span>
                <span>중립</span>
                <span>탐욕</span>
              </div>
            </div>
          </aside>
          <button class="mock-search" type="button" disabled>
            <span class="search-icon" aria-hidden="true"></span>
            <strong>/</strong>
            <span>종목이나 키워드 검색</span>
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
        <span>지연 시세 <strong>{{ staleQuoteCount }}건</strong></span>
        <span>관찰 <strong>{{ reactionRanking.items.length }}종목</strong></span>
        <span>투자 자문 아님</span>
      </div>
    </section>

    <section class="dashboard-main-layout">
      <div class="dashboard-content-flow">
        <section class="insight-grid">
          <article class="return-chart" aria-labelledby="return-title">
            <div class="panel-header">
              <div>
                <p class="label">paper return</p>
                <h3 id="return-title">커뮤니티 지표 비교</h3>
              </div>
              <div class="section-actions">
                <span class="status-pill warning">mock</span>
                <RouterLink class="detail-link" to="/communities">자세히 보기 →</RouterLink>
              </div>
            </div>

            <div class="community-graph" aria-label="커뮤니티별 mock 지표 그래프">
              <div class="community-graph-topline">
                <div class="return-range-tabs in-graph-tabs" aria-label="커뮤니티 비교 단위">
                  <button
                    v-for="mode in returnTimeModes"
                    :key="mode"
                    type="button"
                    :class="{ active: mode === '월' }"
                  >
                    {{ mode }}
                  </button>
                </div>
                <div class="graph-legend in-graph" aria-label="커뮤니티별 색상 범례">
                  <div v-for="series in dashboardSummary.communityReturnSeries" :key="series.community" class="legend-item">
                    <span class="legend-swatch" :style="`--swatch: ${series.color}`"></span>
                    <strong>{{ series.community }}</strong>
                  </div>
                </div>
              </div>
              <svg viewBox="0 0 1200 900" preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby="return-title">
                <text class="axis-title" x="50" y="50">return (%)</text>
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
                  v-for="series in dashboardSummary.communityReturnSeries"
                  :key="`${series.community}-line`"
                  class="return-line"
                  :points="widePointString(series.pointString)"
                  :stroke="series.color"
                />
                <g v-for="series in dashboardSummary.communityReturnSeries" :key="`${series.community}-points`">
                  <circle
                    v-for="point in series.points"
                    :key="`${series.community}-${point.x}-${point.y}`"
                    class="return-dot"
                    :cx="wideX(point.x)"
                    :cy="wideY(point.y)"
                    r="10"
                    :fill="series.color"
                  />
                </g>
                <text
                  v-for="series in dashboardSummary.communityReturnSeries"
                  :key="`${series.community}-end-label`"
                  class="series-end-label"
                  :x="endLabelX(series.points)"
                  :y="wideY(series.points[series.points.length - 1].y) + 8"
                  :fill="series.color"
                >
                  {{ formatPct(series.returnPct) }}
                </text>
              </svg>
            </div>

            <p class="chart-note">모의 성과 fixture · 투자 자문 아님</p>
          </article>

          <section class="mood-board stock-bubble-section reaction-panel" aria-labelledby="mood-title">
            <div class="mood-header">
              <div>
                <p class="label">지금 뜨는 반응</p>
                <h3 id="mood-title">종목 반응 한눈에</h3>
              </div>
              <div class="section-actions">
                <div class="period-tabs mood-period-tabs" aria-label="종목별 심리 비교 기간">
                  <button
                    v-for="period in dashboardSummary.moodPeriods"
                    :key="period"
                    type="button"
                    :class="{ active: period === dashboardSummary.activeMoodPeriod }"
                  >
                    {{ period }}
                  </button>
                </div>
                <RouterLink class="detail-link" to="/stocks/005930">자세히 보기 →</RouterLink>
              </div>
            </div>

            <div class="reaction-legend" aria-label="종목 반응 색상 설명">
              <span><i class="positive"></i>긍정 반응</span>
              <span><i class="negative"></i>부정 반응</span>
              <span><i class="neutral"></i>중립·기타</span>
            </div>

            <div class="reaction-split-board" aria-label="긍정 부정 반응별 종목 순위">
              <section
                v-for="group in reactionSignalGroups"
                :key="group.id"
                :class="['reaction-rank-group', `rank-group-${group.id}`]"
              >
                <div class="reaction-group-title">
                  <span>{{ group.label }}</span>
                  <small>{{ group.caption }}</small>
                </div>
                <div class="reaction-rank-list">
                  <article
                    v-for="(item, index) in group.items"
                    :key="`${group.id}-${item.symbol}`"
                    :class="['reaction-rank-row', `rank-${group.id}`]"
                    :data-rank="index + 1"
                    :data-tone="group.id"
                  >
                    <strong class="rank-number">{{ index + 1 }}</strong>
                    <div class="rank-main">
                      <strong>{{ item.name }}</strong>
                      <span>{{ item.symbol }} · {{ item.market }}</span>
                    </div>
                    <div class="rank-signal">
                      <em>{{ reactionSignalScore(item, group.metric) }}건</em>
                      <span>{{ ratioPct(item.reactionDirectionRatio[group.metric]) }} {{ group.ratioLabel }} · {{ item.mentionCount }} 언급</span>
                    </div>
                    <div class="rank-keywords">
                      <span v-for="keyword in item.topKeywords.slice(0, 3)" :key="`${group.id}-${item.symbol}-${keyword}`">{{ keyword }}</span>
                    </div>
                    <div class="sentiment-track" aria-label="긍정 부정 중립 비율">
                      <i class="positive" :style="`width: ${ratioPct(item.reactionDirectionRatio.bullish)}`"></i>
                      <i class="negative" :style="`width: ${ratioPct(item.reactionDirectionRatio.bearish)}`"></i>
                      <i class="neutral" :style="`width: ${ratioPct(item.reactionDirectionRatio.neutral)}`"></i>
                    </div>
                  </article>
                </div>
              </section>
            </div>
          </section>
        </section>

        <section class="indicator-section" aria-labelledby="indicator-title">
          <div class="section-title-row">
            <div>
              <p class="label">market pulse</p>
              <h3 id="indicator-title">실시간 주요 지표</h3>
            </div>
            <div class="section-actions">
              <span class="status-pill warning">mock · 지연 가능</span>
              <RouterLink class="detail-link" to="/indicators">자세히 보기 →</RouterLink>
            </div>
          </div>

          <div class="indicator-grid">
            <article
              v-for="indicator in dashboardSummary.marketIndicators"
              :key="indicator.label"
              :class="['indicator-card', trendClass(indicator.trend)]"
            >
              <div class="indicator-copy">
                <span>{{ indicator.label }}</span>
                <strong>{{ indicator.value }}</strong>
                <em>{{ formatPct(indicator.changePct) }}</em>
              </div>
              <svg viewBox="0 0 128 48" aria-hidden="true">
                <polygon class="spark-area" :points="areaPointString(indicator.pointString)" />
                <polyline :points="indicator.pointString" />
              </svg>
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
                  <img :src="faviconUrl(news.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
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
                <h3 id="analyst-title">애널리스트 리포트</h3>
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
                  <img :src="faviconUrl(report.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
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
                <h3 id="external-video-title">증권 영상 새 글</h3>
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
                  <img :src="faviconUrl(video.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
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
                  <img :src="faviconUrl(link.iconDomain)" alt="" loading="lazy" @error="hideBrokenIcon" />
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
          <article class="panel" aria-labelledby="quote-title">
            <div class="panel-header">
              <div>
                <p class="label">market placeholder</p>
                <h3 id="quote-title">가격 상태</h3>
              </div>
              <RouterLink class="detail-link" to="/indicators">자세히 보기 →</RouterLink>
            </div>
            <div class="compact-list">
              <div v-for="quote in quoteSnapshots.items" :key="quote.symbol" class="compact-row">
                <strong>{{ quote.name }}</strong>
                <span>{{ quote.price.toLocaleString() }}원</span>
                <span :class="['status-pill', quote.stale ? 'warning' : '']">
                  {{ quote.stale ? 'stale quote' : 'mock quote' }}
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
          <div class="drawer-card hot-stock-panel" aria-labelledby="hot-stock-title">
            <p class="label">라이브 패널 · 지금 언급 급상승 종목</p>
            <h3 id="hot-stock-title">{{ topRiser.name }}</h3>
            <strong>{{ formatPct(topRiser.mentionDeltaPct) }}</strong>
            <span>{{ topRiser.symbol }} · 언급 {{ topRiser.previousMentionCount }} → {{ topRiser.mentionCount }}</span>
            <div class="hot-stock-metrics">
              <div>
                <span>열기</span>
                <em>{{ topRiser.heatScore }}</em>
              </div>
              <div>
                <span>시장</span>
                <em>{{ topRiser.market }}</em>
              </div>
            </div>
            <div class="hot-stock-drivers" aria-label="이 종목 반응이 움직인 이유">
              <p>왜 움직였나</p>
              <div>
                <span v-for="driver in topRiser.reactionDrivers" :key="`${driver.type}-${driver.label}`" class="hot-stock-driver">
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
              <RouterLink class="detail-link" to="/stocks/005930">자세히 보기 →</RouterLink>
            </div>
            <div class="drawer-rising-list">
              <article v-for="item in dashboardSummary.risingStars" :key="item.symbol">
                <strong>{{ item.name }}</strong>
                <span>{{ item.symbol }} · 언급 {{ item.previousMentionCount }} → {{ item.mentionCount }}</span>
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
            <article v-for="item in reactionRanking.items.slice(0, 4)" :key="`${item.symbol}-watch`">
              <strong>{{ item.name }}</strong>
              <span>{{ item.symbol }}</span>
              <em>{{ formatPct(item.mentionDeltaPct) }}</em>
            </article>
          </div>
        </section>
      </aside>
    </section>
  </section>
</template>
