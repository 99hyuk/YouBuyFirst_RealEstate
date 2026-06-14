import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import IndicatorsPage from '../pages/IndicatorsPage.vue';
import {
  fetchRealEstateIndicatorOverview,
  mergeIndicatorFreshnessRows,
  mergeIndicatorGroups
} from '../lib/realestate-indicators';

const mountIndicatorsPage = async (path = '/indicators') => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/indicators', component: IndicatorsPage },
      { path: '/indicators/:category', component: IndicatorsPage }
    ]
  });

  router.push(path);
  await router.isReady();

  const wrapper = mount(IndicatorsPage, {
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

describe('real-estate indicators API adapter', () => {
  it('fetches indicator overview with period and legal dong filters', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      period: 'month',
      dataStatus: 'ok',
      asOf: '2026-06-01',
      groups: [
        {
          id: 'price-transaction',
          label: 'price & volume',
          title: '가격 및 거래량',
          headline: '실거래와 전월세 공개 데이터로 가격 흐름의 최신 관측값을 확인합니다',
          change: '최신',
          tone: 'up',
          summary: '실거래 기반',
          chips: ['매매 실거래 9.15억원'],
          metrics: [{ name: '매매 실거래', value: '9.15억원', tone: 'up' }],
          dataStatus: 'ok',
          stale: false,
          provider: 'molit',
          asOf: '2026-06-01'
        }
      ],
      freshnessRows: [
        { source: '국토부 실거래가', state: '공공데이터 반영', used: '매매/전월세 실거래' }
      ]
    })));

    const overview = await fetchRealEstateIndicatorOverview(
      { legalDongCode: '11740', period: 'month' },
      fetcher
    );

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/indicators?legalDongCode=11740&period=month');
    expect(overview.dataStatus).toBe('ok');
    expect(overview.groups[0].id).toBe('price-transaction');
    expect(overview.groups[0].provider).toBe('molit');
  });

  it('overlays API groups but keeps fallback categories explicit', () => {
    const merged = mergeIndicatorGroups(
      [
        {
          id: 'price-transaction',
          label: 'price & volume',
          title: '가격 및 거래량',
          headline: 'API headline',
          change: '최신',
          tone: 'up',
          summary: 'API summary',
          chips: ['매매 실거래 9.15억원'],
          metrics: [{ name: '매매 실거래', value: '9.15억원', tone: 'up' }],
          dataStatus: 'ok',
          stale: false,
          provider: 'molit',
          asOf: '2026-06-01'
        }
      ],
      [
        {
          id: 'price-transaction',
          label: 'price & volume',
          title: '가격 및 거래량',
          headline: 'fallback headline',
          change: '+0.31%',
          tone: 'up',
          summary: 'fallback summary',
          chips: ['매매가격지수 101.8'],
          metrics: [{ name: '매매가격지수', value: '101.8', tone: 'up' }]
        },
        {
          id: 'supply-demand',
          label: 'supply balance',
          title: '공급 및 수급',
          headline: 'fallback supply',
          change: '-3.2%',
          tone: 'down',
          summary: 'fallback supply summary',
          chips: ['미분양 5.7만호'],
          metrics: [{ name: '미분양', value: '5.7만호', tone: 'down' }]
        }
      ]
    );

    expect(merged).toHaveLength(2);
    expect(merged[0].headline).toBe('API headline');
    expect(merged[0].statusLabel).toBe('공공데이터 반영');
    expect(merged[1].headline).toBe('fallback supply');
    expect(merged[1].statusLabel).toBe('mock fallback');
  });

  it('uses API freshness rows only when available', () => {
    const fallback = [{ source: '국토부 실거래가', state: '신고·공개 지연', used: '실거래가 지수·거래량' }];

    expect(mergeIndicatorFreshnessRows([], fallback)).toEqual(fallback);
    expect(mergeIndicatorFreshnessRows(
      [{ source: '국토부 실거래가', state: '공공데이터 반영', used: '매매/전월세 실거래' }],
      fallback
    )).toEqual([{ source: '국토부 실거래가', state: '공공데이터 반영', used: '매매/전월세 실거래' }]);
  });
});

describe('IndicatorsPage API connection', () => {
  it('renders live public-data indicator groups before fixture fallback labels', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      period: 'month',
      dataStatus: 'ok',
      asOf: '2026-06-01',
      groups: [
        {
          id: 'price-transaction',
          label: 'price & volume',
          title: '가격 및 거래량',
          headline: '실거래 공개 데이터로 가격 흐름을 확인합니다',
          change: '최신',
          tone: 'up',
          summary: '국토부 실거래 기반',
          chips: ['매매 실거래 9.15억원', '전월세 실거래 보증금 5.20억원 / 월세 135만원'],
          metrics: [{ name: '매매 실거래', value: '9.15억원', tone: 'up' }],
          dataStatus: 'ok',
          stale: false,
          provider: 'molit',
          asOf: '2026-06-01'
        }
      ],
      freshnessRows: [
        { source: '국토부 실거래가', state: '공공데이터 반영', used: '매매/전월세 실거래' }
      ]
    })));
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountIndicatorsPage();

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/indicators?period=month');
    expect(wrapper.text()).toContain('실거래 공개 데이터로 가격 흐름을 확인합니다');
    expect(wrapper.text()).toContain('매매 실거래 9.15억원');
    expect(wrapper.text()).toContain('공공데이터 반영');
    expect(wrapper.text()).toContain('API 반영 · 2026-06-01');
  });
});
