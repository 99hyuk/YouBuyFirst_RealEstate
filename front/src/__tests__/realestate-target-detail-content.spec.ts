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
});
