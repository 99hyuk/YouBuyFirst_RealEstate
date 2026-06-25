import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  aggregateTransactions,
  computeTransactionChange,
  transactionCoordinate,
  regionCentroid,
  fetchTransactions,
  filterTransactions,
  toTransactionMarkers
} from '../lib/realestate-transaction-browse';
import type { RealEstateMarketFact } from '../lib/realestate-market-facts';
import transactionRegions from '../fixtures/transaction-regions.json';
import { currentAuthUser } from '../lib/auth-session';
import TransactionMapPage from '../pages/TransactionMapPage.vue';

const routerMock = vi.hoisted(() => ({
  route: { query: {} as Record<string, unknown> },
  router: {
    push: vi.fn(),
    replace: vi.fn()
  }
}));

vi.mock('vue-router', () => ({
  useRoute: () => routerMock.route,
  useRouter: () => routerMock.router
}));

afterEach(() => {
  vi.unstubAllGlobals();
  currentAuthUser.value = null;
  routerMock.route.query = {};
  routerMock.router.push.mockClear();
  routerMock.router.replace.mockClear();
});

type TransactionRegionGroup = {
  sido: string;
  items: Array<{ code: string; name: string }>;
};

const facts: RealEstateMarketFact[] = [
  {
    factType: 'apt_trade',
    provider: 'molit',
    legalDongCode: '11680',
    observedAt: '2026-05-10',
    asOf: '2026-05-01',
    valueJson: { apartmentName: '청담자이', legalDongName: '청담동', dealAmountManwon: 220000, exclusiveAreaM2: 49.6, builtYear: 2011 },
    dataStatus: 'ok',
    stale: false
  },
  {
    factType: 'apt_trade',
    provider: 'molit',
    legalDongCode: '11680',
    observedAt: '2026-05-26',
    asOf: '2026-05-01',
    valueJson: { apartmentName: '청담자이', legalDongName: '청담동', dealAmountManwon: 228100, exclusiveAreaM2: 84.9, builtYear: 2011 },
    dataStatus: 'ok',
    stale: false
  },
  {
    factType: 'apt_rent',
    provider: 'molit',
    legalDongCode: '11440',
    observedAt: '2026-05-15',
    asOf: '2026-05-01',
    valueJson: { apartmentName: '공덕더프라임', legalDongName: '공덕동', depositAmountManwon: 60000, monthlyRentAmountManwon: 80, exclusiveAreaM2: 59.9, builtYear: 2013 },
    dataStatus: 'ok',
    stale: false
  }
];

describe('complex browse aggregation', () => {
  it('groups facts into one card per complex + deal type and keeps the most recent price', () => {
    const items = aggregateTransactions(facts);
    expect(items).toHaveLength(2);

    const cheongdam = items.find((item) => item.name === '청담자이');
    expect(cheongdam).toBeDefined();
    expect(cheongdam!.dealType).toBe('trade');
    expect(cheongdam!.dealCount).toBe(2);
    // most recent observation (2026-05-26 → 228100 만원) wins for the representative price
    expect(cheongdam!.priceValue).toBe(228100);
    expect(cheongdam!.asOf).toBe('2026-05-26');
    expect(cheongdam!.areaLabel).toContain('~');
    expect(cheongdam!.gu).toBe('강남구');
  });

  it('labels rent deposit + monthly rent', () => {
    const rent = aggregateTransactions(facts).find((item) => item.dealType === 'rent');
    expect(rent).toBeDefined();
    expect(rent!.priceLabel).toContain('보증');
    expect(rent!.priceLabel).toContain('월');
  });

  it('skips facts without an apartment name or a known deal type', () => {
    const items = aggregateTransactions([
      { factType: 'apt_trade', valueJson: { dealAmountManwon: 1000 } },
      { factType: 'unknown', valueJson: { apartmentName: 'X' } }
    ]);
    expect(items).toHaveLength(0);
  });
});

