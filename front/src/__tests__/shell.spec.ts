import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { describe, expect, it } from 'vitest';

import App from '../App.vue';
import { routes } from '../router/routes';

const testDir = dirname(fileURLToPath(import.meta.url));

const mountAt = async (path: string) => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes
  });

  router.push(path);
  await router.isReady();

  return mount(App, {
    global: {
      plugins: [router]
    }
  });
};

describe('front dashboard shell', () => {
  it('defines the route inventory shell', () => {
    const routePaths = routes.map((route) => route.path);

    expect(routePaths).toEqual([
      '/',
      '/dashboard',
      '/realestate/map',
      '/newsroom',
      '/realestate/reactions',
      '/realestate/targets/:symbol',
      '/stocks',
      '/stocks/:symbol',
      '/communities',
      '/indicators',
      '/indicators/:category',
      '/agents',
      '/portfolio'
    ]);
    expect(routes[0]).toMatchObject({ redirect: '/dashboard' });
    expect(routes.find((route) => route.path === '/agents')).toMatchObject({
      redirect: { path: '/realestate/reactions', query: { view: 'agents' } }
    });
  });

  it('declares an inline favicon so browser checks do not request /favicon.ico', () => {
    const indexHtml = readFileSync(resolve(testDir, '../../index.html'), 'utf8');

    expect(indexHtml).toContain('rel="icon"');
    expect(indexHtml).toContain('data:image/svg+xml');
  });

  it('renders the dashboard briefing and shell chrome', async () => {
    const wrapper = await mountAt('/dashboard');

    expect(wrapper.get('[data-testid="app-title"]').text()).toContain('YouBuyFirst');
    expect(wrapper.get('[data-testid="app-title"]').attributes('href')).toBe('/dashboard');
    expect(wrapper.get('[data-testid="nav-dashboard"]').text()).toContain('대시보드');
    expect(wrapper.get('[data-testid="nav-map"]').text()).toContain('지도');
    expect(wrapper.get('[data-testid="nav-newsroom"]').text()).toContain('뉴스룸');
    expect(wrapper.findAll('.nav-submenu a')).toHaveLength(4);
    expect(wrapper.findAll('.nav-submenu a.active')).toHaveLength(0);
    expect(wrapper.get('[data-testid="nav-region-reactions"]').text()).toContain('지역 반응');
    expect(wrapper.get('[data-testid="nav-indicators"]').text()).toContain('주요 지표');
    expect(wrapper.find('[data-testid="nav-agents"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="nav-portfolio"]').text()).toContain('관심 지역');
    expect(wrapper.find('.topbar .live-ticker').exists()).toBe(true);
    expect(wrapper.text()).toContain('부동산 투기 과열 지표');
    expect(wrapper.text()).toContain('73점');
    expect(wrapper.text()).toContain('어제 대비 +6.4%');
    expect(wrapper.text()).toContain('가격·전세 동반');
    expect(wrapper.text()).toContain('핵심 지역별 상승률');
    expect(wrapper.text()).toContain('주월6개월년');
    expect(wrapper.text()).not.toContain('유사 과거 흐름 비교');
    expect(wrapper.find('.edge-rail').exists()).toBe(true);
    expect(wrapper.find('.edge-panel').exists()).toBe(true);
    await wrapper.find('.rail-expand').trigger('click');
    expect(wrapper.find('.app-shell').classes()).toContain('edge-panel-open');
    await wrapper.find('.rail-expand').trigger('click');
    expect(wrapper.find('.app-shell').classes()).not.toContain('edge-panel-open');
  });

  it('dismisses the newsroom submenu after a newsroom navigation click', async () => {
    const wrapper = await mountAt('/dashboard');

    await wrapper.get('[data-testid="nav-newsroom"]').trigger('click');
    expect(wrapper.find('.nav-menu-parent').classes()).toContain('menu-dismissed');

    await wrapper.find('.nav-menu-parent').trigger('pointerleave');
    expect(wrapper.find('.nav-menu-parent').classes()).not.toContain('menu-dismissed');

    await wrapper.findAll('.nav-submenu a')[2].trigger('click');
    expect(wrapper.find('.nav-menu-parent').classes()).toContain('menu-dismissed');
  });

  it('renders the core product pages with the expanded planning content', async () => {
    const reactions = await mountAt('/realestate/reactions');
    expect(reactions.text()).toContain('지역 반응');
    expect(reactions.text()).toContain('지역 언급량 TOP 6');
    expect(reactions.text()).toContain('단지군 관심 TOP 6');
    expect(reactions.text()).toContain('지역·단지 순위, 급증 신호');
    expect(reactions.text()).toContain('정렬 기준');
    expect(reactions.text()).toContain('커뮤니티별 언급 급증 지역');
    expect(reactions.text()).toContain('모의 에이전트 판단 기록');
    expect(reactions.text()).not.toContain('커뮤니티별 언급 급증과 반응 비율');
    expect(reactions.text()).not.toContain('커뮤니티 반응과 공식 지표 비교 그래프');
    expect(reactions.findAll('.region-ranking-row').length).toBe(12);

    const legacyStocks = await mountAt('/stocks');
    expect(legacyStocks.text()).toContain('지역 반응');

    const stock = await mountAt('/realestate/targets/SEOUL-MAPO');
    expect(stock.text()).toContain('지역 반응 목록으로');
    expect(stock.text()).toContain('마포구 아파트');
    expect(stock.text()).toContain('전세 매물 체감과 학군 키워드');
    expect(stock.text()).toContain('지역 한줄 브리핑');
    expect(stock.text()).toContain('실거래가 흐름');
    expect(stock.text()).toContain('전세가율');
    expect(stock.text()).toContain('공급 신호');
    expect(stock.text()).toContain('시간대별 변화');
    expect(stock.text()).toContain('커뮤니티 반응 추이');
    expect(stock.text()).toContain('신호 신뢰도');
    expect(stock.findAll('.vertical-timeline article')).toHaveLength(4);
    expect(stock.findAll('.evidence-list a').length).toBeGreaterThanOrEqual(3);

    const otherTarget = await mountAt('/realestate/targets/DONGTAN-STATION');
    expect(otherTarget.text()).toContain('동탄역권');
    expect(otherTarget.text()).toContain('DONGTAN-STATION');
    expect(otherTarget.text()).toContain('GTX 기대와 입주 물량 우려');
    expect(otherTarget.text()).toContain('전세수급지수');

    const unsupportedTarget = await mountAt('/realestate/targets/SEONGSU-DONG');
    expect(unsupportedTarget.find('.unsupported-region-state').exists()).toBe(true);
    expect(unsupportedTarget.text()).toContain('SEONGSU-DONG');
    expect(unsupportedTarget.find('.region-reaction-card').exists()).toBe(false);

    const communities = await mountAt('/communities');
    expect(communities.text()).toContain('지역 반응');
    expect(communities.text()).toContain('커뮤니티별 언급 급증 지역');
    expect(communities.text()).not.toContain('커뮤니티별 반응 비교');
    expect(communities.text()).not.toContain('커뮤니티별 언급 급증과 반응 비율');
    expect(communities.text()).toContain('인기글·댓글·지역 블로그 레이어');
    expect(communities.text()).not.toContain('지역별 반응 선행성 실험');
    expect(communities.text()).toContain('모의 에이전트');
    expect(communities.text()).toContain('모의 에이전트 판단 기록');
    expect(communities.text()).toContain('판단 입력값');
    expect(communities.text()).toContain('전략 버전과 판단 key 기준');

    const newsroomAll = await mountAt('/newsroom');
    expect(newsroomAll.text()).toContain('뉴스룸');
    expect(newsroomAll.findAll('.nav-submenu a.active')).toHaveLength(0);
    expect(newsroomAll.text()).toContain('블로그와 커뮤니티 링크');
    expect(newsroomAll.find('.newsroom-switch').exists()).toBe(false);
    expect(newsroomAll.findAll('.newsroom-overview-card')).toHaveLength(4);
    for (const card of newsroomAll.findAll('.newsroom-overview-card')) {
      expect(card.findAll('.newsroom-row')).toHaveLength(8);
    }
    expect(newsroomAll.text()).toContain('실시간 뉴스');
    expect(newsroomAll.text()).toContain('정책·통계 리포트');
    expect(newsroomAll.text()).toContain('부동산 영상 새 글');
    expect(newsroomAll.text()).toContain('블로그와 커뮤니티 링크');
    expect(newsroomAll.text()).toContain('뉴스만 몰아보기');
    expect(newsroomAll.text()).toContain('원문 링크만 몰아보기');

    const newsroom = await mountAt('/newsroom?feed=videos&page=2');
    expect(newsroom.text()).toContain('영상');
    expect(newsroom.text()).toContain('조회 7.4만');
    expect(newsroom.find('.newsroom-pager').exists()).toBe(true);
    expect(newsroom.findAll('.nav-submenu a.active')).toHaveLength(1);
    expect(newsroom.find('.nav-submenu a.active').text()).toContain('영상');

    const indicators = await mountAt('/indicators');
    expect(indicators.text()).toContain('가격·거래량, 공급·수급, 수요·심리, 거시·금융 지표');
    expect(indicators.text()).toContain('지표와 반응이 엇갈린 지역');
    expect(indicators.text()).toContain('지표별 반응 히트맵');
    expect(indicators.text()).toContain('지표별 데이터 신선도');
    expect(indicators.text()).toContain('주요 일정');

    expect(indicators.text()).toContain('지역별 지표 방향');
    expect(indicators.text()).toContain('지표 묶음별 관찰 포인트');
    expect(indicators.text()).toContain('가격 및 거래량');
    expect(indicators.text()).toContain('공급 및 수급');
    expect(indicators.text()).toContain('수요 및 심리');
    expect(indicators.text()).toContain('거시경제 및 금융');

    const indicatorDetail = await mountAt('/indicators/price-transaction');
    expect(indicatorDetail.text()).toContain('가격 및 거래량 상세 지표');
    expect(indicatorDetail.text()).toContain('전체 핵심 보기');

    const agents = await mountAt('/agents');
    expect(agents.text()).toContain('지역 반응');
    expect(agents.text()).toContain('모의 에이전트 판단 기록');
    expect(agents.text()).toContain('전략 버전과 판단 key 기준');
    expect(agents.text()).toContain('최근 판단 로그');
    expect(agents.text()).toContain('판단 입력값');
    expect(agents.text()).toContain('판단 key');

    const portfolio = await mountAt('/portfolio');
    expect(portfolio.text()).toContain('관심 지역');
    expect(portfolio.text()).toContain('부동산 자문 아님');
    expect(portfolio.text()).toContain('커뮤니티 원문 · 별칭 DB 연결 준비');
    expect(portfolio.text()).toContain('원문/공공데이터 후보');
    expect(portfolio.text()).toContain('민감정보 마스킹');
    expect(portfolio.text()).toContain('관찰 로그');
    expect(portfolio.text()).toContain('알림 후 복기');
  });

  it('opens a report panel when a map region is selected', async () => {
    const wrapper = await mountAt('/realestate/map');

    expect(wrapper.text()).toContain('전국 지역 흐름 지도');
    expect(wrapper.find('[data-testid="map-report-panel"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="realestate-map-layout"]').classes()).toContain('centered');

    await wrapper.get('[data-testid="map-target-seoul"]').trigger('click');

    expect(wrapper.find('[data-testid="realestate-map-layout"]').classes()).toContain('split');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('서울');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('가격 흐름');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('커뮤니티 반응');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('언급량 급증');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('핵심 쟁점');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('전세 매물 감소');

    await wrapper.get('[data-testid="close-map-report"]').trigger('click');

    expect(wrapper.find('[data-testid="map-report-panel"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="realestate-map-layout"]').classes()).toContain('centered');
  });

  it('keeps the visual system and advice guardrails explicit', async () => {
    const wrapper = await mountAt('/dashboard');
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toContain('Pretendard');
    expect(styles).toContain('--surface');
    expect(styles).toContain('--market-up');
    expect(styles).toContain('--market-down');
    expect(styles).toContain('.realestate-map-layout.centered,\n  .realestate-map-layout.split');
    expect(styles).toContain('.region-hero');
    expect(styles).toContain('.event-chain-flow');
    expect(styles).toContain('.community-table');
    expect(styles).toContain('.theme-heatmap');
    expect(styles).toContain('.decision-log-list');
    expect(styles).toContain('.portfolio-table');
    expect(styles).toContain('.account-sync-grid');
    expect(wrapper.text()).toContain('실제 매수·매도 지시나 개인화 부동산 자문을 제공하지 않습니다');
    expect(wrapper.text()).not.toContain('매수 추천');
    expect(wrapper.text()).not.toContain('매도 추천');
    expect(wrapper.text()).not.toContain('수익 보장');
    expect(wrapper.text()).not.toContain('진입하세요');
    expect(wrapper.text()).not.toContain('시그널 확정');
  });
});
