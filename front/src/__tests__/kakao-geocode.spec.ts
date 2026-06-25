import { describe, expect, it, vi } from 'vitest';

import {
  buildGeocodeQueriesForItem,
  geocodeTransactionItems
} from '../lib/kakao-geocode';
import type { TransactionItem } from '../lib/realestate-transaction-browse';

const daejeonYuseong = '\uB300\uC804 \uC720\uC131\uAD6C';
const jijokDong = '\uC9C0\uC871\uB3D9';
const officialBlockOne =
  '\uB300\uC804\uB178\uC7404\uC9C0\uAD6C\uD55C\uD654\uAFC8\uC5D0\uADF8\uB9B01\uBE14\uB85D';
const noEunAliasOne =
  '\uB178\uC740\uD55C\uD654\uAFC8\uC5D0\uADF8\uB9B01\uB2E8\uC9C0';
const spacedDistrictAliasOne =
  '\uB300\uC804 \uC720\uC131\uAD6C \uB178\uC740 \uD55C\uD654\uAFC8\uC5D0\uADF8\uB9B0 1\uB2E8\uC9C0';
const tooBroadAliasOne =
  '\uD55C\uD654\uAFC8\uC5D0\uADF8\uB9B01\uB2E8\uC9C0';

function makeNoeunItem(): TransactionItem {
  return {
    id: `apt|${officialBlockOne}|${jijokDong}|trade`,
    name: officialBlockOne,
    region: jijokDong,
    gu: daejeonYuseong,
    propertyType: 'apt',
    dealType: 'trade',
    priceLabel: '6.25\uc5b5',
    priceValue: 62500,
    dealCount: 5,
    areaLabel: '\uc804\uc6a9 84\u33a1',
    builtYear: 2014,
    asOf: '2026-05-26',
    dataStatus: 'ok',
    stale: false,
    lat: 36.3623,
    lng: 127.3562,
    tone: 'flat',
    coordSource: 'approx',
    pricePerAreaByMonth: {}
  };
}

describe('transaction geocode query fallback', () => {
  it('builds official-name and Noeun alias queries for block-style MOLIT names', () => {
    const queries = buildGeocodeQueriesForItem(makeNoeunItem());

    expect(queries).toContain(`${daejeonYuseong} ${jijokDong} ${officialBlockOne}`);
    expect(queries).toContain(officialBlockOne);
    expect(queries).toContain(noEunAliasOne);
    expect(queries).toContain(spacedDistrictAliasOne);
    expect(new Set(queries).size).toBe(queries.length);
  });

  it('uses an in-region alias result and ignores a far-away broad alias result', async () => {
    const fetcher = vi.fn(async (_input: string, init?: RequestInit) => {
      const payload = JSON.parse(String(init?.body)) as { queries: string[] };
      expect(payload.queries).toContain(noEunAliasOne);
      expect(payload.queries).toContain(tooBroadAliasOne);

      return new Response(JSON.stringify({
        results: [
          { query: tooBroadAliasOne, lat: 35.53674153014342, lng: 129.34849103341116 },
          { query: noEunAliasOne, lat: 36.3882647269268, lng: 127.300999416018 }
        ]
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }) as unknown as typeof fetch;

    const [item] = await geocodeTransactionItems([makeNoeunItem()], fetcher);

    expect(item.coordSource).toBe('geocoded');
    expect(item.lat).toBeCloseTo(36.3882647269268);
    expect(item.lng).toBeCloseTo(127.300999416018);
  });
});
