import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
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
import { fetchMarketDataSchedules } from '../lib/realestate-schedules';

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
  vi.restoreAllMocks();
  TestEventSource.instances = [];
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
  it('fetches market data schedules by month for the calendar screen', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      month: '2026-06',
      scheduleEvents: [],
      sourceLinks: []
    })));

    const response = await fetchMarketDataSchedules({ month: '2026-06' }, fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/market-data-schedules?month=2026-06');
    expect(response.month).toBe('2026-06');
  });

  it('renders official schedule calendar and source links from the schedule API', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      month: '2026-06',
      scheduleEvents: [
        {
          id: 'reb-r-one-published-pres01-3931',
          date: '2026-06-18',
          title: '2026년 6월 15일 기준 주간아파트가격 동향',
          category: '가격지수',
          source: '한국부동산원 R-ONE',
          summary: '한국부동산원 주간아파트가격동향조사 공표자료입니다.',
          link: 'https://www.reb.or.kr/r-one/portal/bbs/pres/selectBulletinPage.do?bbsCd=PRES&seq=3931&noticeYn=N',
          tone: 'market',
          status: '공표 확인',
          dataStatus: 'published',
          stale: false
        },
        {
          id: 'applyhome-published-2026000289',
          date: '2026-06-23',
          title: '신제주 동문디이스트 시그니처원Ⅱ 입주자모집공고',
          category: '청약',
          source: '청약Home',
          summary: '모집공고일 2026-06-23, 청약기간 2026-07-03~2026-07-06, 당첨자 발표 2026-07-10인 청약Home 공고입니다.',
          link: 'https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancDetail.do?houseManageNo=2026000289&pblancNo=2026000289',
          tone: 'subscription',
          status: '공표 확인',
          dataStatus: 'published',
          stale: false
        }
      ],
      sourceLinks: [
        {
          id: 'reb-r-one',
          title: '한국부동산원 R-ONE',
          label: '가격지수·공표일정',
          link: 'https://www.reb.or.kr/r-one/portal/main/indexPage.do',
          status: '확인 완료',
          stale: false
        },
        {
          id: 'applyhome',
          title: '청약Home',
          label: '청약·분양',
          link: 'https://applyhome.co.kr/',
          status: '확인 완료',
          stale: false
        }
      ]
    })));
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountIndicatorsPage();

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/market-data-schedules?month=2026-06');
    expect(wrapper.find('.indicator-calendar-page').exists()).toBe(true);
    expect(wrapper.text()).toContain('주요 일정');
    expect(wrapper.text()).toContain('가격·거래현황, 공급, 금융, 청약, 정책·공시 일정을 캘린더로 확인합니다.');
    expect(wrapper.text()).not.toContain('공식 통계 확인');
    expect(wrapper.find('.calendar-primary-link').exists()).toBe(false);
    expect(wrapper.find('.calendar-agenda-panel').exists()).toBe(false);
    expect(wrapper.text()).toContain('공식 출처');
    expect(wrapper.text()).toContain('한국부동산원 R-ONE');
    expect(wrapper.text()).toContain('청약Home');
    expect(wrapper.findAll('.calendar-event-strip')).toHaveLength(2);
    expect(wrapper.findAll('.calendar-event-card')).toHaveLength(2);
    expect(wrapper.text()).not.toContain('주요 공개·점검 일정');
    expect(wrapper.find('.calendar-tone-legend').exists()).toBe(true);
    expect(wrapper.find('.calendar-tone-legend').text()).toContain('가격·공시');
    expect(wrapper.find('.calendar-tone-legend').text()).toContain('거래현황');
    expect(wrapper.find('.calendar-tone-legend').text()).toContain('공급');
    expect(wrapper.find('.calendar-tone-legend').text()).toContain('금융');
    expect(wrapper.find('.calendar-tone-legend').text()).toContain('정책');
    expect(wrapper.find('.calendar-tone-legend').text()).toContain('청약');
    expect(wrapper.find('.calendar-event-strip').text()).toContain('2026년 6월 15일 기준 주간아파트가격 동향');
    expect(wrapper.find('.calendar-event-strip').text()).toContain('한국부동산원 주간아파트가격동향조사 공표자료입니다.');
    expect(wrapper.text()).toContain('한국부동산원 주간아파트가격동향조사 공표자료입니다.');
    expect(wrapper.text()).toContain('모집공고일 2026-06-23, 청약기간 2026-07-03~2026-07-06, 당첨자 발표 2026-07-10인 청약Home 공고입니다.');
    expect(wrapper.find('.calendar-event-strip[href]').exists()).toBe(false);
    expect(wrapper.find('.calendar-event-card[href="https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancDetail.do?houseManageNo=2026000289&pblancNo=2026000289"]').exists()).toBe(true);
    expect(wrapper.find('.calendar-event-card[href="https://www.reb.or.kr/r-one/portal/bbs/pres/selectBulletinPage.do?bbsCd=PRES&seq=3931&noticeYn=N"]').exists()).toBe(true);
    expect(wrapper.find('.calendar-event-card[href="https://applyhome.co.kr/"]').exists()).toBe(false);
    expect(wrapper.findAll('.schedule-source-card')).toHaveLength(2);
    expect(wrapper.text()).not.toContain('지표 반영');
    expect(wrapper.text()).not.toContain('지표와 반응이 엇갈린 지역');
  });

  it('refreshes the visible schedule when the batch pipeline pushes an update event', async () => {
    vi.stubGlobal('EventSource', TestEventSource);
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        month: '2026-06',
        scheduleEvents: [],
        sourceLinks: []
      })))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        month: '2026-06',
        scheduleEvents: [
          {
            id: 'bok-rate-2026-06-12',
            date: '2026-06-12',
            title: '금리·통화정책 일정 확인',
            category: '금융',
            source: '한국은행',
            summary: '기준금리와 통화정책 방향을 확인합니다.',
            link: 'https://www.bok.or.kr/',
            tone: 'finance',
            status: '공표 확인',
            dataStatus: 'published',
            stale: false
          }
        ],
        sourceLinks: []
      })));
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountIndicatorsPage();

    expect(TestEventSource.instances[0]?.url).toBe('/api/realestate/batch-updates/stream');
    expect(wrapper.text()).not.toContain('금리·통화정책 일정 확인');

    TestEventSource.instances[0].dispatch('realestate-batch-update', {
      topic: 'market-data-schedules',
      month: '2026-06'
    });
    await flushPromises();

    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(wrapper.findAll('.calendar-event-strip')).toHaveLength(1);
    expect(wrapper.findAll('.calendar-event-card')).toHaveLength(1);
    expect(wrapper.text()).toContain('금리·통화정책 일정 확인');
    expect(wrapper.find('.calendar-event-strip').text()).toContain('기준금리와 통화정책 방향을 확인합니다.');
  });

  it('jumps from calendar events to matching list cards while list cards keep source links', async () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: scrollIntoView
    });
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({
      month: '2026-06',
      scheduleEvents: [
        {
          id: 'reb-r-one-published-pres01-3931',
          date: '2026-06-18',
          title: '2026년 6월 15일 기준 주간아파트가격 동향',
          category: '가격지수',
          source: '한국부동산원 R-ONE',
          summary: '한국부동산원 주간아파트가격동향조사 공표자료입니다.',
          link: 'https://www.reb.or.kr/r-one/portal/bbs/pres/selectBulletinPage.do?bbsCd=PRES&seq=3931&noticeYn=N',
          tone: 'market',
          status: '공표 확인',
          dataStatus: 'published',
          stale: false
        }
      ],
      sourceLinks: []
    }))));

    const wrapper = await mountIndicatorsPage();
    const strip = wrapper.get('.calendar-event-strip');
    const card = wrapper.get('[data-schedule-event-id="reb-r-one-published-pres01-3931"]');

    expect(strip.element.tagName).toBe('BUTTON');
    expect(strip.attributes('href')).toBeUndefined();
    expect(card.element.tagName).toBe('A');
    expect(card.attributes('href')).toBe('https://www.reb.or.kr/r-one/portal/bbs/pres/selectBulletinPage.do?bbsCd=PRES&seq=3931&noticeYn=N');

    await strip.trigger('click');
    await flushPromises();

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' });
    expect(card.classes()).toContain('requested');
  });

  it('moves to adjacent months and refreshes the calendar and schedule list', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        month: '2026-06',
        scheduleEvents: [
          {
            id: 'june-schedule',
            date: '2026-06-12',
            title: '6월 금리 일정 확인',
            category: '금융',
            source: '한국은행',
            summary: '6월 기준금리 일정을 확인합니다.',
            link: 'https://www.bok.or.kr/portal/singl/crncyPolicyDrcMtg/listYear.do?menuNo=200755&mtgSe=A',
            tone: 'finance',
            status: '공식 일정',
            dataStatus: 'scheduled',
            stale: false
          }
        ],
        sourceLinks: []
      })))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        month: '2026-07',
        scheduleEvents: [
          {
            id: 'july-schedule',
            date: '2026-07-05',
            title: '7월 실거래 데이터 점검',
            category: '실거래',
            source: '국토교통부 실거래가 공개시스템',
            summary: '7월 신고 거래 반영 여부를 확인합니다.',
            link: 'https://stat.molit.go.kr/portal/cate/viewChk.do?hRsId=32',
            tone: 'deal',
            status: '공식 일정',
            dataStatus: 'scheduled',
            stale: false
          }
        ],
        sourceLinks: []
      })))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        month: '2026-06',
        scheduleEvents: [
          {
            id: 'june-schedule',
            date: '2026-06-12',
            title: '6월 금리 일정 확인',
            category: '금융',
            source: '한국은행',
            summary: '6월 기준금리 일정을 확인합니다.',
            link: 'https://www.bok.or.kr/portal/singl/crncyPolicyDrcMtg/listYear.do?menuNo=200755&mtgSe=A',
            tone: 'finance',
            status: '공식 일정',
            dataStatus: 'scheduled',
            stale: false
          }
        ],
        sourceLinks: []
      })));
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountIndicatorsPage();

    expect(wrapper.text()).toContain('2026.06');
    expect(wrapper.text()).toContain('6월 금리 일정 확인');

    await wrapper.get('[aria-label="다음 달 일정 보기"]').trigger('click');
    await flushPromises();

    expect(fetcher).toHaveBeenLastCalledWith('/api/realestate/market-data-schedules?month=2026-07');
    expect(wrapper.text()).toContain('2026.07');
    expect(wrapper.text()).toContain('7월 실거래 데이터 점검');
    expect(wrapper.text()).not.toContain('6월 금리 일정 확인');
    expect(wrapper.findAll('.calendar-event-strip')).toHaveLength(1);
    expect(wrapper.findAll('.calendar-event-card')).toHaveLength(1);

    await wrapper.get('[aria-label="이전 달 일정 보기"]').trigger('click');
    await flushPromises();

    expect(fetcher).toHaveBeenLastCalledWith('/api/realestate/market-data-schedules?month=2026-06');
    expect(wrapper.text()).toContain('2026.06');
    expect(wrapper.text()).toContain('6월 금리 일정 확인');
    expect(wrapper.text()).not.toContain('7월 실거래 데이터 점검');
  });

  it('keeps legacy indicator detail routes on the schedule screen', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({
      month: '2026-06',
      scheduleEvents: [],
      sourceLinks: []
    }))));

    const wrapper = await mountIndicatorsPage('/indicators/price-transaction');

    expect(wrapper.text()).toContain('주요 일정');
    expect(wrapper.text()).toContain('월간 일정 캘린더');
    expect(wrapper.text()).toContain('공식 출처');
    expect(wrapper.text()).not.toContain('가격 및 거래량 상세 지표');
  });

  it('docks official sources to the right half in a three-column grid', async () => {
    const wrapper = await mountIndicatorsPage();
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(wrapper.find('.schedule-source-section').exists()).toBe(true);
    expect(wrapper.findAll('.schedule-source-card')).toHaveLength(13);
    expect(styles).toContain('.schedule-source-section {\n  justify-self: end;\n  width: 33.333%;');
    expect(styles).toContain('.schedule-source-section .section-title-row {\n  justify-content: flex-end;\n  margin-bottom: 6px;\n  text-align: right;');
    expect(styles).toContain('.schedule-source-grid {\n  display: grid;\n  grid-template-columns: repeat(3, minmax(0, 1fr));');
    expect(styles).toContain('.schedule-source-card {\n  display: grid;\n  align-content: center;\n  gap: 1px;\n  min-height: 28px;\n  padding: 4px 6px;');
  });

  it('keeps calendar date schedule strips legible with neutral text and a restrained accent', async () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toContain('.calendar-event-strip {\n  appearance: none;\n  display: grid;\n  grid-template-columns: 4px minmax(0, 1fr);');
    expect(styles).toContain('  cursor: pointer;\n  font-family: inherit;');
    expect(styles).toContain('  background: #ffffff;\n  color: #172033;');
    expect(styles).toContain('.calendar-event-strip::before {');
    expect(styles).toContain('.calendar-tone-legend {');
    expect(styles).toContain('.calendar-tone-key::before {');
    expect(styles).not.toContain('.calendar-event-strip {\n  color: var(--schedule-tone, #f97316);');
    expect(styles).not.toContain('background: linear-gradient(\n    180deg,\n    #ffffff 0%,\n    color-mix(in srgb, var(--schedule-tone, #f97316) 7%, #ffffff) 100%\n  );');
  });

  it('marks requested schedule cards with a restrained attention animation', async () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toContain('.calendar-event-card.requested {\n  animation: schedule-request-pulse 920ms ease-out;\n}');
    expect(styles).toContain('@keyframes schedule-request-pulse {');
  });

  it('keeps the official schedule calendar dark in dark mode', async () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toMatch(/\.app-shell\.dark-mode \.indicator-calendar-hero,[\s\S]*\.app-shell\.dark-mode \.calendar-month-card\s*\{[\s\S]*background: #171a21;/);
    expect(styles).toMatch(/\.app-shell\.dark-mode \.calendar-day\s*\{[\s\S]*background: #11141a;/);
    expect(styles).toMatch(/\.app-shell\.dark-mode \.calendar-event-strip,[\s\S]*\.app-shell\.dark-mode \.calendar-event-card,[\s\S]*\.app-shell\.dark-mode \.schedule-source-card\s*\{[\s\S]*background: #20242d;/);
    expect(styles).toMatch(/\.app-shell\.dark-mode \.calendar-event-card-body strong,[\s\S]*\.app-shell\.dark-mode \.schedule-source-card strong\s*\{[\s\S]*color: #f8fafc;/);
  });

  it('nudges month navigation glyphs into visual center inside their boxes', async () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toContain('.calendar-month-nav span {\n  display: block;\n  line-height: 1;\n  transform: translateY(-1px);\n}');
  });

  it('centers the month label against the adjacent navigation boxes', async () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toContain('.calendar-month-title-row h3 {\n  margin: 0;\n  line-height: 30px;\n}');
  });

  it('keeps the mobile calendar wide enough for readable schedule rows', async () => {
    const styles = readFileSync(resolve(testDir, '../styles.css'), 'utf8');

    expect(styles).toContain('  .calendar-month-card {\n    overflow-x: auto;');
    expect(styles).toContain('  .calendar-weekdays,\n  .calendar-grid {\n    min-width: 920px;');
    expect(styles).toContain('  .calendar-event-strip {\n    min-height: 24px;\n    padding: 3px 7px;\n    font-size: 10.5px;');
  });
});
