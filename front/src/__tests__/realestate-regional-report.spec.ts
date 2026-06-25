import { describe, expect, it, vi } from 'vitest';

import { fetchRealEstateRegionalReport } from '../lib/realestate-regional-reports';

describe('real-estate regional report API adapter', () => {
  it('fetches the latest DB-backed regional report for a target', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      reportId: 'regional-report-region-seoul-mapo-latest',
      targetId: 'region-seoul-mapo',
      targetName: '서울 마포구',
      regionLevel: 'sigungu',
      regionCode: '11440',
      reportVersion: 'regional-report-seed-v1',
      promptVersion: 'regional-report-template-v1',
      modelName: null,
      generatedBy: 'seed:regional-report-v1',
      title: '서울 마포구 최신 지역 리포트',
      headline: '공식 지표와 최근 이슈를 함께 봐야 하는 관찰 지역입니다.',
      summary: '최신 기준 브리핑입니다.',
      body: '지도 기간별 등락은 보조 수치로만 사용합니다.',
      expectationPoints: ['공식 가격지표와 지도 계층이 연결됩니다.'],
      concernPoints: ['승인되지 않은 뉴스 후보를 결론처럼 쓰지 않습니다.'],
      dataQuality: 'partial',
      confidence: 0.45,
      asOf: '2026-06-24T00:00:00Z',
      publishedAt: '2026-06-24T00:00:00Z',
      sources: [
        {
          reportSourceId: 'regional-report-source-region-seoul-mapo-molit-rt',
          displayOrder: 1,
          refType: 'external',
          refId: 'molit-real-transaction-disclosure',
          label: '실거래 근거',
          title: '국토교통부 실거래가 공개시스템',
          url: 'https://rt.molit.go.kr/',
          sourceName: '국토교통부',
          publishedAt: null,
          dataStatus: 'ok'
        }
      ]
    }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200
    }));

    const report = await fetchRealEstateRegionalReport('region-seoul-mapo', fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/regional-report');
    expect(report?.targetId).toBe('region-seoul-mapo');
    expect(report?.regionLevel).toBe('sigungu');
    expect(report?.expectationPoints).toEqual(['공식 가격지표와 지도 계층이 연결됩니다.']);
    expect(report?.concernPoints).toEqual(['승인되지 않은 뉴스 후보를 결론처럼 쓰지 않습니다.']);
    expect(report?.sources[0].title).toBe('국토교통부 실거래가 공개시스템');
  });

  it('returns null when a target does not have a stored report yet', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ message: 'not found' }), { status: 404 }));

    await expect(fetchRealEstateRegionalReport('region-unknown', fetcher)).resolves.toBeNull();
  });
});
