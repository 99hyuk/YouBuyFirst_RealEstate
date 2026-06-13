import { describe, expect, it, vi } from 'vitest';

import {
  buildMarketFactRows,
  buildMarketSummaryIndicators,
  fetchRealEstateMarketFacts,
  fetchRealEstateMarketSummary,
  marketFactStatusLabel
} from '../lib/realestate-market-facts';

describe('real-estate market fact adapter', () => {
  it('builds dashboard status rows from backend market facts', () => {
    const rows = buildMarketFactRows([
      {
        factType: 'apt_trade',
        provider: 'molit',
        providerDataset: 'molit_apt_trade',
        legalDongCode: '11110',
        observedAt: '2026-06-03',
        asOf: '2026-06-01',
        valueJson: {
          apartmentName: 'Sajik Palace',
          dealAmountManwon: 82500
        },
        dataStatus: 'ok',
        stale: false
      },
      {
        factType: 'apt_rent',
        provider: 'molit',
        providerDataset: 'molit_apt_rent',
        legalDongCode: '11110',
        observedAt: '2026-06-05',
        asOf: '2026-06-01',
        valueJson: {
          apartmentName: 'Sajik Palace',
          depositAmountManwon: 45000,
          monthlyRentAmountManwon: 120
        },
        dataStatus: 'stale',
        stale: true
      }
    ]);

    expect(rows).toEqual([
      {
        id: 'molit_apt_trade:11110:apt_trade:2026-06-03',
        name: '매매 실거래',
        value: '8.25억원',
        meta: 'Sajik Palace · 계약 2026-06-03 · 기준 2026-06-01',
        providerLabel: '국토교통부',
        statusLabel: '공공데이터 반영',
        stale: false
      },
      {
        id: 'molit_apt_rent:11110:apt_rent:2026-06-05',
        name: '전월세 실거래',
        value: '보증금 4.50억원 / 월세 120만원',
        meta: 'Sajik Palace · 계약 2026-06-05 · 기준 2026-06-01',
        providerLabel: '국토교통부',
        statusLabel: '지연 가능',
        stale: true
      }
    ]);
  });

  it('keeps empty and fixture states explicit', () => {
    expect(buildMarketFactRows([])).toEqual([
      {
        id: 'empty-market-facts',
        name: '실거래·전월세',
        value: '수집 대기',
        meta: '공공데이터 registry 연결 후 표시',
        providerLabel: '국토교통부',
        statusLabel: '데이터 없음',
        stale: true
      }
    ]);

    expect(marketFactStatusLabel({ dataStatus: 'mock', stale: false })).toBe('mock');
    expect(marketFactStatusLabel({ dataStatus: 'error', stale: false })).toBe('확인 필요');
  });

  it('fetches market facts with the target query parameters', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ items: [] })));

    await fetchRealEstateMarketFacts(
      { legalDongCode: '11110', factType: 'apt_trade' },
      fetcher
    );

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/market-facts?legalDongCode=11110&factType=apt_trade');
  });

  it('builds dashboard indicator cards from backend market summary', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      items: [
        {
          label: '매매 실거래',
          value: '8.25억원',
          changePct: null,
          updatedLabel: '국토교통부 · 계약 2026-06-09 · 기준 2026-06-01',
          trend: 'up',
          dataStatus: 'ok',
          stale: false,
          provider: 'molit',
          factType: 'apt_trade',
          legalDongCode: '11680'
        }
      ],
      freshness: {
        staleCount: 0,
        sourceCount: 1,
        latestAsOf: '2026-06-01',
        dataStatus: 'ok'
      }
    })));

    const summary = await fetchRealEstateMarketSummary({ legalDongCode: '11680' }, fetcher);
    const indicators = buildMarketSummaryIndicators(summary, [
      {
        label: '미분양',
        value: '5.7만호',
        changePct: -3.2,
        updatedLabel: 'mock',
        trend: 'down'
      }
    ]);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/dashboard/market-summary?legalDongCode=11680');
    expect(indicators).toEqual([
      {
        label: '매매 실거래',
        value: '8.25억원',
        changePct: null,
        updatedLabel: '국토교통부 · 계약 2026-06-09 · 기준 2026-06-01',
        trend: 'up'
      },
      {
        label: '미분양',
        value: '5.7만호',
        changePct: -3.2,
        updatedLabel: 'mock',
        trend: 'down'
      }
    ]);
  });
});
