import { describe, expect, it } from 'vitest';

import {
  aggregateComplexes,
  complexCoordinate,
  filterComplexes,
  toComplexMarkers
} from '../lib/realestate-complex-browse';
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
    const items = aggregateComplexes(facts);
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
    const rent = aggregateComplexes(facts).find((item) => item.dealType === 'rent');
    expect(rent).toBeDefined();
    expect(rent!.priceLabel).toContain('보증');
    expect(rent!.priceLabel).toContain('월');
  });

  it('skips facts without an apartment name or a known deal type', () => {
    const items = aggregateComplexes([
      { factType: 'apt_trade', valueJson: { dealAmountManwon: 1000 } },
      { factType: 'unknown', valueJson: { apartmentName: 'X' } }
    ]);
    expect(items).toHaveLength(0);
  });
});

describe('complex browse filter + markers', () => {
  it('filters by deal type and query, and sorts by price', () => {
    const items = aggregateComplexes(facts);
    const onlyTrade = filterComplexes(items, { dealType: 'trade' });
    expect(onlyTrade.every((item) => item.dealType === 'trade')).toBe(true);

    const byQuery = filterComplexes(items, { query: '공덕' });
    expect(byQuery).toHaveLength(1);
    expect(byQuery[0].name).toBe('공덕더프라임');

    const sorted = filterComplexes(items, {}, 'price-desc');
    expect(sorted[0].priceValue).toBeGreaterThanOrEqual(sorted[sorted.length - 1].priceValue);
  });

  it('converts cards into map markers with required fields', () => {
    const markers = toComplexMarkers(aggregateComplexes(facts));
    expect(markers.length).toBeGreaterThan(0);
    for (const marker of markers) {
      expect(Number.isFinite(marker.lat)).toBe(true);
      expect(Number.isFinite(marker.lng)).toBe(true);
      expect(marker.price).toBeTruthy();
      expect(marker.provider).toBe('molit');
    }
  });

  it('places complexes deterministically near their gu centroid', () => {
    const a = complexCoordinate('11680', 'key-1');
    const b = complexCoordinate('11680', 'key-1');
    const c = complexCoordinate('11680', 'key-2');
    expect(a).toEqual(b); // deterministic
    expect(a).not.toEqual(c); // different keys spread out
    // within ~2km of 강남구 centroid
    expect(Math.abs(a.lat - 37.5172)).toBeLessThan(0.02);
    expect(Math.abs(a.lng - 127.0473)).toBeLessThan(0.02);
  });
});
