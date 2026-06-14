import { describe, expect, it, vi } from 'vitest';

import { fetchRealEstateTargetEvidenceLogs } from '../lib/realestate-evidence-logs';

describe('real-estate evidence log API client', () => {
  it('lists target evidence logs with the requested limit', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      items: [
        {
          evidenceLogId: 'evidence-region-seoul-mapo-20260614',
          targetId: 'region-seoul-mapo',
          evaluationVersion: 'realestate-eval-v1',
          promptVersion: 'realestate-eval-prompt-v1',
          modelName: 'gpt-5-mini',
          tone: 'watch',
          summary: '전세 우려와 학군 기대가 함께 관찰됩니다.',
          subtitle: '반응 지표와 market fact를 함께 본 평가',
          caveats: ['market_fact_partial'],
          dataQuality: 'partial',
          confidence: 0.72,
          skipReason: null,
          evaluatedAt: '2026-06-14T09:20:00Z',
          asOf: '2026-06-14T09:15:00Z',
          evidenceItems: []
        }
      ]
    })));

    const logs = await fetchRealEstateTargetEvidenceLogs('region-seoul-mapo', { limit: 3 }, fetcher);

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/evidence-logs?limit=3');
    expect(logs).toHaveLength(1);
    expect(logs[0]).toMatchObject({
      evidenceLogId: 'evidence-region-seoul-mapo-20260614',
      targetId: 'region-seoul-mapo',
      summary: '전세 우려와 학군 기대가 함께 관찰됩니다.',
      caveats: ['market_fact_partial'],
      confidence: 0.72
    });
  });
});