describe('complex browse filter + markers', () => {
  it('filters by deal type and query, and sorts by price', () => {
    const items = aggregateTransactions(facts);
    const onlyTrade = filterTransactions(items, { dealType: 'trade' });
    expect(onlyTrade.every((item) => item.dealType === 'trade')).toBe(true);

    const byQuery = filterTransactions(items, { query: '공덕' });
    expect(byQuery).toHaveLength(1);
    expect(byQuery[0].name).toBe('공덕더프라임');

    const sorted = filterTransactions(items, {}, 'price-desc');
    expect(sorted[0].priceValue).toBeGreaterThanOrEqual(sorted[sorted.length - 1].priceValue);
  });

  it('matches Noeun block aliases without pulling in Gwanpyeong Hanwha complexes', () => {
    const officialNoeun =
      '\uB300\uC804\uB178\uC7404\uC9C0\uAD6C\uD55C\uD654\uAFC8\uC5D0\uADF8\uB9B01\uBE14\uB85D';
    const gwanpyeong =
      '\uD55C\uD654\uAFC8\uC5D0\uADF8\uB9B01\uCC28';
    const jijokDong = '\uC9C0\uC871\uB3D9';
    const gwanpyeongDong = '\uAD00\uD3C9\uB3D9';
    const items = aggregateTransactions([
      {
        factType: 'apt_trade',
        provider: 'molit',
        legalDongCode: '30200',
        observedAt: '2026-05-26',
        valueJson: {
          apartmentName: officialNoeun,
          legalDongName: jijokDong,
          dealAmountManwon: 62500,
          exclusiveAreaM2: 84,
          builtYear: 2014
        }
      },
      {
        factType: 'apt_trade',
        provider: 'molit',
        legalDongCode: '30200',
        observedAt: '2026-05-29',
        valueJson: {
          apartmentName: gwanpyeong,
          legalDongName: gwanpyeongDong,
          dealAmountManwon: 47000,
          exclusiveAreaM2: 84,
          builtYear: 2006
        }
      }
    ]);

    const byNoeunAlias = filterTransactions(items, {
      query: '\uB178\uC740\uD55C\uD654\uAFC8\uC5D0\uADF8\uB9B0'
    });

    expect(byNoeunAlias).toHaveLength(1);
    expect(byNoeunAlias[0].name).toBe(officialNoeun);
    expect(byNoeunAlias[0].region).toBe(jijokDong);
  });

  it('converts cards into map markers with required fields', () => {
    const markers = toTransactionMarkers(aggregateTransactions(facts));
    expect(markers.length).toBeGreaterThan(0);
    for (const marker of markers) {
      expect(Number.isFinite(marker.lat)).toBe(true);
      expect(Number.isFinite(marker.lng)).toBe(true);
      expect(marker.price).toBeTruthy();
      expect(marker.provider).toBe('molit');
    }
  });

  it('places complexes deterministically near their gu centroid', () => {
    const a = transactionCoordinate('11680', 'key-1');
    const b = transactionCoordinate('11680', 'key-1');
    const c = transactionCoordinate('11680', 'key-2');
    expect(a).toEqual(b); // deterministic
    expect(a).not.toEqual(c); // different keys spread out
    // within ~2km of 강남구 centroid
    expect(Math.abs(a.lat - 37.5172)).toBeLessThan(0.02);
    expect(Math.abs(a.lng - 127.0473)).toBeLessThan(0.02);
  });
});

describe('transaction region select coverage', () => {
  it('includes the regional-analysis legal-dong coverage instead of only hand-picked districts', () => {
    const codes = (transactionRegions.groups as Array<{ items: Array<{ code: string }> }>)
      .flatMap((group) => group.items.map((item) => item.code));

    expect(new Set(codes).size).toBeGreaterThanOrEqual(250);
    expect(codes).toEqual(expect.arrayContaining([
      '11110',
      '26110',
      '30200',
      '41110',
      '50110'
    ]));
  });

  it('has a map center seed for newly exposed transaction regions', () => {
    expect(regionCentroid('26110')).not.toBeNull();
    expect(regionCentroid('30200')).not.toBeNull();
    expect(regionCentroid('50110')).not.toBeNull();
  });
});

