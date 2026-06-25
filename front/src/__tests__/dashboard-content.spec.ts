import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import DashboardPage from '../pages/DashboardPage.vue';

const testDir = dirname(fileURLToPath(import.meta.url));

class TestEventSource {
  static instances: TestEventSource[] = [];
  readonly url: string;
  private listeners = new Map<string, Array<(event: MessageEvent) => void>>();

  constructor(url: string) {
    this.url = url;
    TestEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: (event: MessageEvent) => void) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
  }

  dispatch(type: string, payload: unknown) {
    const event = { data: JSON.stringify(payload) } as MessageEvent;
    for (const listener of this.listeners.get(type) ?? []) {
      listener(event);
    }
  }

  close = vi.fn();
}

const mountDashboardPage = async () => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/dashboard', component: DashboardPage },
      { path: '/realestate/daily-briefing', component: { template: '<div />' } },
      { path: '/newsroom', component: { template: '<div />' } },
      { path: '/realestate/transactions', component: { template: '<div />' } },
      { path: '/realestate/targets/:targetId', component: { template: '<div />' } },
      { path: '/realestate/map', component: { template: '<div />' } },
      { path: '/realestate/map/:regionId', component: { template: '<div />' } },
      { path: '/indicators', component: { template: '<div />' } }
    ]
  });

  router.push('/dashboard');
  await router.isReady();

  const wrapper = mount(DashboardPage, {
    global: {
      plugins: [router]
    }
  });
  await flushPromises();

  return wrapper;
};

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  TestEventSource.instances = [];
});

