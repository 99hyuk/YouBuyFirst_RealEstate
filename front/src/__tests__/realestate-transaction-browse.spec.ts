import { describe, expect, it } from 'vitest';

import {
  aggregateTransactions,
  transactionCoordinate,
  fetchTransactions,
  filterTransactions,
  toTransactionMarkers
} from '../lib/realestate-transaction-browse';
import type { RealEstateMarketFact } from '../lib/realestate-market-facts';

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
