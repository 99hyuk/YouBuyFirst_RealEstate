import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import IndicatorsPage from '../pages/IndicatorsPage.vue';
import {
  buildIndicatorAnomalyRows,
  buildIndicatorRegionTiles,
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
    expect(merged[1].change).toBe('-3.2%');
    expect(merged[1].metrics[0].value).toBe('5.7만호');
    expect(merged[1].statusLabel).toBe('연동 대기');
  });

  it('uses API freshness rows and marks fallback rows as insufficient', () => {
    const fallback = [{ source: '국토부 실거래가', state: '신고·공개 지연', used: '실거래가 지수·거래량' }];

    expect(mergeIndicatorFreshnessRows([], fallback)).toEqual([
      { source: '국토부 실거래가', state: '수집 전/insufficient', used: '실거래가 지수·거래량' }
    ]);
    expect(mergeIndicatorFreshnessRows(
      [{ source: '국토부 실거래가', state: '공공데이터 반영', used: '매매/전월세 실거래' }],
      fallback
    )).toEqual([{ source: '국토부 실거래가', state: '공공데이터 반영', used: '매매/전월세 실거래' }]);
  });

  it('builds regional direction tiles from live map layer periods only', () => {
    const tiles = buildIndicatorRegionTiles({
      layerType: 'sido',
      periods: ['month'],
      targets: [
        {
          targetId: 'region-seoul',
          targetType: 'region',
          displayName: '서울',
          regionCode: '11',
          periods: {
            month: {
              changePct: 0.31,
              sampleCount: 12,
              confidence: 0.82,
              provider: 'reb',
              sourceLabel: 'REB R-ONE',
              dataStatus: 'partial',
              stale: false
            }
          }
        },
        {
          targetId: 'region-seed',
          targetType: 'region',
          displayName: 'seed 지역',
          regionCode: '99',
          periods: {
            month: {
              changePct: 1.2,
              sampleCount: 0,
              confidence: 0.2,
              provider: 'seed',
              sourceLabel: 'mock heat',
              dataStatus: 'mock',
              stale: true
            }
          }
        }
      ]
    });

    expect(tiles).toHaveLength(1);
    expect(tiles[0]).toMatchObject({
      name: '서울',
      change: '+0.31%',
      keyword: 'REB R-ONE',
      statusLabel: '부분 반영'
    });
  });

  it('builds anomaly rows from reaction ranking and map layer comparison', () => {
    const rows = buildIndicatorAnomalyRows(
      {
        layerType: 'sido',
        periods: ['month'],
        targets: [
          {
            targetId: 'region-seoul',
            targetType: 'region',
            displayName: '서울',
            regionCode: '11',
            periods: {
              month: {
                changePct: -0.22,
                sampleCount: 8,
                confidence: 0.72,
                provider: 'reb',
                dataStatus: 'partial',
                stale: false
              }
            }
          }
        ]
      },
      {
        window: '24h',
        items: [
          {
            rank: 1,
            targetId: 'region-seoul',
            targetType: 'region',
            displayName: '서울',
            mentionCount: 10,
            mentionDeltaPct: 25,
            reactionDirectionRatio: { expectation: 0.7, concern: 0.2, neutral: 0.1 },
            heatScore: 81,
            confidence: 0.8,
            sourceCount: 2,
            sourceSkew: 0.2,
            coverageStatus: 'partial',
            stale: false,
            issueMix: [{ issueKey: 'policy', label: '정책', share: 0.5, direction: 'expectation', confidence: 0.7 }]
          },
          {
            rank: 2,
            targetId: 'region-daegu',
            targetType: 'region',
            displayName: '대구',
            mentionCount: 8,
            mentionDeltaPct: 12,
            reactionDirectionRatio: { expectation: 0.2, concern: 0.6, neutral: 0.2 },
            heatScore: 64,
            confidence: 0.7,
            sourceCount: 1,
            sourceSkew: 0.4,
            coverageStatus: 'partial',
            stale: false,
            issueMix: [{ issueKey: 'supply', label: '공급', share: 0.4, direction: 'concern', confidence: 0.6 }]
          }
        ]
      }
    );

    expect(rows).toHaveLength(2);
    expect(rows[0]).toMatchObject({
      target: '서울',
      type: '지표 하락 · 기대 우세',
      price: '-0.22%',
      reaction: '기대 70%',
      reason: '정책 · 부분 반영'
    });
    expect(rows[1]).toMatchObject({
      target: '대구',
      type: '시장 사실 대기 · 반응만 관찰',
      price: '시장 사실 수집 전'
    });
  });
});

describe('IndicatorsPage schedule calendar', () => {
  it('renders official schedule calendar and source links without indicator API calls', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({})));
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountIndicatorsPage();

    expect(fetcher).not.toHaveBeenCalled();
    expect(wrapper.find('.indicator-calendar-page').exists()).toBe(true);
    expect(wrapper.text()).toContain('주요 일정');
    expect(wrapper.text()).toContain('가격지수, 실거래, 공급, 금리, 청약 일정을 캘린더로 확인합니다.');
    expect(wrapper.find('.calendar-agenda-panel').exists()).toBe(false);
    expect(wrapper.text()).toContain('공식 출처');
    expect(wrapper.text()).toContain('한국부동산원 R-ONE');
    expect(wrapper.text()).toContain('국토교통부 실거래가 공개시스템');
    expect(wrapper.text()).toContain('청약Home');
    expect(wrapper.findAll('.calendar-event-pill').length).toBeGreaterThanOrEqual(8);
    expect(wrapper.findAll('.schedule-source-card')).toHaveLength(6);
    expect(wrapper.text()).not.toContain('지표 반영');
    expect(wrapper.text()).not.toContain('지표와 반응이 엇갈린 지역');
  });

  it('keeps legacy indicator detail routes on the schedule screen', async () => {
    const wrapper = await mountIndicatorsPage('/indicators/price-transaction');

    expect(wrapper.text()).toContain('주요 일정');
    expect(wrapper.text()).toContain('월간 일정 캘린더');
    expect(wrapper.text()).toContain('공식 출처');
    expect(wrapper.text()).not.toContain('가격 및 거래량 상세 지표');
  });
});
