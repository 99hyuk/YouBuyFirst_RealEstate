import { mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { describe, expect, it } from 'vitest';

import WatchlistPage from '../pages/WatchlistPage.vue';
import { routes } from '../router/routes';

describe('real-estate mypage', () => {
  it('shows a login-based personal board without fake saved targets', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/realestate/mypage', component: WatchlistPage },
        { path: '/realestate/map', component: { template: '<div />' } }
      ]
    });
    router.push('/realestate/mypage');
    await router.isReady();

    const wrapper = mount(WatchlistPage, {
      global: {
        plugins: [router]
      }
    });

    expect(wrapper.text()).toContain('내 부동산 관찰 보드');
    expect(wrapper.text()).toContain('사용자가 저장한 지역을 관리하고');
    expect(wrapper.text()).toContain('저장된 지역이나 단지가 아직 없습니다');
    expect(wrapper.text()).toContain('지난 방문 이후 바뀐 것');
    expect(wrapper.text()).toContain('내 알림 조건');
    expect(wrapper.text()).toContain('지역별 관찰 메모');
    expect(wrapper.text()).toContain('저장 지역 비교');
    expect(wrapper.text()).toContain('알림 조건 준비 중');
    expect(wrapper.text()).toContain('실거주');
    expect(wrapper.text()).toContain('청약 일정 체크');
    expect(wrapper.text()).not.toContain('관심 후보');
    expect(wrapper.text()).not.toContain('지역 반응 TOP10');
    expect(wrapper.text()).not.toContain('커뮤니티 원문');
    expect(wrapper.text()).not.toContain('언급 변화');
    expect(wrapper.text()).not.toContain('mock watchlist');
  });

  it('keeps the legacy watchlist path by redirecting to mypage', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes
    });

    router.push('/realestate/watchlist');
    await router.isReady();

    expect(router.currentRoute.value.path).toBe('/realestate/mypage');
  });
});
