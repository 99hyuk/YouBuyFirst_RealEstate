import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import WatchlistPage from '../pages/WatchlistPage.vue';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('real-estate watchlist candidates page', () => {
  it('shows reaction ranking rows as watch candidates without mock watchlist copy', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({
      items: [
        {
          rank: 1,
          targetId: 'region-seoul',
          targetType: 'region',
          displayName: '서울특별시',
          mentionCount: 18,
          mentionDeltaPct: 100,
          reactionDirectionRatio: { expectation: 0.06, concern: 0.06, neutral: 0.88 },
          heatScore: 100,
          confidence: 0.87,
          sourceCount: 1,
          sourceSkew: 1,
          coverageStatus: 'source_skewed',
          stale: false,
          issueMix: [
            { issueKey: 'jeonse', label: '전세', share: 0.06, direction: 'concern', summary: '전세 우려', confidence: 0.78 }
          ]
        }
      ]
    }))));

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/realestate/watchlist', component: WatchlistPage },
        { path: '/realestate/targets/:targetId', component: { template: '<div />' } },
        { path: '/realestate/reactions', component: { template: '<div />' } }
      ]
    });
    router.push('/realestate/watchlist');
    await router.isReady();

    const wrapper = mount(WatchlistPage, {
      global: {
        plugins: [router]
      }
    });
    await flushPromises();

    expect(wrapper.text()).toContain('reaction API 반영');
    expect(wrapper.text()).toContain('관심 후보1곳');
    expect(wrapper.text()).toContain('서울특별시');
    expect(wrapper.text()).toContain('+100%');
    expect(wrapper.text()).toContain('전세');
    expect(wrapper.text()).not.toContain('mock watchlist');
    expect(wrapper.text()).not.toContain('원문 묶음 선택 mock');
  });

  it('keeps empty API results as insufficient instead of filling fixture rows', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ items: [] }))));

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/realestate/watchlist', component: WatchlistPage },
        { path: '/realestate/reactions', component: { template: '<div />' } }
      ]
    });
    router.push('/realestate/watchlist');
    await router.isReady();

    const wrapper = mount(WatchlistPage, {
      global: {
        plugins: [router]
      }
    });
    await flushPromises();

    expect(wrapper.text()).toContain('수집 전/insufficient');
    expect(wrapper.findAll('.watchlist-target-row')).toHaveLength(0);
    expect(wrapper.text()).not.toContain('마포구 아파트');
  });
});
