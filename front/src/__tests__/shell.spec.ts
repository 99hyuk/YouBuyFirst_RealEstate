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

      if (url.includes('/api/realestate/map/layers') && url.includes('layerType=sido')) {
        return new Response(JSON.stringify({
          layerType: 'sido',
          asOf: '2026-06-18T00:00:00Z',
          sourceLabel: 'map_layer_snapshots',
          mapDataSource: 'KOSTAT 2018',
          dataStatus: 'ok',
          stale: false,
          periods: ['week', 'month', 'quarter', 'halfYear', 'year'],
          targets: [
            {
              targetId: 'region-seoul',
              targetType: 'region',
              displayName: '서울',
              regionLevel: 'sido',
              regionCode: '11',
              periods: {
                week: {
                  changePct: 0.12,
                  sampleCount: 2,
                  confidence: 1,
                  asOf: '2026-06-18T00:00:00Z',
                  provider: 'reb',
                  sourceLabel: 'map_layer_snapshots',
                  dataStatus: 'ok',
                  stale: false
                },
                month: {
                  changePct: -0.08,
                  sampleCount: 2,
                  confidence: 1,
                  asOf: '2026-05-01T00:00:00Z',
                  provider: 'reb',
                  sourceLabel: 'map_layer_snapshots',
                  dataStatus: 'ok',
                  stale: false
                }
              }
            },
            {
              targetId: 'region-gwangju',
              targetType: 'region',
              displayName: '광주',
              regionLevel: 'sido',
              regionCode: '24',
              periods: {
                week: {
                  changePct: -0.42,
                  sampleCount: 2,
                  confidence: 1,
                  asOf: '2026-06-18T00:00:00Z',
                  provider: 'reb',
                  sourceLabel: 'map_layer_snapshots',
                  dataStatus: 'ok',
                  stale: false
                },
                month: {
                  changePct: -0.61,
                  sampleCount: 2,
                  confidence: 1,
                  asOf: '2026-05-01T00:00:00Z',
                  provider: 'reb',
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

      if (url.includes('/api/realestate/map/layers') && url.includes('layerType=sigungu') && url.includes('region-daejeon')) {
        return new Response(JSON.stringify({
          layerType: 'sigungu',
          parentTargetId: 'region-daejeon',
          asOf: '2026-06-15T00:00:00Z',
          sourceLabel: 'map_layer_snapshots',
          mapDataSource: 'KOSTAT 2018',
          dataStatus: 'ok',
          stale: false,
          periods: ['week', 'month', 'quarter', 'halfYear', 'year'],
          targets: [
            {
              targetId: 'region-daejeon-yuseong',
              targetType: 'region',
              displayName: '대전 유성구',
              regionLevel: 'sigungu',
              regionCode: '25040',
              parentTargetId: 'region-daejeon',
              periods: {
                week: {
                  changePct: 0.31,
                  sampleCount: 42,
                  confidence: 77,
                  asOf: '2026-06-15T00:00:00Z',
                  provider: 'reb_stat',
                  sourceLabel: 'map_layer_snapshots',
                  dataStatus: 'ok',
                  stale: false
                },
                month: {
                  changePct: 0.31,
                  sampleCount: 42,
                  confidence: 77,
                  asOf: '2026-05-01T00:00:00Z',
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

      if (url.includes('/api/realestate/map/layers') && url.includes('layerType=sigungu') && url.includes('region-sejong')) {
        return new Response(JSON.stringify({
          layerType: 'sigungu',
          parentTargetId: 'region-sejong',
          asOf: '2026-05-01T00:00:00Z',
          sourceLabel: 'map_layer_snapshots',
          mapDataSource: 'KOSTAT 2018',
          dataStatus: 'ok',
          stale: false,
          periods: ['month', 'quarter', 'halfYear', 'year'],
          targets: [
            {
              targetId: 'region-sejong-sejongsi',
              targetType: 'region',
              displayName: 'Sejong-si',
              regionLevel: 'sigungu',
              regionCode: '29010',
              parentTargetId: 'region-sejong',
              periods: {
                month: {
                  changePct: -0.18,
                  sampleCount: 1,
                  confidence: 1,
                  asOf: '2026-05-01T00:00:00Z',
                  provider: 'reb',
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

      if (url.includes('/api/realestate/targets/region-sejong/evidence-logs')) {
        return new Response(JSON.stringify({
          items: [
            {
              evidenceLogId: 'evidence-region-sejong-20260624',
              targetId: 'region-sejong',
              summary: 'Sejong parent evidence summary',
              subtitle: 'Sejong parent report',
              confidence: 0.82,
              asOf: '2026-05-01T00:00:00Z',
              evidenceItems: []
            }
          ]
        }), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      if (url.includes('/api/realestate/targets/region-daejeon-yuseong/evidence-logs')) {
        return new Response(JSON.stringify({
          items: [
            {
              evidenceLogId: 'evidence-region-daejeon-yuseong-20260624',
              targetId: 'region-daejeon-yuseong',
              summary: '관찰: 커뮤니티 반응은 확대되어 있음(언급 2건). 시장지표도 일부 소폭 변동을 보입니다.',
              subtitle: '언급 2건, 직전 대비 신규, 주요 쟁점: 확인 필요',
              confidence: 0.77,
              asOf: '2026-05-01T00:00:00Z',
              evidenceItems: []
            }
          ]
        }), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      if (url.includes('/api/realestate/targets/') && url.includes('/evidence-logs')) {
        return new Response(JSON.stringify({ items: [] }), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      if (url.includes('/api/realestate/targets/region-daejeon-yuseong/regional-report')) {
        return new Response(JSON.stringify({
          reportId: 'regional-report-region-daejeon-yuseong-test',
          targetId: 'region-daejeon-yuseong',
          targetName: 'Daejeon Yuseong',
          regionLevel: 'sigungu',
          regionCode: '25040',
          reportVersion: 'test-v1',
          promptVersion: 'test-prompt-v1',
          modelName: null,
          generatedBy: 'test',
          title: 'Stored regional report',
          headline: 'SHOULD_NOT_RENDER_HEADLINE',
          summary: 'Stored regional report summary',
          body: 'SHOULD_RENDER_IN_ANALYSIS_ONLY 매매 실거래와 전월세 흐름은 아래 분석 리포트에서만 다룬다.',
          expectationPoints: ['Stored expectation point 1', 'Stored expectation point 2', 'Stored expectation point 3'],
          concernPoints: ['Stored concern point 1', 'Stored concern point 2', 'Stored concern point 3'],
          dataQuality: 'deep_researched',
          confidence: 0.82,
          asOf: '2026-06-24T00:00:00Z',
          publishedAt: '2026-05-01T00:00:00Z',
          sources: []
        }), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      if (url.includes('/api/realestate/daily-briefings/latest')) {
        return new Response(JSON.stringify({
          briefingId: 'daily-briefing-20260624-v1',
          briefingDate: '2026-06-24',
          title: '오늘의 부동산 시장 브리핑',
          summaryHeadlines: [
            '수도권 전세 압력 재부각',
            '서울 동남권 거래 회복 흐름',
            '경기 남부 공급·정책 이슈 집중'
          ],
          sections: [],
          focusRegions: [],
          sourceItems: []
        }), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      if (url.includes('/api/realestate/newsroom') && url.includes('pageSize=12')) {
        return new Response(JSON.stringify({
          items: [
            {
              contentId: 'old-news',
              contentType: 'news',
              title: '오래된 부동산 뉴스',
              snippet: '오래된 뉴스 후보입니다.',
              url: 'https://example.com/old-news',
              domain: 'example.com',
              publishedAt: '2026-06-01T00:00:00Z',
              statusLabel: '수집 완료'
            },
            {
              contentId: 'latest-filler-news',
              contentType: 'news',
              title: '부동산 앱 제휴 이벤트',
              snippet: '시장 흐름과 직접 관련이 낮은 홍보성 후보입니다.',
              url: 'https://example.com/latest-filler-news',
              domain: 'example.com',
              publishedAt: '2026-06-25T09:30:00Z',
              statusLabel: '수집 완료'
            },
            {
              contentId: 'latest-policy-news',
              contentType: 'news',
              title: '주택 공급 정책 발표 후속 점검',
              snippet: '정책 발표 이후 공급 일정과 지역 영향을 함께 봅니다.',
              url: 'https://example.com/latest-policy-news',
              domain: 'example.com',
              publishedAt: '2026-06-25T08:20:00Z',
              statusLabel: '수집 완료'
            },
            {
              contentId: 'latest-report',
              contentType: 'report',
              title: '전세 가격 흐름 리포트',
              snippet: '전세 가격과 거래 흐름을 정리한 최신 리포트입니다.',
              url: 'https://example.com/latest-report',
              domain: 'example.com',
              publishedAt: '2026-06-24T23:00:00Z',
              statusLabel: '수집 완료'
            },
            {
              contentId: 'latest-loan-policy',
              contentType: 'news',
              title: '주택담보대출 금리 점검',
              snippet: '대출 금리와 가계부채 정책 변화를 함께 점검합니다.',
              url: 'https://example.com/latest-loan-policy',
              domain: 'example.com',
              publishedAt: '2026-06-24T21:00:00Z',
              statusLabel: '수집 완료'
            }
          ]
        }), {
          headers: { 'Content-Type': 'application/json' },
          status: 200
        });
      }

      if (url.includes('/api/realestate/market-data-schedules')) {
        return new Response(JSON.stringify({
          month: '2026-06',
          scheduleEvents: [
            {
              id: 'old-schedule',
              date: '2026-06-10',
              title: '과거 일정',
              category: 'market',
              source: '한국부동산원',
              summary: '이미 지난 일정입니다.',
              link: 'https://example.com/old-schedule',
              tone: 'market',
              status: 'published',
              dataStatus: 'ok',
              stale: false
            },
            {
              id: 'latest-schedule',
              date: '2026-06-26',
              title: '청약Home 모집공고 발표',
              category: 'subscription',
              source: '청약Home',
              summary: '내일 확인해야 하는 청약 일정입니다.',
              link: 'https://example.com/latest-schedule',
              tone: 'subscription',
              status: 'scheduled',
              dataStatus: 'ok',
              stale: false
            },
            {
              id: 'weekly-price-index',
              date: '2026-06-27',
              title: '한국부동산원 주간 가격동향 공표',
              category: 'market',
              source: '한국부동산원',
              summary: '주간 가격지수 공표 일정입니다.',
              link: 'https://example.com/weekly-price-index',
              tone: 'market',
              status: 'scheduled',
              dataStatus: 'ok',
              stale: false
            }
          ],
          sourceLinks: []
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
      '/realestate/daily-briefing',
      '/auth/login',
      '/auth/register',
      '/auth/find-account',
      '/realestate/map',
      '/realestate/map/:regionId',
      '/realestate/complexes',
      '/newsroom',
      '/realestate/transactions',
      '/realestate/reactions',
      '/realestate/targets/:targetId',
      '/indicators',
      '/indicators/:category',
      '/realestate/mypage',
      '/realestate/watchlist'
    ]);
    expect(routes[0]).toMatchObject({ redirect: '/dashboard' });
    expect(routes.find((route) => route.path === '/realestate/reactions')).toMatchObject({ redirect: '/realestate/transactions' });
    expect(routes.find((route) => route.path === '/realestate/watchlist')).toMatchObject({ redirect: '/realestate/mypage' });
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
    await flushPromises();

    expect(wrapper.get('[data-testid="app-title"]').text()).toContain('YouBuyFirst');
    expect(wrapper.get('[data-testid="app-title"]').attributes('href')).toBe('/dashboard');
    expect(wrapper.get('[data-testid="nav-dashboard"]').text()).toContain('대시보드');
    expect(wrapper.get('[data-testid="nav-map"]').text()).toContain('지역 분석');
    expect(wrapper.get('[data-testid="nav-newsroom"]').text()).toContain('뉴스룸');
    expect(wrapper.findAll('.nav-submenu a')).toHaveLength(4);
    expect(wrapper.findAll('.nav-submenu a.active')).toHaveLength(0);
    expect(wrapper.get('[data-testid="nav-transactions"]').text()).toContain('실거래');
    expect(wrapper.get('[data-testid="nav-transactions"]').attributes('href')).toBe('/realestate/transactions');
    expect(wrapper.find('[data-testid="nav-region-reactions"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="nav-indicators"]').text()).toContain('주요 일정');
    expect(wrapper.find('[data-testid="nav-agents"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="nav-watchlist"]').text()).toContain('마이페이지');
    expect(wrapper.get('[data-testid="nav-watchlist"]').attributes('href')).toBe('/realestate/mypage');
    expect(wrapper.get('[data-testid="auth-entry"]').text()).toContain('로그인');
    expect(wrapper.get('[data-testid="auth-entry"]').attributes('href')).toBe('/auth/login');
    expect(wrapper.find('.topbar .live-strip').exists()).toBe(true);
    const footer = wrapper.get('.site-footer');
    expect(footer.text()).toContain('실거래·전세 흐름');
    expect(footer.text()).toContain('Daily briefing');
    expect(footer.text()).not.toContain('Today 3줄 브리핑');
    expect(footer.text()).toContain('주요 일정·뉴스·리포트 정리');
    expect(footer.text()).not.toContain('커뮤니티 반응');
    expect(footer.text()).not.toContain('지역·단지 언급량');
    expect(footer.text()).not.toContain('에이전트 근거 로그');
    expect(wrapper.find('.brand-lockup > strong').exists()).toBe(false);
    expect(wrapper.find('.topbar').text()).not.toContain('BETA');
    expect(wrapper.find('.topbar').text()).not.toContain('MOCK');
    expect(wrapper.find('.topbar').text()).not.toContain('참고용');
    expect(wrapper.find('.topbar-live-strip').text()).not.toContain('mock data');
    expect(wrapper.get('.topbar-live-strip').text()).not.toContain('주요');
    expect(wrapper.get('.topbar-live-strip').text()).toContain('정책');
    expect(wrapper.get('.topbar-live-strip').text()).toContain('주택 공급 정책 발표 후속 점검');
    expect(wrapper.get('.topbar-live-strip').text()).toContain('주택담보대출 금리 점검');
    expect(wrapper.get('.topbar-live-strip').text()).toContain('리포트');
    expect(wrapper.get('.topbar-live-strip').text()).toContain('전세 가격 흐름 리포트');
    expect(wrapper.get('.topbar-live-strip').text()).toContain('일정');
    expect(wrapper.get('.topbar-live-strip').text()).toContain('청약Home 모집공고 발표');
    expect(wrapper.get('.topbar-live-strip').text()).toContain('한국부동산원 주간 가격동향 공표');
    expect(wrapper.get('.topbar-live-strip').text()).toContain('상승');
    expect(wrapper.get('.topbar-live-strip').text()).toContain('하락');
    expect(wrapper.get('.topbar-live-strip').text()).not.toContain('오래된 부동산 뉴스');
    expect(wrapper.get('.topbar-live-strip').text()).not.toContain('부동산 앱 제휴 이벤트');
    expect(wrapper.get('.topbar-live-strip').text()).not.toContain('최신 중요 후보 우선');
    expect(wrapper.get('.topbar-live-strip').text()).not.toContain('시장 이슈 확인 중');
    expect(wrapper.findAll('.live-strip-sequence')).toHaveLength(4);
    expect(wrapper.get('.dashboard-brand-hero').text()).toContain('YouBuyFirst');
    expect(wrapper.get('.dashboard-brand-hero').text()).toContain('당신을 위한 부동산 인사이트');
    expect(wrapper.text()).not.toContain('콘텐츠 반영');
    expect(wrapper.text()).toContain('실시간 뉴스');
    expect(wrapper.text()).toContain('정책·통계 리포트');
    expect(wrapper.text()).toContain('부동산 영상');
    expect(wrapper.text()).toContain('블로그·커뮤니티');
    expect(wrapper.get('.live-feed-card .feed-panel-title').text()).toBe('실시간 뉴스');
    expect(wrapper.get('.report-feed-card .feed-panel-title').text()).toBe('정책·통계 리포트');
    expect(wrapper.get('.video-feed-card .feed-panel-title').text()).toBe('부동산 영상');
    expect(wrapper.get('.link-feed-card .feed-panel-title').text()).toBe('블로그·커뮤니티');
    expect(wrapper.findAll('.content-feed-card .feed-title-dot')).toHaveLength(4);
    expect(wrapper.find('.live-feed-card .panel-header .label').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('live feed');
    expect(wrapper.text()).not.toContain('research feed');
    expect(wrapper.text()).not.toContain('outside links');
    expect(wrapper.text()).not.toContain('columns · community');
    expect(wrapper.text()).toContain('Daily briefing');
    expect(wrapper.text()).toContain('3줄 브리핑');
    expect(wrapper.find('.briefing-title-accent').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('핵심 요약');
    const briefing = wrapper.get('.daily-briefing-card');
    expect(briefing.get('.label').text()).toBe('Daily briefing');
    expect(briefing.find('.daily-briefing-headline-grid').exists()).toBe(true);
    expect(briefing.text()).not.toContain('AI 요약');
    expect(briefing.text()).not.toContain('AI briefing');
    expect(briefing.text()).not.toContain('전체보기');
    expect(briefing.text()).toContain('자세한 분석 보러가기');
    expect(briefing.find('.status-pill').exists()).toBe(false);
    expect(briefing.find('.daily-briefing-cta').exists()).toBe(true);
    expect(briefing.find('.daily-briefing-cta').attributes('href')).toBe('/realestate/daily-briefing');
    expect(briefing.findAll('.daily-briefing-headline-card strong').map((item) => item.text())).toEqual([
      '수도권 전세 압력 재부각',
      '서울 동남권 거래 회복 흐름',
      '경기 남부 공급·정책 이슈 집중'
    ]);
    expect(wrapper.text()).not.toContain('핵심 지역별 상승률');
    expect(wrapper.text()).not.toContain('지도 레이어 확인 중');
    expect(wrapper.find('.dashboard-content-flow > .indicator-section').exists()).toBe(false);
    expect(briefing.classes()).toContain('daily-briefing-card');
    expect(briefing.findAll('.daily-briefing-headline-card')).toHaveLength(3);
    expect(wrapper.findAll('.daily-briefing-item')).toHaveLength(0);
    expect(wrapper.find('.side-drawer .drawer-tabs').exists()).toBe(false);
    expect(wrapper.find('[aria-label="라이브 패널 탭"]').exists()).toBe(false);
    expect(wrapper.find('.drawer-reaction-screen > .drawer-feed').exists()).toBe(false);
    expect(wrapper.find('.drawer-reaction-screen .drawer-rising-stars').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('라이징 스타');
    expect(wrapper.text()).not.toContain('early signal');
    expect(wrapper.find('.drawer-metric-panel').exists()).toBe(false);
    expect(wrapper.find('.drawer-watch-panel').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('유사 과거 흐름 비교');
    expect(wrapper.find('.dashboard-ai-evidence-card').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('TOP 반응 지역 AI 근거 리포트');
    expect((globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.some(([input]) => String(input).includes('/evidence-logs'))).toBe(false);
    const moodBoard = wrapper.get('.region-bubble-section');
    expect(moodBoard.find('.reaction-legend').exists()).toBe(false);
    expect(moodBoard.text()).not.toContain('기대 반응');
    expect(moodBoard.text()).not.toContain('우려 반응');
    expect(moodBoard.text()).not.toContain('중립·기타');
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

  it('keeps the transaction map and filter bar clear of the right rail', () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toContain('body:has(.complex-browse-page) .app-shell {');
    expect(styles).toContain('--complex-browse-right-offset: var(--edge-rail-width);');
    expect(styles).toContain('body:has(.complex-browse-page) .app-shell.edge-panel-open {');
    expect(styles).toContain('--complex-browse-right-offset: calc(var(--edge-rail-width) + var(--edge-panel-open-width));');
    expect(styles).toMatch(
      /body:has\(\.complex-browse-page\) \.page-frame\s*\{[\s\S]*width: calc\(100% - var\(--complex-browse-right-offset\)\);[\s\S]*margin: 0 var\(--complex-browse-right-offset\) 0 0;/
    );
  });

  it('renders the core product pages with the expanded planning content', async () => {
    const transactions = await mountAt('/realestate/transactions');
    await flushPromises();

    expect(transactions.find('.complex-browse-page').exists()).toBe(true);
    expect(transactions.text()).toContain('실거래 지도');
    expect(transactions.find('[data-testid="complex-status"]').exists()).toBe(false);
    expect(transactions.find('[data-testid="complex-coord-status"]').exists()).toBe(false);

    const legacyReactions = await mountAt('/realestate/reactions');
    await flushPromises();

    expect(legacyReactions.vm.$route.path).toBe('/realestate/transactions');
    expect(legacyReactions.find('.complex-browse-page').exists()).toBe(true);
    expect(legacyReactions.text()).toContain('실거래 지도');

    const target = await mountAt('/realestate/targets/region-seoul-mapo');
    expect(target.text()).toContain('실거래로');
    expect(target.text()).toContain('마포구 아파트');
    expect(target.text()).toContain('AI 근거 리포트 수집 전/insufficient');
    expect(target.text()).toContain('지역 한줄 브리핑');
    expect(target.text()).toContain('단지 좌표 수집 전');
    expect(target.text()).toContain('검증된 단지 좌표가 들어오면');
    expect(target.text()).toContain('시간대별 변화');
    expect(target.text()).toContain('커뮤니티 반응 추이');
    expect(target.text()).toContain('신호 신뢰도');
    expect(target.findAll('.vertical-timeline article')).toHaveLength(0);
    expect(target.findAll('.evidence-list a')).toHaveLength(0);

    const complexTarget = await mountAt('/realestate/targets/complex-mapo-raemian-prugio');
    expect(complexTarget.find('.unsupported-region-state').exists()).toBe(false);
    expect(complexTarget.text()).toContain('마포래미안푸르지오');
    expect(complexTarget.text()).toContain('AI 근거 리포트 수집 전/insufficient');
    expect(complexTarget.text()).toContain('단지 좌표 수집 전');
    expect(complexTarget.find('[data-testid="complex-map-inspector"]').exists()).toBe(false);

    const otherTarget = await mountAt('/realestate/targets/living-area-gyeonggi-dongtan-station');
    expect(otherTarget.text()).toContain('동탄역권');
    expect(otherTarget.text()).toContain('living-area-gyeonggi-dongtan-station');
    expect(otherTarget.text()).toContain('AI 근거 리포트 수집 전/insufficient');
    expect(otherTarget.text()).toContain('단지 좌표 수집 전');

    const unsupportedTarget = await mountAt('/realestate/targets/living-area-seoul-seongsu');
    expect(unsupportedTarget.find('.unsupported-region-state').exists()).toBe(true);
    expect(unsupportedTarget.text()).toContain('living-area-seoul-seongsu');
    expect(unsupportedTarget.find('.region-reaction-card').exists()).toBe(false);

    const newsroomAll = await mountAt('/newsroom');
    await flushPromises();

    expect(newsroomAll.text()).toContain('뉴스룸');
    expect(newsroomAll.find('.newsroom-hero').exists()).toBe(true);
    expect(newsroomAll.find('.newsroom-title-card').exists()).toBe(false);
    expect(newsroomAll.text()).toContain('콘텐츠 피드');
    expect(newsroomAll.text()).toContain('원문 링크 기준으로 모아봅니다');
    expect(newsroomAll.findAll('.nav-submenu a.active')).toHaveLength(0);
    expect(newsroomAll.text()).toContain('블로그·커뮤니티');
    expect(newsroomAll.find('.newsroom-switch').exists()).toBe(false);
    expect(newsroomAll.findAll('.newsroom-overview-card')).toHaveLength(4);
    for (const card of newsroomAll.findAll('.newsroom-overview-card')) {
      expect(card.findAll('.newsroom-row')).toHaveLength(0);
      expect(card.find('.newsroom-empty-state').exists()).toBe(true);
    }
    expect(newsroomAll.text()).not.toContain('콘텐츠 반영');
    expect(newsroomAll.text()).not.toContain('콘텐츠 확인 필요');
    expect(newsroomAll.text()).toContain('콘텐츠를 불러오지 못했습니다');
    expect(newsroomAll.text()).toContain('실시간 뉴스');
    expect(newsroomAll.text()).toContain('정책·통계 리포트');
    expect(newsroomAll.text()).toContain('부동산 영상');
    expect(newsroomAll.text()).toContain('블로그·커뮤니티');
    expect(newsroomAll.findAll('.newsroom-overview-card .feed-panel-title').map((title) => title.text())).toEqual([
      '실시간 뉴스',
      '정책·통계 리포트',
      '부동산 영상',
      '블로그·커뮤니티'
    ]);
    expect(newsroomAll.findAll('.feed-title-wrap .feed-title-dot')).toHaveLength(4);
    expect(newsroomAll.text()).not.toContain('newsroom');
    expect(newsroomAll.text()).not.toContain('live feed');
    expect(newsroomAll.text()).not.toContain('research feed');
    expect(newsroomAll.text()).not.toContain('outside links');
    expect(newsroomAll.text()).not.toContain('columns · community');
    expect(newsroomAll.text()).toContain('뉴스만 몰아보기');
    expect(newsroomAll.text()).toContain('원문 링크만 몰아보기');

    const newsroom = await mountAt('/newsroom?feed=videos&page=2');
    await flushPromises();

    expect(newsroom.text()).toContain('영상');
    expect(newsroom.text()).toContain('콘텐츠를 불러오지 못했습니다');
    expect(newsroom.text()).not.toContain('feed list');
    expect(newsroom.find('.newsroom-pager').exists()).toBe(true);
    expect(newsroom.findAll('.nav-submenu a.active')).toHaveLength(1);
    expect(newsroom.find('.nav-submenu a.active').text()).toContain('영상');

    const indicators = await mountAt('/indicators');
    expect(indicators.find('.indicator-calendar-page').exists()).toBe(true);
    expect(indicators.text()).toContain('주요 일정');
    expect(indicators.text()).toContain('가격·거래현황, 공급, 금융, 청약, 정책·공시 일정을 캘린더로 확인합니다.');
    expect(indicators.find('.calendar-agenda-panel').exists()).toBe(false);
    expect(indicators.text()).toContain('공식 출처');
    expect(indicators.text()).toContain('한국부동산원 R-ONE');
    expect(indicators.text()).toContain('국토교통부 실거래가 공개시스템');
    expect(indicators.findAll('.calendar-event-strip')).toHaveLength(0);
    expect(indicators.find('.calendar-event-card.empty').exists()).toBe(true);
    expect(indicators.text()).toContain('공식 일정 수집 전');
    expect(indicators.findAll('.schedule-source-card')).toHaveLength(13);
    expect(indicators.text()).not.toContain('주요 부동산 지표');
    expect(indicators.text()).not.toContain('지표와 반응이 엇갈린 지역');
    expect(indicators.text()).not.toContain('지표별 반응 히트맵');

    const indicatorDetail = await mountAt('/indicators/price-transaction');
    expect(indicatorDetail.text()).toContain('주요 일정');
    expect(indicatorDetail.text()).toContain('공식 출처');

    const mypage = await mountAt('/realestate/mypage');
    expect(mypage.text()).toContain('내 부동산 관찰 보드');
    expect(mypage.text()).toContain('사용자가 저장한 지역을 관리하고');
    expect(mypage.text()).toContain('저장된 지역이나 단지가 아직 없습니다');
    expect(mypage.text()).toContain('지난 방문 이후 바뀐 것');
    expect(mypage.text()).toContain('내 알림 조건');
    expect(mypage.text()).toContain('지역별 관찰 메모');
    expect(mypage.text()).toContain('저장 지역 비교');
    expect(mypage.text()).toContain('알림 조건 준비 중');
    expect(mypage.text()).not.toContain('관심 후보');
    expect(mypage.text()).not.toContain('지역 반응 TOP10');
    expect(mypage.text()).not.toContain('커뮤니티 원문');
    expect(mypage.text()).not.toContain('mock watchlist');

    const legacyWatchlist = await mountAt('/realestate/watchlist');
    expect(legacyWatchlist.vm.$route.path).toBe('/realestate/mypage');
    expect(legacyWatchlist.text()).toContain('내 부동산 관찰 보드');
  });

  it('opens a full regional drilldown map from the national map', async () => {
    const wrapper = await mountAt('/realestate/map');
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('전국 지역 흐름 지도');
    expect(wrapper.find('[data-testid="map-report-panel"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="realestate-map-layout"]').classes()).toContain('centered');
    expect(wrapper.get('[data-testid="map-update-badge"]').text()).toBe('UPDATE: 2026.05.01');
    const periodButtons = wrapper.findAll('.map-period-tabs button');
    expect(periodButtons).toHaveLength(5);
    expect(periodButtons[1].classes()).toContain('active');
    expect(periodButtons[0].classes()).not.toContain('active');
    expect(wrapper.get('[data-testid="map-zoom-percent"]').text()).toBe('100%');
    expect(wrapper.text()).toContain('가장 높은 상승');
    expect(wrapper.text()).toContain('가장 많은 하락');
    expect(wrapper.text()).toContain('지역 단위');
    expect(wrapper.text()).not.toContain('다음 단계');

    wrapper.get('[data-testid="korea-map-shell"]').element.dispatchEvent(new WheelEvent('wheel', {
      bubbles: true,
      cancelable: true,
      clientX: 520,
      clientY: 420,
      deltaY: -460
    }));
    await wrapper.vm.$nextTick();

    expect(wrapper.get('[data-testid="korea-map-shell"]').classes()).toContain('is-map-zoomed');
    expect(wrapper.get('[data-testid="korea-map-board"]').attributes('style')).toContain('--map-zoom: 2.');
    expect(wrapper.get('[data-testid="korea-map-board"]').attributes('style')).toContain('--map-label-scale: 0.');
    const mapPageSource = readFileSync(resolve(testDir, '../pages/RealEstateMapPage.vue'), 'utf8');
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');
    const scopedBoardRule = /\.realestate-map-page \.korea-map-board\s*{[\s\S]*?}/.exec(styles)?.[0] ?? '';
    const targetButtonRule = /\.map-target-buttons button,\s*\n\.map-target-buttons \.map-target-link\s*{[\s\S]*?}/.exec(styles)?.[0] ?? '';

    expect(wrapper.find('.map-surface-layer').exists()).toBe(true);
    expect(mapPageSource).toContain('class="map-surface-layer"');
    expect(styles).toMatch(/\.realestate-map-page \.map-surface-layer\s*{[\s\S]*scale\(var\(--map-zoom, 1\)/);
    expect(scopedBoardRule).toContain('transform: none;');
    expect(scopedBoardRule).not.toContain('scale(var(--map-zoom');
    expect(targetButtonRule).not.toContain('scale(var(--map-label-scale');

    await wrapper.get('button[aria-label="지도 확대 초기화"]').trigger('click');

    expect(wrapper.get('[data-testid="map-zoom-percent"]').text()).toBe('100%');

    const daejeonTarget = wrapper.get('[data-testid="map-target-daejeon"]');
    expect(daejeonTarget.attributes('href')).toBe('/realestate/map/region-daejeon');
    const drilldown = await mountAt(daejeonTarget.attributes('href')!);
    await flushPromises();

    expect(drilldown.vm.$route.path).toBe('/realestate/map/region-daejeon');
    expect(drilldown.text()).toContain('대전 상세 흐름 지도');
    expect(drilldown.text()).toContain('전국 지도로 돌아가기');
    expect(drilldown.findAll('[data-testid^="subregion-shape-"]')).toHaveLength(5);
    expect(drilldown.findAll('.subregion-labels text')).toHaveLength(0);
    expect(drilldown.find('[data-testid="korea-map-shell"]').exists()).toBe(true);
    expect(drilldown.find('[data-testid="map-zoom-percent"]').exists()).toBe(true);
    expect(drilldown.text()).toContain('동구');
    expect(drilldown.text()).toContain('유성구');
    expect(drilldown.text()).toContain('가장 높은 상승');
    expect(drilldown.text()).toContain('가장 많은 하락');
    expect(drilldown.text()).toContain('하위지역');
    expect(drilldown.text()).not.toContain('다음 단계');
    expect(drilldown.get('[data-testid="subregion-layer-status"]').text()).toBe('하위지역 기준');
    expect(drilldown.text()).not.toContain('한국부동산원 · 공공데이터 반영 · 최신 반영 · 2026. 05. 01. 09:00 KST');

    const unavailableButton = drilldown.findAll('[data-testid^="subregion-button-"]')
      .find((button) => button.attributes('data-testid') !== 'subregion-button-25040');
    expect(unavailableButton).toBeTruthy();
    const unavailableCode = unavailableButton!.attributes('data-testid')!.replace('subregion-button-', '');
    const unavailableShape = drilldown.get(`[data-testid="subregion-shape-${unavailableCode}"]`);

    expect(unavailableButton!.classes()).toContain('unavailable');
    expect(unavailableButton!.attributes('disabled')).toBeDefined();
    expect(unavailableShape.classes()).toContain('unavailable');

    await unavailableShape.trigger('click');

    expect(unavailableButton!.classes()).not.toContain('active');
    expect(unavailableShape.classes()).not.toContain('active');

    await drilldown.get('[data-testid="subregion-button-25040"]').trigger('click');
    await flushPromises();

    expect(drilldown.find('[data-testid="realestate-map-layout"]').classes()).toContain('split');
    const reportPanel = drilldown.get('[data-testid="map-report-panel"]');
    const reportText = reportPanel.text();
    const briefingSection = reportPanel.get('[data-testid="report-section-ai-briefing"]');
    const analysisSection = reportPanel.get('[data-testid="report-section-ai-analysis"]');

    expect(briefingSection.text()).not.toContain('SHOULD_NOT_RENDER_HEADLINE');
    expect(reportPanel.find('#map-ai-report-title').exists()).toBe(false);
    expect(analysisSection.text()).toContain('SHOULD_RENDER_IN_ANALYSIS_ONLY');
    expect(reportText).toContain('유성구');
    expect(reportText).toContain('AI 핵심 브리핑');
    expect(reportText).not.toContain('최근 변화율');
    expect(reportText).toContain('기대 지점');
    expect(reportText).toContain('우려 지점');
    expect(reportText).toContain('AI 분석 리포트');
    expect(reportText).toContain('관련 뉴스·리포트');
    expect(reportText).not.toContain('핵심 변화');
    expect(reportText).not.toContain('주의해서 볼 점');
    expect(reportText).not.toContain('핵심 확인');
    expect(reportText).not.toContain('공식 근거');
    expect(reportText).not.toContain('근거와 한계');
    expect(reportText).not.toContain('핵심 수치');
    expect(reportText).not.toContain('공식 시장 사실');
    expect(reportText).not.toContain('지역 내 비교');
    expect(reportText).not.toContain('공급·정책·일정');
    expect(reportText).not.toContain('보조 반응');
    expect(reportText).not.toContain('다음 연결 후보');
    expect(reportText).not.toContain('market facts');
    expect(reportText).not.toContain('official facts');
    expect(reportText).not.toContain('secondary signal');
    expect(reportText).not.toContain('언급량 급증');
    expect(reportText).not.toContain('언급');
    expect(reportText).not.toContain('community pulse');
    expect(reportText).not.toContain('신뢰도');
    expect(reportText).not.toContain('공공데이터 반영');
    expect(reportText).not.toContain('AI 근거');
    expect(reportText).not.toContain('insufficient');
    expect(reportText).not.toContain('시군구 ·');
    expect(reportPanel.find('.map-briefing-report-layout').exists()).toBe(true);
    expect(reportPanel.find('.map-report-card.featured').exists()).toBe(true);
    expect(reportPanel.find('.map-report-delta-block').exists()).toBe(true);
    const deltaBlockText = reportPanel.get('.map-report-delta-block').text();
    expect(deltaBlockText).toContain('최근 1개월');
    expect(deltaBlockText).not.toContain('가격지수 변화');
    expect(deltaBlockText.match(/최근 1개월/g) ?? []).toHaveLength(1);
    expect(reportPanel.find('.map-report-card.featured > .map-report-card-header .map-report-delta-block').exists()).toBe(false);
    expect(reportPanel.find('[data-testid="report-section-ai-analysis"] .map-report-analysis-copy > .map-report-delta-block.analysis-delta').exists()).toBe(true);
    expect(reportPanel.find('.map-report-card.featured .map-report-card-body > .map-report-hero-grid > .map-report-delta-block').exists()).toBe(false);
    const deltaValue = reportPanel.get('.map-report-delta-value');
    expect(deltaValue.text()).toMatch(/[+-]?\d+\.\d{2}%/);
    expect(deltaValue.classes().some((className) => ['up', 'down', 'flat'].includes(className))).toBe(true);
    const outlookPanel = reportPanel.get('.map-report-outlook-grid');
    expect(outlookPanel.text()).toContain('기대 지점');
    expect(outlookPanel.text()).toContain('우려 지점');
    expect(outlookPanel.findAll('.map-report-outlook-row')).toHaveLength(6);
    expect(reportPanel.find('.map-briefing-primary-panel').exists()).toBe(false);
    const reportCards = reportPanel.findAll('.map-report-card');
    expect(reportCards).toHaveLength(3);
    for (const card of reportCards) {
      expect(card.find('.map-report-card-header').exists()).toBe(true);
      expect(card.find('.map-report-card-body').exists()).toBe(true);
    }
    expect(reportPanel.findAll('.map-report-card-row')).toHaveLength(0);
    expect(reportPanel.findAll('.map-report-row-index')).toHaveLength(0);
    expect(reportPanel.find('.map-briefing-focus-list').exists()).toBe(false);
    expect(reportPanel.find('.map-briefing-source-ledger').exists()).toBe(false);
    expect(reportPanel.find('.map-briefing-limit-ledger').exists()).toBe(false);
    expect(reportPanel.find('.map-report-briefing-board').exists()).toBe(false);
    expect(reportPanel.find('.report-plain-briefing').exists()).toBe(false);
    expect(reportPanel.find('.regional-briefing-headline-card').exists()).toBe(false);
    expect(reportPanel.find('.regional-briefing-index').exists()).toBe(false);
    expect(reportPanel.find('.regional-briefing-chipline').exists()).toBe(false);
    expect(reportPanel.find('.report-mini-metric-grid').exists()).toBe(false);
    expect(reportPanel.find('.report-evidence-mini-grid').exists()).toBe(false);
    expect(reportPanel.find('.report-kpi-lines').exists()).toBe(false);
    expect(reportPanel.find('.report-ledger-columns').exists()).toBe(false);
    expect(reportPanel.findAll('.status-pill')).toHaveLength(0);
    expect(reportPanel.find('.daily-briefing-card').exists()).toBe(false);
    expect(reportPanel.find('.daily-briefing-headline-card').exists()).toBe(false);
    expect(reportPanel.findAll('.issue-report-section')).toHaveLength(0);
    expect(reportPanel.findAll('.report-compact-ledger').length).toBeLessThanOrEqual(1);
    expect(reportPanel.get('[data-testid="report-section-ai-analysis"]').text()).toContain('최신 종합 리포트');
    const reportUpdatedAt = reportPanel.get('[data-testid="report-updated-at"]').text();
    expect(reportUpdatedAt).toContain('리포트 업데이트');
    expect(reportUpdatedAt).toContain('2026. 05. 01. 09:00 KST');
    expect(reportPanel.get('[data-testid="report-section-ai-analysis"]').text()).toContain('매매 실거래');
    expect(reportPanel.get('[data-testid="report-section-related-reports"]').text()).toContain('가격지수');
    expect(reportPanel.get('[data-testid="report-section-related-reports"]').text()).toContain('수집 전');

    const weekTab = drilldown.findAll('.map-period-tabs button').find((button) => button.text() === '1주');
    expect(weekTab).toBeTruthy();
    await weekTab!.trigger('click');
    await flushPromises();

    const updatedReportPanel = drilldown.get('[data-testid="map-report-panel"]');
    expect(updatedReportPanel.get('[data-testid="report-updated-at"]').text()).toBe(reportUpdatedAt);
    expect(updatedReportPanel.get('.map-report-delta-block').text()).toContain('최근 1주');

    await drilldown.get('[data-testid="close-map-report"]').trigger('click');

    expect(drilldown.find('[data-testid="map-report-panel"]').exists()).toBe(true);
    expect(drilldown.get('[data-testid="map-report-panel"]').text()).toContain('대전 전체');
    expect(drilldown.find('[data-testid="realestate-map-layout"]').classes()).toContain('split');
  }, 15000);

  it('opens the map report panel for a selected municipality from route query', async () => {
    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    fetchMock.mockClear();

    const wrapper = await mountAt('/realestate/map/region-daejeon?selectedTargetId=region-daejeon-yuseong&selectedRegionCode=25040&period=week');
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.$route.path).toBe('/realestate/map/region-daejeon');
    expect(wrapper.vm.$route.query.selectedTargetId).toBe('region-daejeon-yuseong');
    expect(wrapper.vm.$route.query.period).toBe('week');
    expect(wrapper.find('[data-testid="realestate-map-layout"]').classes()).toContain('split');
    expect(wrapper.get('[data-testid="subregion-button-25040"]').classes()).toContain('active');
    expect(wrapper.get('[data-testid="map-report-panel"] .map-report-header > div > span').text()).toContain('25040');

    const evidenceUrls = fetchMock.mock.calls
      .map(([input]) => String(input))
      .filter((url) => url.includes('/evidence-logs'));

    expect(evidenceUrls.some((url) => url.includes('/api/realestate/targets/region-daejeon-yuseong/evidence-logs?limit=1'))).toBe(true);
  }, 15000);

  it('uses the parent Sejong report when selecting the single Sejong city subregion', async () => {
    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    const sejongTarget = mapTargetsFixture.targets.find((target) => target.targetId === 'region-sejong');
    fetchMock.mockClear();

    expect(sejongTarget).toBeTruthy();

    const wrapper = await mountAt('/realestate/map/region-sejong');
    await flushPromises();
    await wrapper.vm.$nextTick();

    await wrapper.get('[data-testid="subregion-button-29010"]').trigger('click');
    await flushPromises();
    await wrapper.vm.$nextTick();

    const evidenceUrls = fetchMock.mock.calls
      .map(([input]) => String(input))
      .filter((url) => url.includes('/evidence-logs'));

    expect(evidenceUrls.some((url) => url.includes('/api/realestate/targets/region-sejong/evidence-logs?limit=1'))).toBe(true);
    expect(evidenceUrls.some((url) => url.includes('/api/realestate/targets/region-sejong-sejongsi/evidence-logs'))).toBe(false);
    expect(wrapper.get('[data-testid="map-report-panel"] .map-report-header > div > span').text()).toBe(`${sejongTarget!.regionCode} \u00b7 ${sejongTarget!.regionCode}`);
  }, 15000);

  it('opens a focused Gyeonggi municipal map from dense cluster markers', async () => {
    const wrapper = await mountAt('/realestate/map/region-gyeonggi');
    await flushPromises();

    const clusters = wrapper.findAll('[data-testid^="subregion-cluster-"]');

    expect(clusters).toHaveLength(4);
    expect(wrapper.text()).not.toContain('경기 동부');
    expect(wrapper.findAll('[data-testid^="subregion-button-31"]').length).toBe(0);
    expect(wrapper.get('[data-testid="map-zoom-percent"]').text()).toBe('100%');

    await wrapper.get('[data-testid="subregion-cluster-center"]').trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('경기 중부 상세 흐름');
    expect(wrapper.get('[data-testid="map-zoom-percent"]').text()).toBe('100%');
    expect(wrapper.find('[data-testid="subregion-focus-return"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-testid^="subregion-cluster-"]')).toHaveLength(0);
    expect(wrapper.findAll('[data-testid^="subregion-button-31"]').length).toBeGreaterThan(10);
    expect(wrapper.findAll('[data-testid^="subregion-button-31"]').length).toBeLessThan(42);

    await wrapper.get('[data-testid="subregion-focus-return"]').trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('경기 상세 흐름');
    expect(wrapper.findAll('[data-testid^="subregion-cluster-"]')).toHaveLength(4);
    expect(wrapper.findAll('[data-testid^="subregion-button-31"]').length).toBe(0);
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

  it('keeps Incheon municipality buttons readable despite far island geometry', async () => {
    const wrapper = await mountAt('/realestate/map/region-incheon');
    await flushPromises();
    const mapPageSource = readFileSync(resolve(testDir, '../pages/RealEstateMapPage.vue'), 'utf8');

    const renderedPathBoundsByCode = new Map<string, { maxX: number; maxY: number; minX: number; minY: number }>();
    const renderedPathXs = wrapper.findAll('[data-testid^="subregion-shape-"]').flatMap((shape) => {
      const code = shape.attributes('data-testid')?.replace('subregion-shape-', '') ?? '';
      const values = (shape.attributes('d')?.match(/-?\d+(?:\.\d+)?/g) ?? []).map(Number);
      const points = values.reduce<[number, number][]>((items, value, index) => {
        if (index % 2 === 0) {
          items.push([value, values[index + 1] ?? value]);
        }

        return items;
      }, []);
      const xs = points.map(([x]) => x);
      const ys = points.map(([, y]) => y);

      renderedPathBoundsByCode.set(code, {
        maxX: Math.max(...xs),
        maxY: Math.max(...ys),
        minX: Math.min(...xs),
        minY: Math.min(...ys)
      });

      return xs;
    });
    const mainlandButtonLefts = wrapper.findAll('[data-testid^="subregion-button-23"]')
      .filter((button) => !button.attributes('data-testid')?.startsWith('subregion-button-233'))
      .map((button) => Number(/left:\s*([\d.]+)%/.exec(button.attributes('style') ?? '')?.[1] ?? '0'));
    const incheonButtons = wrapper.findAll('[data-testid^="subregion-button-23"]');
    const extrusionTransforms = wrapper.findAll('.subregion-map .region-extrusion path')
      .map((path) => path.attributes('transform'));
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(mapPageSource).not.toContain('compactIncheonGeometry');
    expect(mapPageSource).not.toContain('compactIncheonCoordinate');
    expect(mapPageSource).not.toContain('incheonLabelPositionByCode');
    expect(mapPageSource).not.toContain('incheonDisplayPoint');
    expect(mapPageSource).toContain('omitRemoteIncheonOffshorePolygons');
    expect(mapPageSource).toContain('projectedInteriorPoint(feature');
    expect(mapPageSource).toContain("detailExtrusionTransform = 'translate(0 7)'");
    expect(new Set(extrusionTransforms)).toEqual(new Set(['translate(0 7)']));
    expect(styles).toContain('.realestate-map-page .subregion-map');
    expect(styles).toContain('drop-shadow(0 9px 14px rgba(0, 0, 0, 0.28))');
    expect(styles).toContain('.realestate-map-page .region-detail-outline');
    expect(styles).toContain('transform: translate(0, 8px);');
    expect(styles).toContain('.is-incheon-drilldown .subregion-target-buttons button');
    expect(wrapper.find('.realestate-map-page').classes()).toContain('is-incheon-drilldown');
    expect(Math.min(...renderedPathXs)).toBeGreaterThan(80);
    for (const button of incheonButtons) {
      const code = button.attributes('data-testid')?.replace('subregion-button-', '') ?? '';
      const bounds = renderedPathBoundsByCode.get(code);
      const style = button.attributes('style') ?? '';
      const centerX = (Number(/left:\s*([\d.]+)%/.exec(style)?.[1] ?? '0') / 100) * 560;
      const centerY = (Number(/top:\s*([\d.]+)%/.exec(style)?.[1] ?? '0') / 100) * 560;

      expect(bounds, code).toBeTruthy();
      expect(centerX, code).toBeGreaterThanOrEqual(bounds!.minX);
      expect(centerX, code).toBeLessThanOrEqual(bounds!.maxX);
      expect(centerY, code).toBeGreaterThanOrEqual(bounds!.minY);
      expect(centerY, code).toBeLessThanOrEqual(bounds!.maxY);
    }
    expect(mainlandButtonLefts).toHaveLength(8);
    expect(Math.max(...mainlandButtonLefts) - Math.min(...mainlandButtonLefts)).toBeGreaterThan(24);
    expect(Math.min(...mainlandButtonLefts)).toBeLessThan(60);
    expect(Math.max(...mainlandButtonLefts)).toBeLessThan(95);
  }, 15000);

  it('keeps Ulleung close to the Gyeongbuk mainland inset', async () => {
    const wrapper = await mountAt('/realestate/map/region-gyeongbuk');
    await flushPromises();
    const mapPageSource = readFileSync(resolve(testDir, '../pages/RealEstateMapPage.vue'), 'utf8');
    const renderedPathBoundsByCode = new Map<string, { maxX: number; maxY: number; minX: number; minY: number }>();

    wrapper.findAll('[data-testid^="subregion-shape-"]').forEach((shape) => {
      const code = shape.attributes('data-testid')?.replace('subregion-shape-', '') ?? '';
      const values = (shape.attributes('d')?.match(/-?\d+(?:\.\d+)?/g) ?? []).map(Number);
      const points = values.reduce<[number, number][]>((items, value, index) => {
        if (index % 2 === 0) {
          items.push([value, values[index + 1] ?? value]);
        }

        return items;
      }, []);
      const xs = points.map(([x]) => x);
      const ys = points.map(([, y]) => y);

      renderedPathBoundsByCode.set(code, {
        maxX: Math.max(...xs),
        maxY: Math.max(...ys),
        minX: Math.min(...xs),
        minY: Math.min(...ys)
      });
    });

    const ulleungBounds = renderedPathBoundsByCode.get('37430');
    const mainlandBounds = [...renderedPathBoundsByCode.entries()]
      .filter(([code]) => code !== '37430')
      .map(([, bounds]) => bounds);
    const mainlandMaxX = Math.max(...mainlandBounds.map((bounds) => bounds.maxX));
    const mainlandMinX = Math.min(...mainlandBounds.map((bounds) => bounds.minX));
    const ulleungButtonStyle = wrapper.get('[data-testid="subregion-button-37430"]').attributes('style') ?? '';
    const ulleungButtonLeft = Number(/left:\s*([\d.]+)%/.exec(ulleungButtonStyle)?.[1] ?? '0');
    const ulleungButtonTop = Number(/top:\s*([\d.]+)%/.exec(ulleungButtonStyle)?.[1] ?? '0');

    expect(mapPageSource).toContain('repositionGyeongbukUlleungInset');
    expect(ulleungBounds).toBeTruthy();
    expect(ulleungBounds!.minX - mainlandMaxX).toBeLessThan(30);
    expect(mainlandMaxX - mainlandMinX).toBeGreaterThan(480);
    expect(ulleungButtonLeft).toBeGreaterThan(82);
    expect(ulleungButtonLeft).toBeLessThan(99);
    expect(ulleungButtonTop).toBeGreaterThan(8);
    expect(ulleungButtonTop).toBeLessThan(28);
  }, 15000);

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
    expect(wrapper.text()).toContain('실제 매수·매도·청약 판단을 대신하지 않습니다');
    expect(wrapper.text()).toContain('매수·매도·청약·대출 행동을 권유하지 않으며');
    expect(wrapper.text()).not.toContain('매수 추천');
    expect(wrapper.text()).not.toContain('매도 추천');
    expect(wrapper.text()).not.toContain('수익 보장');
    expect(wrapper.text()).not.toContain('진입하세요');
    expect(wrapper.text()).not.toContain('시그널 확정');
  });
});