describe('transaction page region picker', () => {
  it('starts on apartment all deals and places MoM before longer trend periods', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ items: [] }), { status: 200 })),
    );

    const wrapper = mount(TransactionMapPage, {
      global: {
        stubs: {
          RealEstateTransactionMap: {
            props: ['selectedTargetId', 'center'],
            template: '<div data-testid="map-stub" :data-selected-target-id="selectedTargetId" :data-center-lat="center?.lat" :data-center-lng="center?.lng" />',
          },
        },
      },
    });

    await flushPromises();

    const propertyGroup = wrapper.get('[aria-label="매물 유형"]');
    const apartmentButton = propertyGroup.findAll('button').find((button) => button.text() === '아파트');
    const dealButtons = wrapper.get('[aria-label="거래 방식"]').findAll('button');
    const allDealButton = dealButtons.find((button) => button.text() === '전체');
    const trendButtons = wrapper.get('[aria-label="가격 비교 기간"]').findAll('button');
    const momButton = trendButtons.find((button) => button.text() === 'MoM');
    const sortSelect = wrapper.get('select.complex-sort').element;

    expect(apartmentButton?.classes()).toContain('active');
    expect(allDealButton?.classes()).toContain('active');
    expect(trendButtons.map((button) => button.text())).toEqual(['MoM', '6개월', 'YoY']);
    expect(momButton?.attributes('aria-checked')).toBe('true');
    expect(momButton?.classes()).toContain('active');
    expect(
      Boolean(sortSelect.compareDocumentPosition(propertyGroup.element) & Node.DOCUMENT_POSITION_FOLLOWING),
    ).toBe(true);

    wrapper.unmount();
  });

  it('splits region selection into linked sido and sigungu selects', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ items: [] }), { status: 200 })),
    );

    const wrapper = mount(TransactionMapPage, {
      global: {
        stubs: {
          RealEstateTransactionMap: {
            props: ['selectedTargetId', 'center'],
            template: '<div data-testid="map-stub" :data-selected-target-id="selectedTargetId" :data-center-lat="center?.lat" :data-center-lng="center?.lng" />',
          },
        },
      },
    });

    await flushPromises();

    const sidoSelect = wrapper.get('[data-testid="complex-sido-select"]')
      .element as HTMLSelectElement;
    const regionSelect = wrapper.get('[data-testid="complex-region-select"]')
      .element as HTMLSelectElement;
    const sidoCodes = Array.from(sidoSelect.options).map((option) => option.value);

    expect(sidoSelect.value).toBe('11');
    expect(sidoCodes).toEqual(expect.arrayContaining(['11', '30']));
    expect(Array.from(regionSelect.options).map((option) => option.value)).toContain('11680');

    await wrapper.get('[data-testid="complex-sido-select"]').setValue('30');

    const daejeonCodes = (transactionRegions.groups as TransactionRegionGroup[])
      .find((group) => group.items.some((item) => item.code.startsWith('30')))
      ?.items.map((item) => item.code);

    expect((wrapper.get('[data-testid="complex-sido-select"]').element as HTMLSelectElement).value).toBe(
      '30',
    );
    expect(
      Array.from(
        (wrapper.get('[data-testid="complex-region-select"]').element as HTMLSelectElement).options,
      ).map((option) => option.value),
    ).toEqual(daejeonCodes);
    expect((wrapper.get('[data-testid="complex-region-select"]').element as HTMLSelectElement).value).toBe(
      daejeonCodes?.[0],
    );

    wrapper.unmount();
  });
});

