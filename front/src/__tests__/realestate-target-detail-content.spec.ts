import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import RegionDetailPage from '../pages/RegionDetailPage.vue';

const mountTargetDetail = async (path = '/realestate/targets/region-seoul-mapo') => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/realestate/targets/:targetId', component: RegionDetailPage },
      { path: '/realestate/reactions', component: { template: '<div />' } }
    ]
  });

  router.push(path);
  await router.isReady();

  const wrapper = mount(RegionDetailPage, {
    global: {
      plugins: [router]
    }
  });
  await flushPromises();

  return wrapper;
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('real-estate target detail content feed', () => {
  it('uses approved target content API rows as evidence links', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      items: [
        {
          contentId: 'content-mapo-jeonse-20260612',
          sourceId: 'ddangzipgo',
          contentType: 'news',
          title: '마포 전세 매물 체감 원문 확인',
          snippet: '전세 매물 감소 체감 반응이 늘었습니다.',
          url: 'https://example.com/mapo-jeonse',
          domain: 'example.com',
          publishedAt: '2026-06-12T04:00:00Z',
          metricLabel: '댓글 42',
          statusLabel: '승인 링크',
          ingestedAt: '2026-06-12T04:10:00Z',
          dataStatus: 'ok',
          targetId: 'region-seoul-mapo',
          linkType: 'mentioned',
          confidence: 0.91,
          reviewState: 'approved'
        }
      ]
    })));
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountTargetDetail();

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/content?feed=all&limit=6');
    expect(wrapper.text()).toContain('content API 반영');
    expect(wrapper.text()).toContain('마포 전세 매물 체감 원문 확인');
    expect(wrapper.text()).toContain('땅집고');
    expect(wrapper.text()).toContain('2026-06-12 · 댓글 42');
    expect(wrapper.text()).not.toContain('원문 후보 묶음');
  });

  it('renders the embedded complex map fallback on region targets', async () => {
    const wrapper = await mountTargetDetail();

    expect(wrapper.find('[data-testid="kakao-complex-map"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="kakao-map-fallback"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="complex-map-inspector"]').text()).toContain('마포래미안푸르지오');
    expect(wrapper.text()).toContain('단지 위치 레이어');
    expect(wrapper.text()).toContain('mock fallback');
    expect(wrapper.text()).toContain('fixture fallback');
    expect(wrapper.text()).toContain('mock 좌표');
  });

  it('uses nearby complex API markers before the local fixture markers', async () => {
    const fetcher = vi.fn(async (input: string) => {
      if (input.includes('/nearby-complexes')) {
        return new Response(JSON.stringify({
          items: [
            {
              targetId: 'complex-api-marker',
              name: 'API 단지 marker',
              address: '서울 마포구 API로 일대',
              region: '서울 마포구',
              latitude: 37.551,
              longitude: 126.955,
              tone: 'up',
              price: '16.1억',
              change: '+0.44%',
              reaction: 'API 반응 요약',
              provider: 'complex_api_test',
              asOf: '2026-06-14T00:00:00Z',
              dataStatus: 'candidate',
              stale: true,
              note: 'API marker 우선 사용'
            }
          ]
        }));
      }
      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountTargetDetail();

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/nearby-complexes?limit=20');
    expect(wrapper.find('[data-testid="complex-map-inspector"]').text()).toContain('API 단지 marker');
    expect(wrapper.text()).toContain('marker API 반영');
    expect(wrapper.text()).toContain('candidate · stale');
    expect(wrapper.text()).not.toContain('마포래미안푸르지오');
  });

  it('opens a complex target detail with the same map and report frame', async () => {
    const wrapper = await mountTargetDetail('/realestate/targets/complex-mapo-raemian-prugio');

    expect(wrapper.find('.unsupported-region-state').exists()).toBe(false);
    expect(wrapper.text()).toContain('마포래미안푸르지오');
    expect(wrapper.text()).toContain('마래푸');
    expect(wrapper.text()).toContain('단지 위치 레이어');
    expect(wrapper.find('[data-testid="complex-map-inspector"]').text()).toContain('학군·역세권 언급 증가');
  });
});