describe('dashboard newsroom content', () => {
  it('loads target search suggestions immediately and opens a result with one press', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      const rawUrl = String(input);
      const url = new URL(rawUrl, 'http://localhost');

      if (url.pathname === '/api/realestate/targets/search') {
        return new Response(JSON.stringify({
          items: [
            {
              targetId: 'region-seoul-mapo',
              targetType: 'region',
              displayName: '서울 마포구',
              slug: 'seoul-mapo',
              reviewState: 'approved',
              dataStatus: 'ok',
              regionLevel: 'sigungu',
              parentTargetId: 'region-seoul',
              legalDongCode: '11440',
              regionCode: '11440'
            },
            {
              targetId: 'complex-mapo-raemian-prugio',
              targetType: 'complex',
              displayName: '마포래미안푸르지오',
              slug: 'mapo-raemian-prugio',
              reviewState: 'candidate',
              dataStatus: 'mock',
              regionLevel: 'complex',
              parentTargetId: 'region-seoul-mapo',
              legalDongCode: '1144010100',
              regionCode: null
            }
          ]
        }));
      }
      if (url.pathname === '/api/realestate/daily-briefings/latest') {
        return new Response(JSON.stringify({ summaryHeadlines: [] }));
      }
      if (url.pathname === '/api/realestate/map/layers') {
        return new Response(JSON.stringify({ layerType: 'sigungu', periods: ['week'], targets: [] }));
      }
      if (url.pathname === '/api/realestate/dashboard/market-summary') {
        return new Response(JSON.stringify({ items: [] }));
      }
      if (url.pathname === '/api/realestate/newsroom') {
        return new Response(JSON.stringify({ items: [] }));
      }

      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountDashboardPage();
    await flushPromises();

    await wrapper.get('[data-testid="dashboard-search-input"]').trigger('focus');
    await wrapper.get('[data-testid="dashboard-search-input"]').setValue('마');
    await flushPromises();
    expect(fetcher.mock.calls.some(([input]) => String(input).includes('/api/realestate/targets/search'))).toBe(false);

    await wrapper.get('[data-testid="dashboard-search-input"]').setValue('마포');
    await flushPromises();

    const searchUrl = fetcher.mock.calls.map(([input]) => String(input)).find((url) => url.includes('/api/realestate/targets/search'));
    expect(searchUrl).toContain('q=%EB%A7%88%ED%8F%AC');
    expect(searchUrl).toContain('limit=8');
    expect(searchUrl).toContain('mode=autocomplete');
    expect(wrapper.get('[data-testid="dashboard-search-suggestions"]').text()).toContain('서울 마포구');
    expect(wrapper.get('[data-testid="dashboard-search-suggestions"]').text()).toContain('마포래미안푸르지오');

    await wrapper.get('[data-testid="dashboard-search-result-region-seoul-mapo"]').trigger('pointerdown');
    await flushPromises();

    expect(wrapper.vm.$route.path).toBe('/realestate/map/region-seoul');
    expect(wrapper.vm.$route.query.selectedTargetId).toBe('region-seoul-mapo');
    expect(wrapper.vm.$route.query.selectedRegionCode).toBe('11440');
    expect(wrapper.vm.$route.query.period).toBe('week');
    expect(wrapper.find('[data-testid="dashboard-search-suggestions"]').exists()).toBe(false);
  });

  it('searches when Korean composition completes at exactly two characters', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost');

      if (url.pathname === '/api/realestate/targets/search') {
        return new Response(JSON.stringify({ items: [] }));
      }
      if (url.pathname === '/api/realestate/daily-briefings/latest') {
        return new Response(JSON.stringify({ summaryHeadlines: [] }));
      }
      if (url.pathname === '/api/realestate/map/layers') {
        return new Response(JSON.stringify({ layerType: 'sigungu', periods: ['week'], targets: [] }));
      }
      if (url.pathname === '/api/realestate/dashboard/market-summary') {
        return new Response(JSON.stringify({ items: [] }));
      }
      if (url.pathname === '/api/realestate/newsroom') {
        return new Response(JSON.stringify({ items: [] }));
      }

      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountDashboardPage();
    await flushPromises();

    const input = wrapper.get('[data-testid="dashboard-search-input"]');
    await input.trigger('focus');
    (input.element as HTMLInputElement).value = '\uAC15\uB0A8';
    await input.trigger('compositionend');
    await flushPromises();

    const searchUrl = fetcher.mock.calls
      .map(([calledInput]) => String(calledInput))
      .find((url) => url.includes('/api/realestate/targets/search'));

    expect(searchUrl).toContain('q=%EA%B0%95%EB%82%A8');
    expect(searchUrl).toContain('limit=8');
    expect(searchUrl).toContain('mode=autocomplete');
  });

  it('searches while the second Korean character is still composing', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost');

      if (url.pathname === '/api/realestate/targets/search') {
        return new Response(JSON.stringify({ items: [] }));
      }
      if (url.pathname === '/api/realestate/daily-briefings/latest') {
        return new Response(JSON.stringify({ summaryHeadlines: [] }));
      }
      if (url.pathname === '/api/realestate/map/layers') {
        return new Response(JSON.stringify({ layerType: 'sigungu', periods: ['week'], targets: [] }));
      }
      if (url.pathname === '/api/realestate/dashboard/market-summary') {
        return new Response(JSON.stringify({ items: [] }));
      }
      if (url.pathname === '/api/realestate/newsroom') {
        return new Response(JSON.stringify({ items: [] }));
      }

      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountDashboardPage();
    await flushPromises();

    const input = wrapper.get('[data-testid="dashboard-search-input"]');
    await input.trigger('focus');
    await input.trigger('compositionstart');
    (input.element as HTMLInputElement).value = '\uAC15\uB0A8';
    await input.trigger('input');
    await flushPromises();

    const searchUrl = fetcher.mock.calls
      .map(([calledInput]) => String(calledInput))
      .find((url) => url.includes('/api/realestate/targets/search'));

    expect(searchUrl).toContain('q=%EA%B0%95%EB%82%A8');
    expect(searchUrl).toContain('limit=8');
    expect(searchUrl).toContain('mode=autocomplete');
  });

  it('opens eupmyeondong search results in transaction filtering instead of regional analysis', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost');

      if (url.pathname === '/api/realestate/targets/search') {
        return new Response(JSON.stringify({
          items: [{
            targetId: 'region-daejeon-seogu-galma',
            targetType: 'region',
            displayName: '\uB300\uC804\uAD11\uC5ED\uC2DC \uC11C\uAD6C \uAC08\uB9C8\uB3D9',
            slug: 'daejeon-seogu-galma',
            reviewState: 'approved',
            dataStatus: 'ok',
            regionLevel: 'eupmyeondong',
            parentTargetId: 'region-daejeon-seogu',
            legalDongCode: '3017010100',
            regionCode: null
          }]
        }));
      }
      if (url.pathname === '/api/realestate/daily-briefings/latest') {
        return new Response(JSON.stringify({ summaryHeadlines: [] }));
      }
      if (url.pathname === '/api/realestate/map/layers') {
        return new Response(JSON.stringify({ layerType: 'sigungu', periods: ['week'], targets: [] }));
      }
      if (url.pathname === '/api/realestate/dashboard/market-summary') {
        return new Response(JSON.stringify({ items: [] }));
      }
      if (url.pathname === '/api/realestate/newsroom') {
        return new Response(JSON.stringify({ items: [] }));
      }

      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountDashboardPage();
    await flushPromises();

    await wrapper.get('[data-testid="dashboard-search-input"]').trigger('focus');
    await wrapper.get('[data-testid="dashboard-search-input"]').setValue('\uAC08\uB9C8');
    await flushPromises();

    expect(wrapper.text()).toContain('실거래 지역');

    await wrapper.get('[data-testid="dashboard-search-result-region-daejeon-seogu-galma"]').trigger('pointerdown');
    await flushPromises();

    expect(wrapper.vm.$route.path).toBe('/realestate/transactions');
    expect(wrapper.vm.$route.query.region).toBe('30170');
    expect(wrapper.vm.$route.query.q).toBe('\uAC08\uB9C8\uB3D9');
  });

  it('renders dashboard headlines from the stored daily briefing API', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      const rawUrl = String(input);
      const url = new URL(rawUrl, 'http://localhost');

      if (url.pathname === '/api/realestate/daily-briefings/latest') {
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
        }));
      }
      if (url.pathname === '/api/realestate/reactions/rankings') {
        return new Response(JSON.stringify({ items: [] }));
      }
      if (url.pathname === '/api/realestate/dashboard/market-summary') {
        return new Response(JSON.stringify({ items: [] }));
      }
      if (url.pathname === '/api/realestate/newsroom') {
        return new Response(JSON.stringify({ items: [] }));
      }

      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountDashboardPage();
    await flushPromises();

    expect(wrapper.get('.daily-briefing-card .label').text()).toBe('Daily briefing');
    expect(wrapper.findAll('.daily-briefing-card .daily-briefing-headline-card strong').map((item) => item.text())).toEqual([
      '수도권 전세 압력 재부각',
      '서울 동남권 거래 회복 흐름',
      '경기 남부 공급·정책 이슈 집중'
    ]);
    expect(wrapper.findAll('.daily-briefing-card .daily-briefing-headline-index').map((item) => item.text())).toEqual([
      '01',
      '02',
      '03'
    ]);
    expect(wrapper.find('.daily-briefing-card .daily-briefing-list').exists()).toBe(false);
    expect(wrapper.get('.daily-briefing-cta').attributes('href')).toBe('/realestate/daily-briefing');
    expect(fetcher.mock.calls.some(([input]) => String(input).includes('/api/realestate/daily-briefings/latest'))).toBe(true);
  });

  it('stacks dashboard briefing headline cards to match the reaction panel height', () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toMatch(/\.daily-briefing-card\s*\{[^}]*align-self:\s*stretch;[^}]*height:\s*100%;/s);
    expect(styles).toMatch(
      /\.daily-briefing-dashboard-headlines\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\);[^}]*grid-template-rows:\s*repeat\(3,\s*minmax\(0,\s*1fr\)\);[^}]*flex:\s*1;/s
    );
    expect(styles).toMatch(/\.insight-grid\s*\{[^}]*gap:\s*34px;/s);
    expect(styles).toMatch(/\.news-macro-grid\s*\{[^}]*gap:\s*34px 34px;/s);
    expect(styles).toMatch(/\.daily-briefing-dashboard-headlines\s+\.daily-briefing-headline-card\s*\{[^}]*min-height:\s*0;/s);
    expect(styles).toMatch(/\.daily-briefing-cta\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+28px;/s);
    expect(styles).toMatch(/\.daily-briefing-cta\s*\{[^}]*background:\s*linear-gradient\(135deg,\s*#111827\s*0%,\s*#243244\s*100%\);/s);
    expect(styles).toMatch(/\.daily-briefing-cta::after\s*\{[^}]*content:\s*"→";/s);
    expect(styles).toMatch(/\.app-shell\.dark-mode \.daily-briefing-cta\s*\{[^}]*background:\s*linear-gradient\(135deg,\s*#fff7ed\s*0%,\s*#fed7aa/s);
    expect(styles).toMatch(/\.app-shell\.dark-mode \.daily-briefing-card \.daily-briefing-dashboard-headlines \.daily-briefing-headline-index\s*\{[^}]*background:/s);
    expect(styles).toMatch(/\.app-shell\.dark-mode \.daily-briefing-card \.daily-briefing-dashboard-headlines \.daily-briefing-headline-card:nth-child\(2\)\s*\{[^}]*--briefing-card-accent:\s*#60a5fa;/s);
    expect(styles).toMatch(/\.daily-briefing-dashboard-headlines\s+\.daily-briefing-headline-card\s*\{[^}]*border-radius:\s*10px;/s);
    expect(styles).toMatch(/\.daily-briefing-dashboard-headlines\s+\.daily-briefing-headline-card\s+small\s*\{[^}]*font-size:\s*13px;/s);
    expect(styles).toMatch(/\.daily-briefing-dashboard-headlines\s+\.daily-briefing-headline-card\s+strong\s*\{[^}]*font-size:\s*20px;/s);
    expect(styles).toMatch(
      /\.reaction-panel\s+\.mood-header\s*\{[^}]*min-height:\s*54px;[^}]*align-items:\s*center;[^}]*margin-bottom:\s*12px;/s
    );
    expect(styles.lastIndexOf('.daily-briefing-dashboard-headlines')).toBeGreaterThan(
      styles.indexOf('.daily-briefing-headline-grid')
    );
  });

  it('omits the reaction panel header actions from the dashboard summary view', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      const rawUrl = String(input);
      const url = new URL(rawUrl, 'http://localhost');

      if (url.pathname === '/api/realestate/daily-briefings/latest') {
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
        }));
      }
      if (url.pathname === '/api/realestate/reactions/rankings') {
        return new Response(JSON.stringify({ items: [] }));
      }

      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountDashboardPage();
    await flushPromises();

    expect(wrapper.get('.reaction-panel h3').text()).toBe('지역·단지 반응 한눈에');
    expect(wrapper.find('.reaction-panel .section-actions').exists()).toBe(false);
    expect(wrapper.find('.reaction-panel .mood-period-tabs').exists()).toBe(false);
    expect(wrapper.find('.reaction-panel .detail-link').exists()).toBe(false);
  });

  it('renders weekly gain top five regions with report-derived expectation and concern sentences', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      const rawUrl = String(input);
      const url = new URL(rawUrl, 'http://localhost');

      if (url.pathname === '/api/realestate/daily-briefings/latest') {
        return new Response(JSON.stringify({
          briefingId: 'daily-briefing-20260624-v1',
          briefingDate: '2026-06-24',
          title: 'Dashboard briefing',
          summaryHeadlines: ['Headline A', 'Headline B', 'Headline C'],
          sections: [],
          focusRegions: [],
          sourceItems: []
        }));
      }
      if (url.pathname === '/api/realestate/map/layers' && url.searchParams.get('layerType') === 'sigungu') {
        return new Response(JSON.stringify({
          layerType: 'sigungu',
          asOf: '2026-06-24T00:00:00Z',
          sourceLabel: 'REB R-ONE weekly apartment sale price index',
          dataStatus: 'ok',
          stale: false,
          periods: ['week'],
          targets: [
            {
              targetId: 'region-top-1',
              targetType: 'region',
              displayName: '경기도 화성시',
              regionLevel: 'sigungu',
              regionCode: '41111',
              periods: { week: { changePct: 1.24, sampleCount: 4, confidence: 0.91, provider: 'reb', asOf: '2026-06-17T00:00:00Z', dataStatus: 'ok', stale: false } }
            },
            {
              targetId: 'region-top-2',
              targetType: 'region',
              displayName: 'Top Two Region',
              regionLevel: 'sigungu',
              regionCode: '41112',
              periods: { week: { changePct: 0.95, sampleCount: 4, confidence: 0.88, provider: 'reb', asOf: '2026-06-17T00:00:00Z', dataStatus: 'ok', stale: false } }
            },
            {
              targetId: 'region-top-3',
              targetType: 'region',
              displayName: 'Top Three Region',
              regionLevel: 'sigungu',
              regionCode: '41113',
              periods: { week: { changePct: 0.72, sampleCount: 4, confidence: 0.86, provider: 'reb', asOf: '2026-06-17T00:00:00Z', dataStatus: 'ok', stale: false } }
            },
            {
              targetId: 'region-top-4',
              targetType: 'region',
              displayName: 'Top Four Region',
              regionLevel: 'sigungu',
              regionCode: '41114',
              periods: { week: { changePct: 0.51, sampleCount: 4, confidence: 0.84, provider: 'reb', asOf: '2026-06-17T00:00:00Z', dataStatus: 'ok', stale: false } }
            },
            {
              targetId: 'region-top-5',
              targetType: 'region',
              displayName: 'Top Five Region',
              regionLevel: 'sigungu',
              regionCode: '41115',
              periods: { week: { changePct: 0.33, sampleCount: 4, confidence: 0.82, provider: 'reb', asOf: '2026-06-17T00:00:00Z', dataStatus: 'ok', stale: false } }
            },
            {
              targetId: 'region-top-6',
              targetType: 'region',
              displayName: 'Hidden Sixth Region',
              regionLevel: 'sigungu',
              regionCode: '41116',
              periods: { week: { changePct: 0.22, sampleCount: 4, confidence: 0.8, provider: 'reb', asOf: '2026-06-17T00:00:00Z', dataStatus: 'ok', stale: false } }
            }
          ]
        }));
      }
      if (url.pathname.startsWith('/api/realestate/targets/') && url.pathname.endsWith('/regional-report')) {
        const targetId = decodeURIComponent(url.pathname.split('/')[4] ?? 'region-top-1');
        const isSecondRegion = targetId === 'region-top-2';
        return new Response(JSON.stringify({
          reportId: `report-${targetId}`,
          targetId,
          targetName: targetId === 'region-top-1' ? '경기도 화성시' : targetId,
          title: 'Top weekly region report',
          headline: 'GTX 역세권 수요와 정비사업 기대가 가격 흐름을 지지합니다.',
          summary: '전세압력과 공급부담은 단기 점검이 필요합니다.',
          body: '**평가** GTX 교통 개선과 정비사업 기대가 우세합니다.\n**전망** 공급부담과 대출 금리는 우려 요인입니다.',
          expectationPoints: isSecondRegion
            ? ['전세 안정 기대', '교통·산업축 실수요 확인', 'GTX 역세권 수요 유입']
            : ['화성시 실거래 회복', '교통·산업축 실수요 확인', 'GTX 역세권 수요 유입'],
          concernPoints: isSecondRegion
            ? ['입주 시점 전세 약세', '입주·전세 부담', '대출 금리 부담']
            : ['화성시 입주·전세 부담', '입주 시점 전세 약세', '대출 금리 부담'],
          sources: []
        }));
      }

      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountDashboardPage();
    await flushPromises();

    const cards = wrapper.findAll('.reaction-carousel-card');
    const card = cards[0];
    const labels = card.findAll('.kw-col-label span');
    const positivePoints = card.findAll('.kw-col-positive .report-point-item').map((point) => point.text());
    const negativePoints = card.findAll('.kw-col-negative .report-point-item').map((point) => point.text());
    const secondPositivePoints = cards[1].findAll('.kw-col-positive .report-point-item').map((point) => point.text());
    const secondNegativePoints = cards[1].findAll('.kw-col-negative .report-point-item').map((point) => point.text());
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(wrapper.get('.reaction-panel .label').text()).toBe('주간 상승률 TOP5');
    expect(cards).toHaveLength(5);
    expect(wrapper.findAll('.carousel-dot')).toHaveLength(5);
    expect(cards.map((item) => item.find('.carousel-region-name').text())).toEqual([
      '경기도 화성시',
      'Top Two Region',
      'Top Three Region',
      'Top Four Region',
      'Top Five Region'
    ]);
    expect(wrapper.text()).not.toContain('Hidden Sixth Region');
    expect(card.text()).toContain('+1.24%');
    expect(labels).toHaveLength(2);
    expect(positivePoints).toEqual(['화성시 실거래 회복', '교통·산업축 실수요 확인', 'GTX 역세권 수요 유입']);
    expect(negativePoints).toEqual(['화성시 입주·전세 부담', '입주 시점 전세 약세', '대출 금리 부담']);
    expect(secondPositivePoints).toEqual(['전세 안정 기대', '교통·산업축 실수요 확인', 'GTX 역세권 수요 유입']);
    expect(secondNegativePoints).toEqual(['입주 시점 전세 약세', '입주·전세 부담', '대출 금리 부담']);
    expect(card.attributes('href')).toBe('/realestate/map/region-gyeonggi?selectedTargetId=region-top-1&selectedRegionCode=41111&period=week');
    expect(wrapper.find('.carousel-change-badge').exists()).toBe(true);
    expect(wrapper.find('.carousel-mention-badge').exists()).toBe(false);
    expect(wrapper.find('.carousel-region-meta').exists()).toBe(false);
    expect(wrapper.find('.carousel-link-section').exists()).toBe(false);
    expect(wrapper.find('.reaction-carousel-card .reaction-track-wrap').exists()).toBe(false);
    expect(wrapper.find('.kw-word').exists()).toBe(false);
    expect(styles).toMatch(/\.carousel-region-name\s*\{[^}]*font-size:\s*25px;/s);
    expect(styles).toMatch(/\.carousel-change-badge\s*\{[^}]*display:\s*flex;[^}]*align-items:\s*baseline;[^}]*transform:\s*translateY\(-4px\);/s);
    expect(styles).toMatch(/\.kw-col-label\s+span\s*\{[^}]*font-size:\s*17px;[^}]*font-weight:\s*940;/s);
    expect(styles).toMatch(/\.report-point-list\s*\{[^}]*overflow-y:\s*auto;/s);
    expect(styles).toMatch(/\.report-point-list\s*\{[^}]*justify-content:\s*stretch;/s);
    expect(styles).toMatch(/\.report-point-item\s*\{[^}]*flex:\s*1 1 0;[^}]*min-height:\s*54px;/s);
    expect(styles).not.toMatch(/\.report-point-item\s*\{[^}]*white-space/s);
    expect(styles).not.toContain('.carousel-mention-badge');
    expect(styles).not.toContain('.carousel-link-section');
    expect(styles).not.toContain('.kw-word');
    expect(fetcher.mock.calls.some(([input]) => String(input).includes('/api/realestate/reactions/rankings'))).toBe(false);
    expect(fetcher.mock.calls.filter(([input]) => String(input).includes('/regional-report'))).toHaveLength(5);
  });

  it('renders the live drawer as weekly top gain and loss regions instead of reaction mentions', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      const rawUrl = String(input);
      const url = new URL(rawUrl, 'http://localhost');

      if (url.pathname === '/api/realestate/map/layers' && url.searchParams.get('layerType') === 'sigungu') {
        return new Response(JSON.stringify({
          layerType: 'sigungu',
          asOf: '2026-06-24T00:00:00Z',
          sourceLabel: 'REB R-ONE weekly apartment sale price index',
          dataStatus: 'ok',
          stale: false,
          periods: ['week', 'month'],
          targets: [
            {
              targetId: 'region-seoul-jongno',
              targetType: 'region',
              displayName: '서울특별시 종로구',
              regionLevel: 'sigungu',
              regionCode: '11110',
              periods: {
                week: {
                  changePct: 0.42,
                  sampleCount: 2,
                  confidence: 0.82,
                  provider: 'reb',
                  sourceLabel: 'REB R-ONE weekly apartment sale price index',
                  asOf: '2026-06-17T00:00:00Z',
                  dataStatus: 'ok',
                  stale: false
                }
              }
            },
            {
              targetId: 'region-gyeonggi-jangan',
              targetType: 'region',
              displayName: '경기도 수원시 장안구',
              regionLevel: 'sigungu',
              regionCode: '41111',
              geometryId: '31011',
              parentTargetId: 'region-gyeonggi',
              periods: {
                week: {
                  changePct: 1.24,
                  sampleCount: 4,
                  confidence: 0.91,
                  provider: 'reb',
                  sourceLabel: 'REB R-ONE weekly apartment sale price index',
                  asOf: '2026-06-17T00:00:00Z',
                  dataStatus: 'ok',
                  stale: false
                }
              }
            },
            {
              targetId: 'region-gangwon-chuncheon',
              targetType: 'region',
              displayName: '강원특별자치도 춘천시',
              regionLevel: 'sigungu',
              regionCode: '51110',
              geometryId: '32010',
              parentTargetId: 'region-gangwon',
              periods: {
                week: {
                  changePct: -0.87,
                  sampleCount: 3,
                  confidence: 0.88,
                  provider: 'reb',
                  sourceLabel: 'REB R-ONE weekly apartment sale price index',
                  asOf: '2026-06-17T00:00:00Z',
                  dataStatus: 'ok',
                  stale: false
                }
              }
            }
          ]
        }));
      }
      if (url.pathname === '/api/realestate/daily-briefings/latest') {
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
        }));
      }
      if (url.pathname === '/api/realestate/reactions/rankings') {
        return new Response(JSON.stringify({
          items: [
            {
              rank: 1,
              targetId: 'region-mention-only',
              targetType: 'region',
              displayName: '언급 많은 지역',
              mentionCount: 20,
              mentionDeltaPct: 100,
              reactionDirectionRatio: { expectation: 0.6, concern: 0.2, neutral: 0.2 },
              heatScore: 90,
              confidence: 0.8,
              sourceCount: 2,
              sourceSkew: 0.2,
              coverageStatus: 'partial',
              stale: false,
              issueMix: []
            }
          ]
        }));
      }

      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountDashboardPage();
    await flushPromises();

    const titleBand = wrapper.get('.hot-region-title-band');
    const hotPanel = wrapper.get('.hot-region-panel');
    const hotPanelText = hotPanel.text();
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(titleBand.text()).toBe('라이브 패널 · 주간 가격 흐름');
    expect(wrapper.find('.hot-region-shell').exists()).toBe(true);
    expect(hotPanelText).toContain('라이브 패널 · 주간 가격 흐름');
    expect(titleBand.element.closest('.hot-region-panel')).toBe(hotPanel.element);
    expect(hotPanelText).toContain('이번주 가장 많이 상승한 지역');
    expect(hotPanelText).toContain('경기도 수원시 장안구');
    expect(hotPanelText).toContain('+1.24%');
    expect(hotPanelText).toContain('이번주 가장 많이 하락한 지역');
    expect(hotPanelText).toContain('강원특별자치도 춘천시');
    expect(hotPanelText).toContain('-0.87%');
    expect(hotPanelText).toContain('최근 1주 · 2026-06-17 기준');
    expect(wrapper.get('a.hot-region-movement-up').attributes('href')).toBe('/realestate/map/region-gyeonggi?selectedTargetId=region-gyeonggi-jangan&selectedRegionCode=31011&period=week');
    expect(wrapper.get('a.hot-region-movement-down').attributes('href')).toBe('/realestate/map/region-gangwon?selectedTargetId=region-gangwon-chuncheon&selectedRegionCode=32010&period=week');
    expect(wrapper.get('.hot-region-reference').text()).toBe('최근 1주 · 2026-06-17 기준');
    expect(wrapper.find('.hot-region-divider').exists()).toBe(true);
    expect(hotPanelText).not.toContain('상승률');
    expect(hotPanelText).not.toContain('표본');
    expect(hotPanelText).not.toContain('데이터 근거');
    expect(hotPanelText).not.toContain('주간 가격지수 변화율');
    expect(hotPanelText).not.toContain('신뢰도');
    expect(hotPanelText).not.toContain('출처');
    expect(hotPanelText).not.toContain('상태');
    expect(hotPanelText).not.toContain('언급');
    expect(hotPanelText).not.toContain('열기');
    expect(hotPanelText).not.toContain('시장');
    expect(styles).toMatch(/\.side-drawer\s*\{[^}]*padding-top:\s*66px;/s);
    expect(styles).toMatch(/\.hot-region-title-band\s*\{[^}]*background:\s*#ff6a00;[^}]*color:\s*#111827;/s);
    expect(styles).toMatch(/\.hot-region-panel\s*\{[^}]*gap:\s*0;[^}]*overflow:\s*hidden;/s);
    expect(styles).toMatch(/\.hot-region-movement-grid\s*\{[^}]*grid-template-rows:\s*minmax\(0,\s*1fr\)\s+auto\s+minmax\(0,\s*1fr\);/s);
    expect(styles).toMatch(/\.hot-region-movement\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+auto;/s);
    expect(styles).toMatch(/\.hot-region-movement span\s*\{[^}]*grid-column:\s*1\s*\/\s*-1;[^}]*grid-row:\s*1;[^}]*word-break:\s*keep-all;/s);
    expect(styles).toMatch(/\.hot-region-movement h3\s*\{[^}]*grid-row:\s*2;[^}]*align-self:\s*start;/s);
    expect(styles).toMatch(/\.hot-region-movement strong\s*\{[^}]*grid-row:\s*3;[^}]*align-self:\s*end;[^}]*justify-self:\s*end;[^}]*text-align:\s*right;/s);
    expect(styles).toMatch(/\.hot-region-reference\s*\{[^}]*justify-self:\s*end;[^}]*text-align:\s*right;/s);
    expect(fetcher.mock.calls.some(([input]) => String(input).includes('/api/realestate/map/layers?layerType=sigungu'))).toBe(true);
  });

  it('keeps video and blog feed rows aligned with news and report rows', () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');
    const styleEl = document.createElement('style');
    styleEl.textContent = styles;
    document.head.append(styleEl);

    const host = document.createElement('div');
    host.innerHTML = `
      <article class="panel content-feed-card live-feed-card">
        <div class="feed-list">
          <a class="feed-row">
            <span class="site-icon real-icon news-source"></span>
          </a>
        </div>
      </article>
      <article class="panel content-feed-card report-feed-card">
        <div class="feed-list">
          <a class="feed-row">
            <span class="site-icon real-icon news-source"></span>
          </a>
        </div>
      </article>
      <article class="panel external-content-panel content-feed-card video-feed-card">
        <div class="feed-list">
          <a class="feed-row">
            <span class="site-icon real-icon source-badge youtube"></span>
          </a>
        </div>
      </article>
      <article class="panel external-content-panel content-feed-card link-feed-card">
        <div class="feed-list">
          <a class="feed-row">
            <span class="site-icon real-icon source-badge naver-blog"></span>
          </a>
        </div>
      </article>
    `;
    document.body.append(host);

    const feedLists = Array.from(host.querySelectorAll<HTMLElement>('.feed-list'));
    const icons = Array.from(host.querySelectorAll<HTMLElement>('.site-icon'));
    const [newsList, reportList, videoList, linkList] = feedLists.map((list) => getComputedStyle(list));
    const [newsIcon, reportIcon, videoIcon, linkIcon] = icons.map((icon) => getComputedStyle(icon));

    expect(videoList.paddingLeft).toBe(newsList.paddingLeft);
    expect(linkList.paddingLeft).toBe(newsList.paddingLeft);
    expect(videoList.paddingRight).toBe(reportList.paddingRight);
    expect(linkList.paddingRight).toBe(reportList.paddingRight);
    expect(videoIcon.width).toBe(newsIcon.width);
    expect(linkIcon.width).toBe(reportIcon.width);

    host.remove();
    styleEl.remove();
  });

  it('refreshes report, video, and link lanes when the newsroom batch pushes an update', async () => {
    vi.stubGlobal('EventSource', TestEventSource);
    let hasBatchData = false;
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      const rawUrl = String(input);
      const url = new URL(rawUrl, 'http://localhost');

      if (url.pathname === '/api/realestate/reactions/rankings') {
        return new Response(JSON.stringify({ items: [] }));
      }
      if (url.pathname === '/api/realestate/dashboard/market-summary') {
        return new Response(JSON.stringify({ items: [] }));
      }
      if (url.pathname === '/api/realestate/newsroom') {
        if (!hasBatchData) {
          return new Response(JSON.stringify({ items: [] }));
        }

        const feed = url.searchParams.get('feed');
        const contentByFeed = {
          news: {
            contentId: 'dashboard-news-item',
            sourceId: 'google_news_rss',
            contentType: 'news',
            title: 'Dashboard news item',
            url: 'https://news.example.com/item',
            domain: 'news.example.com',
            publishedAt: '2026-06-23T00:00:00Z',
            dataStatus: 'ok'
          },
          report: {
            contentId: 'dashboard-report-item',
            sourceId: 'manual_curated:report',
            contentType: 'report',
            title: 'Dashboard report item',
            url: 'https://www.kbfg.com/report',
            domain: 'www.kbfg.com',
            publishedAt: '2026-06-23T00:00:00Z',
            dataStatus: 'curated'
          },
          video: {
            contentId: 'dashboard-video-item',
            sourceId: 'manual_curated:youtube',
            contentType: 'video',
            title: 'Dashboard video item',
            url: 'https://www.youtube.com/watch?v=dashboard',
            domain: 'www.youtube.com',
            publishedAt: '2026-06-23T00:00:00Z',
            dataStatus: 'curated'
          },
          link: {
            contentId: 'dashboard-link-item',
            sourceId: 'manual_curated:blog',
            contentType: 'link',
            title: 'Dashboard blog item',
            url: 'https://brunch.co.kr/@dashboard/1',
            domain: 'brunch.co.kr',
            publishedAt: '2026-06-23T00:00:00Z',
            dataStatus: 'curated'
          }
        } as const;

        return new Response(JSON.stringify({
          items: feed && feed in contentByFeed ? [contentByFeed[feed as keyof typeof contentByFeed]] : []
        }));
      }

      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountDashboardPage();

    expect(TestEventSource.instances[0]?.url).toBe('/api/realestate/batch-updates/stream');
    expect(wrapper.text()).not.toContain('Dashboard report item');

    hasBatchData = true;
    TestEventSource.instances[0].dispatch('realestate-batch-update', {
      topic: 'newsroom',
      acceptedItems: 4,
      refreshedAt: '2026-06-23T00:00:00Z'
    });
    await flushPromises();

    expect(wrapper.text()).toContain('Dashboard news item');
    expect(wrapper.text()).toContain('Dashboard report item');
    expect(wrapper.text()).toContain('Dashboard video item');
    expect(wrapper.text()).toContain('Dashboard blog item');
    expect(fetcher.mock.calls.some(([input]) => String(input).includes('feed=report'))).toBe(true);
    expect(fetcher.mock.calls.some(([input]) => String(input).includes('feed=video'))).toBe(true);
    expect(fetcher.mock.calls.some(([input]) => String(input).includes('feed=link'))).toBe(true);

    wrapper.unmount();
    expect(TestEventSource.instances[0].close).toHaveBeenCalled();
  });
});
