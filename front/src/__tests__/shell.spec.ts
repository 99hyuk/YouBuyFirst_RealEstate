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
      '/newsroom',
      '/stocks',
      '/stocks/:symbol',
      '/communities',
      '/indicators',
      '/agents',
      '/portfolio'
    ]);
    expect(routes[0]).toMatchObject({ redirect: '/dashboard' });
    expect(routes.find((route) => route.path === '/agents')).toMatchObject({
      redirect: { path: '/communities', query: { view: 'agents' } }
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
    expect(wrapper.get('[data-testid="nav-newsroom"]').text()).toContain('뉴스룸');
    expect(wrapper.findAll('.nav-submenu a')).toHaveLength(4);
    expect(wrapper.findAll('.nav-submenu a.active')).toHaveLength(0);
    expect(wrapper.get('[data-testid="nav-stock"]').text()).toContain('종목');
    expect(wrapper.get('[data-testid="nav-communities"]').text()).toContain('인간 지표');
    expect(wrapper.get('[data-testid="nav-indicators"]').text()).toContain('주요 지표');
    expect(wrapper.find('[data-testid="nav-agents"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="nav-portfolio"]').text()).toContain('내 포트폴리오');
    expect(wrapper.find('.topbar .live-ticker').exists()).toBe(true);
    expect(wrapper.text()).toContain('커뮤니티 지표 비교');
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
    const stocks = await mountAt('/stocks');
    expect(stocks.text()).toContain('종목 거래량 순위');
    expect(stocks.text()).toContain('국장 거래량 TOP 10');
    expect(stocks.text()).toContain('해외 거래량 TOP 10');
    expect(stocks.text()).toContain('목록에서 종목을 눌러 상세로 이동');
    expect(stocks.text()).toContain('정렬 기준');
    expect(stocks.findAll('.market-ranking-row').length).toBe(20);

    const stock = await mountAt('/stocks/005930');
    expect(stock.text()).toContain('종목 랭킹으로');
    expect(stock.text()).toContain('HBM 붙었다고 삼전이 엔비디아');
    expect(stock.text()).toContain('오늘의 한줄평');
    expect(stock.text()).toContain('실적표 없으면 행복회로 압수');
    expect(stock.text()).toContain('실거래 판단 근거 아님');
    expect(stock.text()).toContain('국내/해외 TradingView 위젯 비교');
    expect(stock.text()).toContain('KRX:005930');
    expect(stock.text()).toContain('NASDAQ:NVDA');
    expect(stock.text()).toContain('국내주식 위젯 테스트');
    expect(stock.text()).toContain('해외주식 위젯 테스트');
    expect(stock.text()).toContain('거래량');
    expect(stock.text()).toContain('quote snapshot');
    expect(stock.text()).toContain('TradingView 공개 embed 위젯');
    expect(stock.text()).toContain('어제와 달라진 점');
    expect(stock.text()).toContain('반응 키워드');
    expect(stock.text()).toContain('시간대별 변화');
    expect(stock.text()).toContain('커뮤니티 반응 추이');
    expect(stock.text()).toContain('신호 신뢰도');
    expect(stock.findAll('.vertical-timeline article')).toHaveLength(5);
    expect(stock.findAll('.evidence-list a').length).toBeGreaterThanOrEqual(5);

    const overseasStock = await mountAt('/stocks/NVDA');
    expect(overseasStock.text()).toContain('NVIDIA');
    expect(overseasStock.text()).toContain('NASDAQ:NVDA');
    expect(overseasStock.text()).toContain('$924.80');
    expect(overseasStock.text()).toContain('AI 왕관');

    const communities = await mountAt('/communities');
    expect(communities.text()).toContain('인간 지표');
    expect(communities.text()).toContain('수집 상태');
    expect(communities.text()).toContain('커뮤니티별 언급 급증 종목');
    expect(communities.text()).toContain('커뮤니티별 반응 비교');
    expect(communities.text()).toContain('커뮤니티별 언급 급증과 반응 비율');
    expect(communities.text()).toContain('인기글·개념글 레이어');
    expect(communities.text()).toContain('커뮤니티별 성과 실험');
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
    expect(newsroomAll.text()).toContain('애널리스트 리포트');
    expect(newsroomAll.text()).toContain('증권 영상 새 글');
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
    expect(indicators.text()).toContain('시장 지표 자체보다 커뮤니티 반응과 엇갈리는 구간');
    expect(indicators.text()).toContain('가격과 반응이 엇갈린 종목');
    expect(indicators.text()).toContain('섹터·테마별 반응 히트맵');
    expect(indicators.text()).toContain('지표별 데이터 신선도');
    expect(indicators.text()).toContain('주요 일정');

    expect(indicators.text()).toContain('국장 섹터 방향');
    expect(indicators.text()).toContain('미장 섹터 방향');

    const agents = await mountAt('/agents');
    expect(agents.text()).toContain('인간 지표');
    expect(agents.text()).toContain('모의 에이전트 판단 기록');
    expect(agents.text()).toContain('전략 버전과 판단 key 기준');
    expect(agents.text()).toContain('최근 판단 로그');
    expect(agents.text()).toContain('판단 입력값');
    expect(agents.text()).toContain('판단 key');

    const portfolio = await mountAt('/portfolio');
    expect(portfolio.text()).toContain('내 포트폴리오');
    expect(portfolio.text()).toContain('실거래 아님');
    expect(portfolio.text()).toContain('자산 OCR · 주식 계좌 연결 준비');
    expect(portfolio.text()).toContain('OCR/거래내역 후보');
    expect(portfolio.text()).toContain('민감정보 마스킹');
    expect(portfolio.text()).toContain('원장 내역');
    expect(portfolio.text()).toContain('체결 후 복기');
  });

  it('keeps the visual system and advice guardrails explicit', async () => {
    const wrapper = await mountAt('/dashboard');
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toContain('Pretendard');
    expect(styles).toContain('--surface');
    expect(styles).toContain('--market-up');
    expect(styles).toContain('--market-down');
    expect(styles).toContain('.stock-hero');
    expect(styles).toContain('.event-chain-flow');
    expect(styles).toContain('.community-table');
    expect(styles).toContain('.theme-heatmap');
    expect(styles).toContain('.decision-log-list');
    expect(styles).toContain('.portfolio-table');
    expect(styles).toContain('.account-sync-grid');
    expect(wrapper.text()).toContain('실제 거래 지시나 개인화 투자 권유를 제공하지 않습니다');
    expect(wrapper.text()).not.toContain('매수 추천');
    expect(wrapper.text()).not.toContain('매도 추천');
    expect(wrapper.text()).not.toContain('수익 보장');
    expect(wrapper.text()).not.toContain('진입하세요');
    expect(wrapper.text()).not.toContain('시그널 확정');
  });
});
