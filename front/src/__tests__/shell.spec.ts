import { mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { describe, expect, it } from 'vitest';

import App from '../App.vue';
import dashboardSummary from '../fixtures/dashboard-summary.json';
import reactionRanking from '../fixtures/reaction-ranking.json';
import { routes } from '../router/routes';

describe('front dashboard shell', () => {
  it('defines the route inventory shell', () => {
    const routePaths = routes.map((route) => route.path);

    expect(routePaths).toEqual([
      '/',
      '/dashboard',
      '/stocks/:symbol',
      '/communities',
      '/agents',
      '/portfolio'
    ]);
    expect(routes[0]).toMatchObject({ redirect: '/dashboard' });
  });

  it('keeps dashboard mock data explicit and reviewable', () => {
    expect(dashboardSummary.productName).toBe('너나사');
    expect(dashboardSummary.confirmationNeeded).toContain('열기 지수 용어 확정');
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

    const wrapper = mount(App, {
      global: {
        plugins: [router]
      }
    });

    expect(wrapper.get('[data-testid="app-title"]').text()).toContain('YouBuyFirst');
    expect(wrapper.get('[data-testid="nav-dashboard"]').text()).toContain('대시보드');
    expect(wrapper.get('[data-testid="nav-stock"]').text()).toContain('종목 상세');
    expect(wrapper.get('[data-testid="nav-communities"]').text()).toContain('커뮤니티');
    expect(wrapper.get('[data-testid="nav-agents"]').text()).toContain('에이전트');
    expect(wrapper.get('[data-testid="nav-portfolio"]').text()).toContain('준비 중');
    expect(wrapper.text()).toContain('기획자 확인 필요');
  });
});
