import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { describe, expect, it } from 'vitest';

import App from '../App.vue';
import dashboardSummary from '../fixtures/dashboard-summary.json';
import reactionRanking from '../fixtures/reaction-ranking.json';
import { routes } from '../router/routes';

const testDir = dirname(fileURLToPath(import.meta.url));

describe('front dashboard shell', () => {
  it('defines the route inventory shell', () => {
    const routePaths = routes.map((route) => route.path);

    expect(routePaths).toEqual([
      '/',
      '/dashboard',
      '/stocks/:symbol',
      '/communities',
      '/indicators',
      '/agents',
      '/portfolio'
    ]);
    expect(routes[0]).toMatchObject({ redirect: '/dashboard' });
  });

  it('declares an inline favicon so browser checks do not request /favicon.ico', () => {
    const indexHtml = readFileSync(resolve(testDir, '../../index.html'), 'utf8');

    expect(indexHtml).toContain('rel="icon"');
    expect(indexHtml).toContain('data:image/svg+xml');
  });

  it('keeps dashboard mock data explicit and reviewable', () => {
    const firstRiser = dashboardSummary.risingStars[0]!;
    const reactionDrivers = firstRiser.reactionDrivers!;
    const movementReasons = firstRiser.movementReasons!;

    expect(dashboardSummary.productName).toBe('너나사');
    expect(dashboardSummary.confirmationNeeded).toContain('열기 지수 용어 확정');
    expect(firstRiser).toMatchObject({
      symbol: '042700',
      name: '한미반도체',
      previousMentionCount: 22,
      mentionCount: 41,
      dataStatus: 'mock'
    });
    expect(firstRiser.coreReactions).toContain('HBM 장비 수요가 다시 붙는다는 기대가 늘었습니다.');
    expect(reactionDrivers).toHaveLength(4);
    expect(reactionDrivers.map((driver) => driver.type)).toEqual([
      '기사',
      '공시',
      '커뮤니티',
      '가격'
    ]);
    expect(movementReasons).toHaveLength(3);
    expect(dashboardSummary.communityReturns[0]).toMatchObject({
      community: '네이버 종토방',
      dataStatus: 'mock'
    });
    expect(dashboardSummary.returnPeriods).toEqual(['1D', '7D', '1M', '3M', '6M']);
    expect(dashboardSummary.moodPeriods).toEqual(['1D', '7D', '1M', '3M']);
    expect(dashboardSummary.communityReturnSeries[0].points).toHaveLength(6);
    expect(dashboardSummary.marketIndicators).toHaveLength(6);
    expect(dashboardSummary.liveNews).toHaveLength(5);
    expect(dashboardSummary.liveNews[0]).toMatchObject({
      source: 'Yahoo Finance',
      iconDomain: 'finance.yahoo.com'
    });
    expect(dashboardSummary.analystReports).toHaveLength(4);
    expect(dashboardSummary.analystReports[0]).toMatchObject({
      source: '네이버페이 증권 리서치',
      iconDomain: 'finance.naver.com',
      tag: 'research',
      dataStatus: 'mock'
    });
    expect(dashboardSummary.macroMetrics).toHaveLength(8);
    expect(dashboardSummary.externalContent.videos).toHaveLength(4);
    expect(dashboardSummary.externalContent.links).toHaveLength(5);
    expect(dashboardSummary.externalContent.videos[0]).toMatchObject({
      type: 'youtube',
      source: '삼프로TV',
      iconDomain: 'www.youtube.com',
      dataStatus: 'rss'
    });
    expect(dashboardSummary.externalContent.links[0]).toMatchObject({
      type: 'blog',
      source: '메르 블로그',
      iconDomain: 'blog.naver.com',
      dataStatus: 'rss'
    });
    expect(reactionRanking.items[0]).toMatchObject({
      symbol: '005930',
      name: '삼성전자',
      dataStatus: 'mock'
    });
  });

  it('renders navigation for every planned route', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes
    });

    router.push('/dashboard');
    await router.isReady();

    const firstRiser = dashboardSummary.risingStars[0]!;
    const reactionDrivers = firstRiser.reactionDrivers!;
    const movementReasons = firstRiser.movementReasons!;

    const wrapper = mount(App, {
      global: {
        plugins: [router]
      }
    });

    expect(wrapper.get('[data-testid="app-title"]').text()).toContain('YouBuyFirst');
    expect(wrapper.get('[data-testid="app-title"]').attributes('href')).toBe('/dashboard');
    expect(wrapper.get('[data-testid="nav-dashboard"]').text()).toContain('대시보드');
    expect(wrapper.get('[data-testid="nav-stock"]').text()).toContain('종목 상세');
    expect(wrapper.get('[data-testid="nav-communities"]').text()).toContain('커뮤니티');
    expect(wrapper.get('[data-testid="nav-indicators"]').text()).toContain('주요 지표');
    expect(wrapper.get('[data-testid="nav-agents"]').text()).toContain('에이전트');
    expect(wrapper.get('[data-testid="nav-portfolio"]').text()).toContain('내 포트폴리오');
    expect(wrapper.find('.site-footer').exists()).toBe(true);
    expect(wrapper.find('.site-footer').text()).toContain('너나사 YouBuyFirst');
    expect(wrapper.find('.site-footer').text()).toContain('문의 yh99cho1@gmail.com');
    expect(wrapper.find('.site-footer a').attributes('href')).toBe('mailto:yh99cho1@gmail.com');
    expect(wrapper.find('.site-footer').text()).toContain('서비스 특징');
    expect(wrapper.find('.site-footer').text()).toContain('유의사항');
    expect(wrapper.find('.site-footer').text()).toContain('데이터 출처');
    expect(wrapper.find('.site-footer').text()).toContain('어떠한 종목 매매도 권유하지 않습니다');
    expect(wrapper.find('.site-footer').text()).toContain('KRX · 네이버 금융');
    expect(wrapper.find('.site-footer').text()).toContain('비공개·유료 데이터 미사용');
    expect(wrapper.text()).not.toContain('커뮤니티 반응 대시보드');
    expect(wrapper.text()).toContain('투자자들이 먼저 떠드는 종목을 읽습니다');
    expect(wrapper.text()).toContain('종목이나 키워드 검색');
    expect(wrapper.find('.mock-search strong').text()).toBe('/');
    expect(wrapper.text()).toContain('지금 뜨는 반응');
    expect(wrapper.text()).toContain('실시간 아님');
    expect(wrapper.text()).not.toContain('반응 터미널');
    expect(wrapper.text()).toContain('종목 반응 한눈에');
    expect(wrapper.text()).toContain('지금 언급 급상승 종목');
    expect(wrapper.text()).toContain('실시간 주요 지표');
    expect(wrapper.text()).toContain('실시간 뉴스');
    expect(wrapper.text()).toContain('애널리스트 리포트');
    expect(wrapper.text()).toContain('반도체 장비 업종, HBM 수요와 수주 모멘텀 점검');
    expect(wrapper.text()).not.toContain('매크로 지표 자세히 보기');
    expect(wrapper.text()).toContain('긍정 반응');
    expect(wrapper.text()).toContain('부정 반응');
    expect(wrapper.text()).toContain('라이브 패널');
    expect(wrapper.text()).toContain('라이징 스타');
    expect(wrapper.text()).toContain('커뮤니티 지표 비교');
    expect(wrapper.text()).toContain('1D');
    expect(wrapper.text()).not.toContain('1Y');
    expect(wrapper.text()).toContain('투자 자문 아님');
    expect(wrapper.text()).toContain('로그인');
    expect(wrapper.text()).toContain('RAIL EDGE TEST · 오른쪽 탭 옆에서 시작');
    expect(wrapper.text()).toContain('증권 영상 새 글');
    expect(wrapper.text()).toContain('블로그와 커뮤니티 링크');
    expect(wrapper.text()).toContain('삼프로TV');
    expect(wrapper.text()).toContain('메르 블로그');
    expect(wrapper.text()).not.toContain('실제 API 계약 전까지 필요한 기획 질문');
    expect(wrapper.text()).not.toContain('HBM 장비 수요가 다시 붙는다는 기대가 늘었습니다.');
    expect(wrapper.find('.standalone-search').exists()).toBe(true);
    expect(wrapper.find('.search-icon').exists()).toBe(true);
    expect(wrapper.find('.mock-search').text()).not.toContain('KR');
    expect(wrapper.find('.mock-search').text()).not.toContain('mock search');
    expect(wrapper.find('.signal-strip').exists()).toBe(false);
    expect(wrapper.find('.dashboard-meta-strip').exists()).toBe(true);
    expect(wrapper.find('.briefing-copy-compact').exists()).toBe(false);
    expect(wrapper.get('.dashboard-content-flow').element.firstElementChild?.classList.contains('insight-grid')).toBe(true);
    expect(wrapper.find('.insight-grid .reaction-panel').exists()).toBe(true);
    expect(wrapper.find('.dashboard-content-flow > .reaction-panel').exists()).toBe(false);
    expect(wrapper.find('.dashboard-content-flow .rising-stars').exists()).toBe(false);
    expect(wrapper.find('.side-drawer .drawer-rising-stars').exists()).toBe(true);
    expect(wrapper.get('.community-graph svg').attributes('viewBox')).toBe('0 0 1200 900');
    expect(wrapper.get('.community-graph svg').attributes('preserveAspectRatio')).toBe('xMidYMid meet');
    expect(wrapper.find('.return-range-tabs').exists()).toBe(true);
    expect(wrapper.find('.community-graph .return-range-tabs').exists()).toBe(true);
    expect(wrapper.find('.return-toolbar').exists()).toBe(false);
    expect(wrapper.find('.return-chart .period-tabs').exists()).toBe(false);
    expect(wrapper.find('.community-graph-topline').exists()).toBe(true);
    expect(wrapper.find('.community-graph .return-range-tabs').text()).toBe('일주월년');
    const communityAxisLabels = wrapper.findAll('.community-graph .axis-label.x-axis').map((label) => label.text());
    expect(communityAxisLabels).not.toContain('1D');
    expect(communityAxisLabels).not.toContain('7D');
    expect(communityAxisLabels).not.toContain('1M');
    expect(wrapper.find('.return-kpi-row').exists()).toBe(false);
    expect(wrapper.findAll('.return-area')).toHaveLength(0);
    expect(wrapper.findAll('.series-end-label')).toHaveLength(dashboardSummary.communityReturnSeries.length);
    expect(wrapper.find('.chart-y-axis').exists()).toBe(true);
    expect(wrapper.findAll('.y-axis-right')).toHaveLength(3);
    expect(wrapper.find('.community-graph .graph-legend').exists()).toBe(true);
    expect(wrapper.find('.community-graph .graph-legend em').exists()).toBe(false);
    expect(wrapper.find('.hot-stock-panel').exists()).toBe(true);
    expect(wrapper.text()).toContain('왜 움직였나');
    expect(wrapper.findAll('.hot-stock-driver')).toHaveLength(reactionDrivers.length);
    expect(wrapper.findAll('.movement-reasons li')).toHaveLength(movementReasons.length);
    expect(wrapper.find('.side-drawer').exists()).toBe(true);
    expect(wrapper.findAll('.drawer-tab')).toHaveLength(3);
    expect(wrapper.findAll('.drawer-tab').map((tab) => tab.text())).toEqual(['반응', '지표', '관심']);
    expect(wrapper.find('.drawer-metric-panel').exists()).toBe(true);
    expect(wrapper.find('.drawer-watch-panel').exists()).toBe(true);
    expect(wrapper.find('.drawer-tab-screen').isVisible()).toBe(true);
    await wrapper.findAll('.drawer-tab')[1].trigger('click');
    expect(wrapper.findAll('.drawer-tab')[1].classes()).toContain('active');
    expect(wrapper.find('.drawer-metric-panel').isVisible()).toBe(true);
    await wrapper.findAll('.drawer-tab')[2].trigger('click');
    expect(wrapper.findAll('.drawer-tab')[2].classes()).toContain('active');
    expect(wrapper.find('.drawer-watch-panel').isVisible()).toBe(true);
    expect(wrapper.find('.edge-rail').exists()).toBe(true);
    expect(wrapper.find('.edge-panel').exists()).toBe(true);
    expect(wrapper.find('.theme-toggle').exists()).toBe(true);
    expect(wrapper.find('.edge-rail button.active').exists()).toBe(false);
    expect(wrapper.find('.edge-panel').classes()).not.toContain('open');
    await wrapper.find('.rail-expand').trigger('click');
    expect(wrapper.find('.app-shell').classes()).toContain('edge-panel-open');
    expect(wrapper.find('.edge-panel').classes()).toContain('open');
    expect(wrapper.find('.edge-panel').text()).toContain('관심 주식 TOP 8');
    expect(wrapper.find('.edge-rail button.active').text()).toContain('관심');
    await wrapper.findAll('.edge-rail button')[3].trigger('click');
    expect(wrapper.findAll('.edge-rail button')[3].attributes('aria-pressed')).toBe('true');
    expect(wrapper.find('.edge-panel').text()).toContain('최근 본 화면');
    await wrapper.find('.rail-expand').trigger('click');
    expect(wrapper.find('.edge-panel').classes()).not.toContain('open');
    expect(wrapper.find('.edge-rail button.active').exists()).toBe(false);
    expect(wrapper.findAll('.edge-rail button')[3].attributes('aria-pressed')).toBe('false');
    expect(wrapper.find('.topbar .live-ticker').exists()).toBe(true);
    expect(wrapper.find('.dashboard-page > .live-ticker').exists()).toBe(false);
    expect(wrapper.find('.reaction-legend').exists()).toBe(true);
    expect(wrapper.findAll('.detail-link').length).toBeGreaterThanOrEqual(4);
    expect(wrapper.findAll('.indicator-card')).toHaveLength(dashboardSummary.marketIndicators.length);
    expect(wrapper.findAll('.spark-area')).toHaveLength(dashboardSummary.marketIndicators.length);
    expect(wrapper.find('.analyst-feed').exists()).toBe(true);
    expect(wrapper.findAll('.content-feed-card')).toHaveLength(4);
    expect(wrapper.find('.live-feed-card .panel-header').exists()).toBe(true);
    expect(wrapper.find('.report-feed-card .panel-header').exists()).toBe(true);
    expect(wrapper.find('.video-feed-card .panel-header').exists()).toBe(true);
    expect(wrapper.find('.link-feed-card .panel-header').exists()).toBe(true);
    expect(wrapper.findAll('.feed-list')).toHaveLength(4);
    expect(wrapper.findAll('.feed-row')).toHaveLength(16);
    expect(wrapper.findAll('.feed-open')).toHaveLength(16);
    expect(wrapper.findAll('.site-icon.youtube')).toHaveLength(dashboardSummary.externalContent.videos.length);
    expect(wrapper.findAll('.site-icon.naver-blog').length).toBeGreaterThanOrEqual(1);
    expect(wrapper.findAll('.site-icon.news-source')).toHaveLength(
      dashboardSummary.liveNews.slice(0, 4).length + dashboardSummary.analystReports.length
    );
    expect(wrapper.findAll('.site-icon.real-icon img')).toHaveLength(
      dashboardSummary.liveNews.slice(0, 4).length +
        dashboardSummary.analystReports.length +
        dashboardSummary.externalContent.videos.length +
        dashboardSummary.externalContent.links.slice(0, 4).length
    );
    const iconSources = wrapper.findAll('.site-icon.real-icon img').map((image) => image.attributes('src'));
    expect(iconSources.filter((src) => src === 'https://ssl.pstatic.net/static/blog/icon/favicon.ico')).toHaveLength(2);
    expect(iconSources.filter((src) => src === 'https://ssl.pstatic.net/imgstock/favi/favicon-96x96.png')).toHaveLength(4);
    expect(iconSources).not.toContain('https://www.google.com/s2/favicons?domain=blog.naver.com&sz=64');
    expect(iconSources).not.toContain('https://www.google.com/s2/favicons?domain=finance.naver.com&sz=64');
    expect(wrapper.findAll('.feed-row')[0].attributes('target')).toBe('_blank');
    expect(wrapper.find('.macro-detail').exists()).toBe(false);
    expect(wrapper.findAll('.macro-metric-card')).toHaveLength(0);
    expect(wrapper.find('.mood-period-tabs').exists()).toBe(true);
    expect(reactionRanking.items).toHaveLength(6);
    expect(wrapper.findAll('.reaction-rank-group')).toHaveLength(2);
    expect(wrapper.findAll('.reaction-rank-group').map((group) => group.text())).toEqual([
      expect.stringContaining('언급+긍정 TOP 3'),
      expect.stringContaining('언급+부정 TOP 3')
    ]);
    expect(wrapper.findAll('.reaction-rank-row')).toHaveLength(6);
    expect(wrapper.findAll('.rank-number').map((rank) => rank.text())).toEqual(['1', '2', '3', '1', '2', '3']);
    expect(wrapper.findAll('.reaction-rank-row').map((card) => card.attributes('data-rank'))).toEqual([
      '1',
      '2',
      '3',
      '1',
      '2',
      '3'
    ]);
    expect(wrapper.find('.stock-bubble').exists()).toBe(false);
    expect(wrapper.find('.reaction-panel').exists()).toBe(true);
    expect(wrapper.find('.return-chart.panel').exists()).toBe(false);
    expect(wrapper.find('.reaction-panel.panel').exists()).toBe(false);
    expect(wrapper.find('.hero-focus').exists()).toBe(false);
    expect(wrapper.find('.community-graph').exists()).toBe(true);
    expect(wrapper.findAll('.return-line')).toHaveLength(dashboardSummary.communityReturnSeries.length);
    expect(wrapper.find('.return-bars').exists()).toBe(false);
    expect(wrapper.find('.feature-rail').exists()).toBe(false);
  });

  it('uses a cleaner YASUN-style visual system with Pretendard', () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toContain('Pretendard');
    expect(styles).toContain('--surface');
    expect(styles).toContain('--positive-blue');
    expect(styles).toContain('--negative-red');
    expect(styles).toContain('@keyframes live-shift');
    expect(styles).toContain('position: sticky');
    expect(styles).toContain('.topbar-ticker');
    expect(styles).toContain('.site-footer');
    expect(styles).toContain('.site-footer-grid');
    expect(styles).toContain('.site-footer-bottom');
    expect(styles).toContain('.drawer-rising-stars');
    expect(styles).toContain('max-width: 1500px');
    expect(styles).toContain('--market-up');
    expect(styles).toContain('--market-down');
    expect(styles).toContain('--edge-rail-width');
    expect(styles).toContain('--edge-panel-open-width');
    expect(styles).toContain('--topbar-height');
    expect(styles).toContain('.edge-panel');
    expect(styles).toContain('top: var(--topbar-height)');
    expect(styles).toContain('.ticker-edge-test');
    expect(styles).toContain('transform: translateX(0)');
    expect(styles).toContain('padding-right: 0');
    expect(styles).toContain('.feed-row');
    expect(styles).toContain('grid-auto-rows: 246px');
    expect(styles).toContain('.content-feed-card .panel-header');
    expect(styles).toContain('--feed-accent');
    expect(styles).toContain('grid-template-columns: repeat(2, minmax(0, 1fr))');
    expect(styles).toContain('.indicator-grid');
    expect(styles).toContain('grid-template-columns: repeat(6, minmax(0, 1fr))');
    expect(styles).toContain('.search-icon::before');
    expect(styles).toContain('.search-icon::after');
    expect(styles).toContain('grid-template-columns: 22px 24px minmax(0, 1fr)');
    expect(styles).toContain('.reaction-rank-row');
    expect(styles).toContain('content: none');
    expect(styles).toContain('.reaction-split-board');
    expect(styles).toContain('.rank-group-positive');
    expect(styles).toContain('.rank-group-negative');
    expect(styles).toContain('backdrop-filter: none');
    expect(styles).toContain('.sentiment-track');
    expect(styles).toContain('height: 6px');
    expect(styles).toContain('background: linear-gradient(90deg, #ff7783, var(--market-up))');
    expect(styles).toContain('background: linear-gradient(90deg, #7fb0ff, var(--market-down))');
    expect(styles).toContain('.community-graph-topline');
    expect(styles).toContain('height: 352px');
    expect(styles).toContain('.hot-stock-driver');
    expect(styles).toContain('.movement-reasons');
    expect(styles).toContain('.site-icon.youtube');
    expect(styles).toContain('.site-icon.real-icon');
    expect(styles).toContain('.site-icon img');
    expect(styles).toContain('.site-icon.naver-blog');
    expect(styles).toContain('.site-icon.naver img');
    expect(styles).toContain('.site-icon.news-macro');
    expect(styles).toContain('.site-icon.news-research');
    expect(styles).toContain('.drawer-tab-screen');
    expect(styles).toContain('.spark-area');
    expect(styles).toContain('.chart-y-axis');
    expect(styles).toContain('.edge-rail');
    expect(styles).toContain('position: fixed');
    expect(styles).not.toContain('radial-gradient(circle at 18%');
    expect(styles).not.toContain('order: -1');
  });
});