describe('transaction detail panel', () => {
  it('seeds detail trend from the page trend once, then keeps the controls independent', async () => {
    const makeFact = (dealYm: string, dealAmountManwon: number): RealEstateMarketFact => ({
      factType: 'apt_trade',
      provider: 'molit',
      legalDongCode: '11680',
      observedAt: `${dealYm.slice(0, 4)}-${dealYm.slice(4, 6)}-10`,
      asOf: `${dealYm.slice(0, 4)}-${dealYm.slice(4, 6)}-01`,
      valueJson: {
        apartmentName: '기간분리단지',
        legalDongName: '역삼동',
        dealAmountManwon,
        exclusiveAreaM2: 50,
        builtYear: 2018
      },
      dataStatus: 'ok',
      stale: false
    });

    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('/api/realestate/market-facts')) {
          const params = new URL(url, 'http://local.test').searchParams;
          const dealYm = params.get('dealYm');
          const factType = params.get('factType');
          const prices: Record<string, number> = {
            '202606': 120000,
            '202605': 100000,
            '202512': 150000,
            '202506': 110000
          };

          return new Response(JSON.stringify({
            items: factType === 'apt_trade' && dealYm && prices[dealYm]
              ? [makeFact(dealYm, prices[dealYm])]
              : []
          }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

        return new Response(JSON.stringify({ items: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }),
    );

    const wrapper = mount(TransactionMapPage, {
      global: {
        stubs: {
          RealEstateTransactionMap: {
            template: '<div data-testid="map-stub" />',
          },
        },
      },
    });

    await flushPromises();

    const pageTrendButtons = () => wrapper.get('[aria-label="가격 비교 기간"]').findAll('button');
    await pageTrendButtons().find((button) => button.text() === '6개월')!.trigger('click');
    await wrapper.get('[data-testid="pending-toggle"]').trigger('click');
    await wrapper.get('[data-testid="complex-card-apt|기간분리단지|역삼동|trade"]').trigger('click');
    await flushPromises();

    const detailTrendButtons = () => wrapper.get('[aria-label="상세 비교 기간"]').findAll('button');
    expect(detailTrendButtons().find((button) => button.text() === '6개월')?.attributes('aria-checked')).toBe('true');
    expect(pageTrendButtons().find((button) => button.text() === '6개월')?.attributes('aria-checked')).toBe('true');

    await detailTrendButtons().find((button) => button.text() === 'YoY')!.trigger('click');

    expect(detailTrendButtons().find((button) => button.text() === 'YoY')?.attributes('aria-checked')).toBe('true');
    expect(pageTrendButtons().find((button) => button.text() === '6개월')?.attributes('aria-checked')).toBe('true');
    expect(pageTrendButtons().find((button) => button.text() === 'YoY')?.attributes('aria-checked')).toBe('false');

    wrapper.unmount();
  });

  it('keeps nearby facilities but removes related reaction, content, and timeline sections', async () => {
    const urls: string[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        urls.push(url);
        if (url.includes('/api/realestate/market-facts')) {
          return new Response(JSON.stringify({
            items: [{
              factType: 'apt_trade',
              provider: 'molit',
              legalDongCode: '11680',
              observedAt: '2026-06-10',
              asOf: '2026-06-01',
              valueJson: {
                apartmentName: '상세테스트단지',
                legalDongName: '청담동',
                dealAmountManwon: 130000,
                exclusiveAreaM2: 84,
                builtYear: 2010
              },
              dataStatus: 'ok',
              stale: false
            }]
          }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

        return new Response(JSON.stringify({ items: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }),
    );

    const wrapper = mount(TransactionMapPage, {
      global: {
        stubs: {
          RealEstateTransactionMap: {
            template: '<div data-testid="map-stub" />',
          },
        },
      },
    });

    await flushPromises();

    await wrapper.get('[data-testid="pending-toggle"]').trigger('click');
    await wrapper.get('[data-testid="complex-card-apt|상세테스트단지|청담동|trade"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="transaction-detail"]').text()).toContain('상세테스트단지');
    expect(wrapper.find('[data-testid="transaction-nearby"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="transaction-reaction"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="transaction-content"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="transaction-timeline"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('커뮤니티 반응');
    expect(wrapper.text()).not.toContain('관련 뉴스/콘텐츠');
    expect(wrapper.text()).not.toContain('정책 타임라인');
    expect(urls.some((url) => url.includes('/api/realestate/targets/search'))).toBe(false);

    wrapper.unmount();
  });

  it('opens the first q-matched transaction when arriving from dashboard search', async () => {
    routerMock.route.query = { region: '11680', q: 'SearchMatchTower' };
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('/api/realestate/market-facts')) {
          return new Response(JSON.stringify({
            items: [{
              factType: 'apt_trade',
              provider: 'molit',
              legalDongCode: '11680',
              observedAt: '2026-06-10',
              asOf: '2026-06-01',
              valueJson: {
                apartmentName: 'SearchMatchTower',
                legalDongName: 'Yeoksam',
                dealAmountManwon: 130000,
                exclusiveAreaM2: 84,
                builtYear: 2010
              },
              dataStatus: 'ok',
              stale: false
            }]
          }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

        return new Response(JSON.stringify({ items: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }),
    );

    const wrapper = mount(TransactionMapPage, {
      global: {
        stubs: {
          RealEstateTransactionMap: {
            props: ['selectedTargetId', 'center'],
            template: '<div data-testid="map-stub" :data-selected-target-id="selectedTargetId" :data-center-lat="center?.lat" :data-center-lng="center?.lng" />',
          },
        },
      },
    });

    await flushPromises();
    await wrapper.vm.$nextTick();

    const searchInput = wrapper.get('.complex-search input').element as HTMLInputElement;
    const expectedCenter = transactionCoordinate('11680', 'apt|SearchMatchTower|Yeoksam|trade');
    const mapStub = wrapper.get('[data-testid="map-stub"]');
    expect(searchInput.value).toBe('SearchMatchTower');
    expect(wrapper.get('[data-testid="transaction-detail"]').text()).toContain('SearchMatchTower');
    expect(mapStub.attributes('data-selected-target-id')).toBe('apt|SearchMatchTower|Yeoksam|trade');
    expect(Number(mapStub.attributes('data-center-lat'))).toBeCloseTo(expectedCenter.lat, 5);
    expect(Number(mapStub.attributes('data-center-lng'))).toBeCloseTo(expectedCenter.lng, 5);

    wrapper.unmount();
  });

  it('saves and unsaves the selected transaction from the detail heart button', async () => {
    const urls: string[] = [];
    currentAuthUser.value = {
      id: 'user-watch',
      username: 'watchuser',
      email: 'watch@example.com',
      displayName: '관심유저',
      authProvider: 'local',
      createdAt: '2026-06-25T00:00:00Z',
      lastSeenAt: '2026-06-25T00:00:00Z'
    };

    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        urls.push(url);

        if (url === '/api/realestate/watch-targets' && (init?.method ?? 'GET') === 'GET') {
          return new Response(JSON.stringify({ items: [] }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
          });
        }

        if (url === '/api/realestate/watch-targets' && init?.method === 'POST') {
          return new Response(JSON.stringify({
            watchId: 'watch-complex-interest-test',
            targetType: 'complex',
            targetId: 'apt|관심테스트단지|청담동|trade',
            displayName: '관심테스트단지',
            landingPath: '/realestate/transactions?region=11680&selected=apt%7C%EA%B4%80%EC%8B%AC%ED%85%8C%EC%8A%A4%ED%8A%B8%EB%8B%A8%EC%A7%80%7C%EC%B2%AD%EB%8B%B4%EB%8F%99%7Ctrade',
            createdAt: '2026-06-25T00:00:00Z',
            updatedAt: '2026-06-25T00:00:00Z'
          }), {
            status: 201,
            headers: { 'Content-Type': 'application/json' }
          });
        }

        if (url.startsWith('/api/realestate/watch-targets?') && init?.method === 'DELETE') {
          return new Response(null, { status: 204 });
        }

        if (url.includes('/api/realestate/market-facts')) {
          return new Response(JSON.stringify({
            items: [{
              factType: 'apt_trade',
              provider: 'molit',
              legalDongCode: '11680',
              observedAt: '2026-06-10',
              asOf: '2026-06-01',
              valueJson: {
                apartmentName: '관심테스트단지',
                legalDongName: '청담동',
                dealAmountManwon: 150000,
                exclusiveAreaM2: 84,
                builtYear: 2014
              },
              dataStatus: 'ok',
              stale: false
            }]
          }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

        return new Response(JSON.stringify({ items: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }),
    );

    const wrapper = mount(TransactionMapPage, {
      global: {
        stubs: {
          RealEstateTransactionMap: {
            template: '<div data-testid="map-stub" />',
          },
        },
      },
    });

    await flushPromises();

    await wrapper.get('[data-testid="pending-toggle"]').trigger('click');
    await wrapper.get('[data-testid="complex-card-apt|관심테스트단지|청담동|trade"]').trigger('click');
    await flushPromises();

    const heart = wrapper.get('[data-testid="transaction-watch-toggle"]');
    expect(heart.attributes('aria-pressed')).toBe('false');

    await heart.trigger('click');
    await flushPromises();

    const saveCall = vi.mocked(globalThis.fetch).mock.calls.find(
      ([input, init]) => input === '/api/realestate/watch-targets' && init?.method === 'POST'
    );
    expect(saveCall).toBeTruthy();
    expect(JSON.parse(String(saveCall?.[1]?.body))).toEqual({
      targetType: 'complex',
      targetId: 'apt|관심테스트단지|청담동|trade',
      displayName: '관심테스트단지',
      landingPath: '/realestate/transactions?region=11680&selected=apt%7C%EA%B4%80%EC%8B%AC%ED%85%8C%EC%8A%A4%ED%8A%B8%EB%8B%A8%EC%A7%80%7C%EC%B2%AD%EB%8B%B4%EB%8F%99%7Ctrade'
    });
    expect(wrapper.get('[data-testid="transaction-watch-toggle"]').attributes('aria-pressed')).toBe('true');

    await wrapper.get('[data-testid="transaction-watch-toggle"]').trigger('click');
    await flushPromises();

    expect(urls).toContain('/api/realestate/watch-targets?targetType=complex&targetId=apt%7C%EA%B4%80%EC%8B%AC%ED%85%8C%EC%8A%A4%ED%8A%B8%EB%8B%A8%EC%A7%80%7C%EC%B2%AD%EB%8B%B4%EB%8F%99%7Ctrade');
    expect(wrapper.get('[data-testid="transaction-watch-toggle"]').attributes('aria-pressed')).toBe('false');

    wrapper.unmount();
  });
});

describe('complex browse property type', () => {
  const mixedFacts: RealEstateMarketFact[] = [
    ...facts,
    {
      factType: 'offi_trade',
      provider: 'molit',
      legalDongCode: '11680',
      observedAt: '2026-05-28',
      asOf: '2026-05-01',
      valueJson: { apartmentName: '사이룩스', legalDongName: '수서동', dealAmountManwon: 28000, exclusiveAreaM2: 40.88, builtYear: 2003 },
      dataStatus: 'ok',
      stale: false
    }
  ];

  it('classifies offi_trade as officetel and apt facts as apartment', () => {
    const items = aggregateTransactions(mixedFacts);
    const offi = items.find((item) => item.name === '사이룩스');
    expect(offi).toBeDefined();
    expect(offi!.propertyType).toBe('offi');
    expect(offi!.dealType).toBe('trade');
    expect(items.filter((item) => item.propertyType === 'apt').length).toBeGreaterThan(0);
  });

  it('filters by property type', () => {
    const items = aggregateTransactions(mixedFacts);
    const offiOnly = filterTransactions(items, { propertyType: 'offi' });
    expect(offiOnly.every((item) => item.propertyType === 'offi')).toBe(true);
    expect(offiOnly.map((item) => item.name)).toContain('사이룩스');

    const aptOnly = filterTransactions(items, { propertyType: 'apt' });
    expect(aptOnly.every((item) => item.propertyType === 'apt')).toBe(true);
    expect(aptOnly.map((item) => item.name)).not.toContain('사이룩스');
  });

  it('fetches the selected region and category factTypes', async () => {
    const urls: string[] = [];
    const fetcher = (async (input: string) => {
      urls.push(input);
      return new Response(JSON.stringify({ items: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }) as unknown as typeof fetch;

    await fetchTransactions('rh', '26350', fetcher);
    expect(urls.some((u) => u.includes('factType=rh_trade') && u.includes('legalDongCode=26350'))).toBe(true);
  });

  it('requests the latest June 2026 transaction month and matching comparison months', async () => {
    const urls: string[] = [];
    const fetcher = (async (input: string) => {
      urls.push(input);
      return new Response(JSON.stringify({
        items: [{
          factType: 'apt_trade',
          provider: 'molit',
          legalDongCode: '11680',
          observedAt: '2026-06-10',
          valueJson: {
            apartmentName: '기준월단지',
            legalDongName: '역삼동',
            dealAmountManwon: 100000,
            exclusiveAreaM2: 50,
            builtYear: 2018
          },
          dataStatus: 'ok',
          stale: false
        }]
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }) as unknown as typeof fetch;

    await fetchTransactions('apt', '11680', fetcher);

    const dealYms = urls
      .map((url) => new URL(url, 'http://local.test').searchParams.get('dealYm'))
      .filter((dealYm): dealYm is string => Boolean(dealYm));

    expect(new Set(dealYms)).toEqual(new Set(['202606', '202605', '202512', '202506']));
  });

  it('classifies rh_trade as 연립·다세대 and silv_trade as 분양권', () => {
    const items = aggregateTransactions([
      {
        factType: 'rh_trade',
        provider: 'molit',
        legalDongCode: '11680',
        observedAt: '2026-05-28',
        valueJson: { apartmentName: '에이트', legalDongName: '역삼동', dealAmountManwon: 49301, exclusiveAreaM2: 28.49, builtYear: 2022 }
      },
      {
        factType: 'silv_trade',
        provider: 'molit',
        legalDongCode: '11680',
        observedAt: '2026-05-29',
        valueJson: { apartmentName: '디에이치 퍼스티어 아이파크', legalDongName: '개포동', dealAmountManwon: 343000, exclusiveAreaM2: 84.99, builtYear: 2024 }
      }
    ]);
    const rh = items.find((item) => item.name === '에이트');
    const silv = items.find((item) => item.name === '디에이치 퍼스티어 아이파크');
    expect(rh?.propertyType).toBe('rh');
    expect(silv?.propertyType).toBe('silv');
  });

  it('labels nameless 단독·다가구 by 지번 address, falling back to 동+유형', () => {
    const items = aggregateTransactions([
      {
        factType: 'sh_trade',
        provider: 'molit',
        legalDongCode: '11680',
        observedAt: '2026-05-20',
        valueJson: { legalDongName: '역삼동', jibun: '736-12', dealAmountManwon: 250000, builtYear: 2001 }
      },
      {
        factType: 'sh_rent',
        provider: 'molit',
        legalDongCode: '11680',
        observedAt: '2026-05-21',
        valueJson: { legalDongName: '역삼동', depositAmountManwon: 1000, monthlyRentAmountManwon: 66, houseType: '다가구', builtYear: 1998 }
      }
    ]);
    const byJibun = items.find((item) => item.name === '역삼동 736-12');
    const byHouseType = items.find((item) => item.name === '역삼동 다가구');
    expect(byJibun?.propertyType).toBe('sh');
    expect(byJibun?.dealType).toBe('trade');
    expect(byHouseType?.propertyType).toBe('sh');
    expect(byHouseType?.dealType).toBe('rent');
  });
});

describe('transaction trend (period change)', () => {
  const make = (ym: string, dealAmountManwon: number) => ({
    factType: 'apt_trade',
    provider: 'molit',
    legalDongCode: '11680',
    observedAt: `${ym}-10`,
    valueJson: { apartmentName: '트렌드단지', legalDongName: '역삼동', dealAmountManwon, exclusiveAreaM2: 50, builtYear: 2018 }
  });

  it('keeps per-month 평단가 and returns null when only one month exists', () => {
    const item = aggregateTransactions([make('2026-05', 100000)])[0];
    expect(item.pricePerAreaByMonth['2026-05']).toBeCloseTo(2000);
    expect(computeTransactionChange(item, 'yoy')).toBeNull();
  });

  it('computes YoY change from per-month 평단가, null for missing comparison month', () => {
    const item = aggregateTransactions([make('2025-05', 100000), make('2026-05', 110000)]).find((i) => i.name === '트렌드단지')!;
    expect(computeTransactionChange(item, 'yoy')).toBeCloseTo(10); // 2200 vs 2000 → +10%
    expect(computeTransactionChange(item, 'mom')).toBeNull(); // no 2026-04
  });
});
