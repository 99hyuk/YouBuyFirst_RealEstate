import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';

import App from '../App.vue';
import { routes } from '../router/routes';

const testDir = dirname(fileURLToPath(import.meta.url));
const mapTargetsFixture = JSON.parse(
  readFileSync(resolve(testDir, '../fixtures/realestate-map-targets.json'), 'utf8')
) as {
  targets: { id: string; targetId: string; name: string; regionCode: string }[];
};
const municipalityTopology = JSON.parse(
  readFileSync(resolve(testDir, '../fixtures/skorea-municipalities-2018-topo-simple.json'), 'utf8')
) as {
  objects: {
    skorea_municipalities_2018_geo: {
      geometries: { properties: { code: string } }[];
    };
  };
};
const municipalityTopologyJson = readFileSync(
  resolve(testDir, '../fixtures/skorea-municipalities-2018-topo-simple.json'),
  'utf8'
);
const nativeFetch = globalThis.fetch;
const municipalityCountByRegionCode = municipalityTopology.objects.skorea_municipalities_2018_geo.geometries.reduce(
  (counts, geometry) => {
    const regionCode = geometry.properties.code.slice(0, 2);
    counts.set(regionCode, (counts.get(regionCode) ?? 0) + 1);

    return counts;
  },
  new Map<string, number>()
);

beforeAll(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);

      if (url.includes('skorea-municipalities-2018-topo-simple')) {
        return new Response(municipalityTopologyJson, {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      if (url.includes('/api/realestate/map/layers') && url.includes('layerType=sigungu') && url.includes('region-daejeon')) {
        return new Response(JSON.stringify({
          layerType: 'sigungu',
          parentTargetId: 'region-daejeon',
          asOf: '2026-06-15T00:00:00Z',
          sourceLabel: 'map_layer_snapshots',
          mapDataSource: 'KOSTAT 2018',
          dataStatus: 'ok',
          stale: false,
          periods: ['week', 'month', 'halfYear'],
          targets: [
            {
              targetId: 'region-daejeon-yuseong',
              targetType: 'region',
              displayName: '대전 유성구',
              regionLevel: 'sigungu',
              regionCode: '25040',
              parentTargetId: 'region-daejeon',
              periods: {
                month: {
                  changePct: 0.31,
                  sampleCount: 42,
                  confidence: 77,
                  asOf: '2026-06-15T00:00:00Z',
                  provider: 'reb_stat',
                  sourceLabel: 'map_layer_snapshots',
                  dataStatus: 'ok',
                  stale: false
                }
              }
            }
          ]
        }), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      return nativeFetch(input, init);
    })
  );
});

afterAll(() => {
  vi.unstubAllGlobals();
});

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
      '/realestate/map/:regionId',
      '/realestate/complexes',
      '/newsroom',
      '/realestate/reactions',
      '/realestate/targets/:targetId',
      '/indicators',
      '/indicators/:category',
      '/realestate/watchlist'
    ]);
    expect(routes[0]).toMatchObject({ redirect: '/dashboard' });
    expect(routePaths).not.toContain('/communities');
    expect(routePaths).not.toContain('/agents');
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
    expect(wrapper.get('[data-testid="nav-watchlist"]').text()).toContain('관심 지역');
    expect(wrapper.get('[data-testid="nav-watchlist"]').attributes('href')).toBe('/realestate/watchlist');
    expect(wrapper.find('.topbar .live-strip').exists()).toBe(true);
    expect(wrapper.find('.brand-lockup > strong').text()).toBe('BETA');
    expect(wrapper.find('.topbar').text()).not.toContain('MOCK');
    expect(wrapper.find('.topbar-live-strip').text()).not.toContain('mock data');
    expect(wrapper.text()).toContain('부동산 투기 과열 지표');
    expect(wrapper.text()).toContain('0점');
    expect(wrapper.text()).toContain('수집 전 · 최근 24시간 최신');
    expect(wrapper.text()).toContain('반응 수집 대기');
    expect(wrapper.text()).toContain('핵심 지역별 상승률');
    expect(wrapper.text()).toContain('map layer 확인 중');
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
    await flushPromises();

    expect(reactions.text()).toContain('지역 반응');
    expect(reactions.text()).toContain('지역 언급량 TOP 10');
    expect(reactions.text()).toContain('단지군 관심 TOP 10');
    expect(reactions.text()).toContain('전체 TOP10');
    expect(reactions.text()).toContain('서울 TOP10');
    expect(reactions.text()).toContain('경기 TOP10');
    expect(reactions.text()).toContain('대전 TOP10');
    expect(reactions.text()).toContain('지역·단지 순위, 급증 신호');
    expect(reactions.text()).toContain('정렬 기준');
    expect(reactions.text()).toContain('커뮤니티 언급 급증 지역');
    expect(reactions.text()).toContain('언급 급증, 기대 우세, 우려 증가, 정책 민감을 한 줄로 통합');
    expect(reactions.text()).not.toContain('커뮤니티별 언급 급증 지역');
    expect(reactions.text()).toContain('모의 에이전트 판단 기록');
    expect(reactions.text()).not.toContain('커뮤니티별 언급 급증과 반응 비율');
    expect(reactions.text()).not.toContain('커뮤니티 반응과 공식 지표 비교 그래프');
    expect(reactions.findAll('.region-ranking-row').length).toBe(20);
    await reactions.findAll('.region-scope-filter button').find((button) => button.text() === '서울 TOP10')?.trigger('click');
    await flushPromises();
    expect(reactions.text()).toContain('서울 지역 언급량 TOP 10');
    expect(reactions.findAll('.region-ranking-row').length).toBe(6);
    const fetchCalls = (globalThis.fetch as unknown as { mock: { calls: [RequestInfo | URL][] } }).mock.calls;
    const reactionRankingRequests = fetchCalls.map(([input]) => String(input));
    expect(reactionRankingRequests).toContain('/api/realestate/reactions/rankings?type=region&windowMinutes=1440&limit=10&parentTargetId=region-seoul');
    expect(reactionRankingRequests).toContain('/api/realestate/reactions/rankings?type=complex&windowMinutes=1440&limit=10&parentTargetId=region-seoul');

    const target = await mountAt('/realestate/targets/region-seoul-mapo');
    expect(target.text()).toContain('지역 반응 목록으로');
    expect(target.text()).toContain('마포구 아파트');
    expect(target.text()).toContain('전세 매물 체감과 학군 키워드');
    expect(target.text()).toContain('지역 한줄 브리핑');
    expect(target.text()).toContain('실거래가 흐름');
    expect(target.text()).toContain('전세가율');
    expect(target.text()).toContain('공급 신호');
    expect(target.text()).toContain('단지 위치 레이어');
    expect(target.text()).toContain('mock 좌표');
    expect(target.text()).toContain('시간대별 변화');
    expect(target.text()).toContain('커뮤니티 반응 추이');
    expect(target.text()).toContain('신호 신뢰도');
    expect(target.findAll('.vertical-timeline article')).toHaveLength(4);
    expect(target.findAll('.evidence-list a').length).toBeGreaterThanOrEqual(3);

    const complexTarget = await mountAt('/realestate/targets/complex-mapo-raemian-prugio');
    expect(complexTarget.find('.unsupported-region-state').exists()).toBe(false);
    expect(complexTarget.text()).toContain('마포래미안푸르지오');
    expect(complexTarget.text()).toContain('마래푸');
    expect(complexTarget.text()).toContain('단지 위치 레이어');
    expect(complexTarget.find('[data-testid="complex-map-inspector"]').text()).toContain('마포래미안푸르지오');

    const otherTarget = await mountAt('/realestate/targets/living-area-gyeonggi-dongtan-station');
    expect(otherTarget.text()).toContain('동탄역권');
    expect(otherTarget.text()).toContain('living-area-gyeonggi-dongtan-station');
    expect(otherTarget.text()).toContain('GTX 기대와 입주 물량 우려');
    expect(otherTarget.text()).toContain('전세수급지수');

    const unsupportedTarget = await mountAt('/realestate/targets/living-area-seoul-seongsu');
    expect(unsupportedTarget.find('.unsupported-region-state').exists()).toBe(true);
    expect(unsupportedTarget.text()).toContain('living-area-seoul-seongsu');
    expect(unsupportedTarget.find('.region-reaction-card').exists()).toBe(false);

    const newsroomAll = await mountAt('/newsroom');
    await flushPromises();

    expect(newsroomAll.text()).toContain('뉴스룸');
    expect(newsroomAll.findAll('.nav-submenu a.active')).toHaveLength(0);
    expect(newsroomAll.text()).toContain('블로그와 커뮤니티 링크');
    expect(newsroomAll.find('.newsroom-switch').exists()).toBe(false);
    expect(newsroomAll.findAll('.newsroom-overview-card')).toHaveLength(4);
    for (const card of newsroomAll.findAll('.newsroom-overview-card')) {
      expect(card.findAll('.newsroom-row')).toHaveLength(0);
      expect(card.find('.newsroom-empty-state').exists()).toBe(true);
    }
    expect(newsroomAll.text()).toContain('content API 오류');
    expect(newsroomAll.text()).toContain('콘텐츠 API를 불러오지 못했습니다');
    expect(newsroomAll.text()).toContain('실시간 뉴스');
    expect(newsroomAll.text()).toContain('정책·통계 리포트');
    expect(newsroomAll.text()).toContain('부동산 영상 새 글');
    expect(newsroomAll.text()).toContain('블로그와 커뮤니티 링크');
    expect(newsroomAll.text()).toContain('뉴스만 몰아보기');
    expect(newsroomAll.text()).toContain('원문 링크만 몰아보기');

    const newsroom = await mountAt('/newsroom?feed=videos&page=2');
    await flushPromises();

    expect(newsroom.text()).toContain('영상');
    expect(newsroom.text()).toContain('콘텐츠 API를 불러오지 못했습니다');
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

    const watchlist = await mountAt('/realestate/watchlist');
    expect(watchlist.text()).toContain('관심 지역');
    expect(watchlist.text()).toContain('부동산 자문 아님');
    expect(watchlist.text()).toContain('reaction API 확인 중');
    expect(watchlist.text()).not.toContain('mock watchlist');
    expect(watchlist.text()).not.toContain('원문 묶음 선택 mock');
    expect(watchlist.text()).toContain('커뮤니티 원문 · 별칭 DB 연결 준비');
    expect(watchlist.text()).toContain('원문/공공데이터 후보');
    expect(watchlist.text()).toContain('민감정보 마스킹');
    expect(watchlist.text()).toContain('관찰 로그');
    expect(watchlist.text()).toContain('알림 후 복기');
  });

  it('opens a full regional drilldown map from the national map', async () => {
    const wrapper = await mountAt('/realestate/map');

    expect(wrapper.text()).toContain('전국 지역 흐름 지도');
    expect(wrapper.find('[data-testid="map-report-panel"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="realestate-map-layout"]').classes()).toContain('centered');

    await wrapper.get('[data-testid="map-target-daejeon"]').trigger('click');
    await flushPromises();

    expect(wrapper.vm.$route.path).toBe('/realestate/map/region-daejeon');
    expect(wrapper.text()).toContain('대전 상세 흐름 지도');
    expect(wrapper.text()).toContain('전국 지도로 돌아가기');
    expect(wrapper.findAll('[data-testid^="subregion-shape-"]')).toHaveLength(5);
    expect(wrapper.findAll('.subregion-labels text')).toHaveLength(0);
    expect(wrapper.text()).toContain('동구');
    expect(wrapper.text()).toContain('유성구');
    expect(wrapper.get('[data-testid="subregion-layer-status"]').text()).toContain('reb_stat · ok · fresh · 2026-06-15T00:00:00Z');

    await wrapper.get('[data-testid="subregion-button-25040"]').trigger('click');

    expect(wrapper.find('[data-testid="realestate-map-layout"]').classes()).toContain('split');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('유성구');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('가격 흐름');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('커뮤니티 언급');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('언급량 급증');
    expect(wrapper.get('[data-testid="map-report-panel"]').text()).toContain('핵심 쟁점');

    await wrapper.get('[data-testid="close-map-report"]').trigger('click');

    expect(wrapper.find('[data-testid="map-report-panel"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="realestate-map-layout"]').classes()).toContain('centered');
  }, 15000);

  it('renders every province as a municipal drilldown map', async () => {
    expect(mapTargetsFixture.targets).toHaveLength(17);

    for (const target of mapTargetsFixture.targets) {
      const expectedCount = municipalityCountByRegionCode.get(target.regionCode);
      const wrapper = await mountAt(`/realestate/map/${target.targetId}`);
      await flushPromises();

      if (!expectedCount) {
        throw new Error(`No municipality fixture rows for ${target.name}`);
      }

      expect(expectedCount).toBeGreaterThan(0);
      expect(wrapper.text()).toContain(`${target.name} 상세 흐름 지도`);
      expect(wrapper.findAll('[data-testid^="subregion-shape-"]')).toHaveLength(expectedCount);
    }
  }, 20000);

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
    expect(styles).toContain('.watchlist-table');
    expect(styles).toContain('.account-sync-grid');
    expect(wrapper.text()).toContain('실제 매수·매도 지시나 개인화 부동산 자문을 제공하지 않습니다');
    expect(wrapper.text()).not.toContain('매수 추천');
    expect(wrapper.text()).not.toContain('매도 추천');
    expect(wrapper.text()).not.toContain('수익 보장');
    expect(wrapper.text()).not.toContain('진입하세요');
    expect(wrapper.text()).not.toContain('시그널 확정');
  });
});
