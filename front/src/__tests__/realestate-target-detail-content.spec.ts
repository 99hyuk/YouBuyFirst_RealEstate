import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import RegionDetailPage from '../pages/RegionDetailPage.vue';

const mountTargetDetail = async (path = '/realestate/targets/region-seoul-mapo') => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/realestate/targets/:targetId', component: RegionDetailPage },
      { path: '/realestate/reactions', component: { template: '<div />' } }
    ]
  });

  router.push(path);
  await router.isReady();

  const wrapper = mount(RegionDetailPage, {
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
});

describe('real-estate target detail content feed', () => {
  it('uses approved target content API rows as evidence links', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      items: [
        {
          contentId: 'content-mapo-jeonse-20260612',
          sourceId: 'ddangzipgo',
          contentType: 'news',
          title: '마포 전세 매물 체감 원문 확인',
          snippet: '전세 매물 감소 체감 반응이 늘었습니다.',
          url: 'https://example.com/mapo-jeonse',
          domain: 'example.com',
          publishedAt: '2026-06-12T04:00:00Z',
          metricLabel: '댓글 42',
          statusLabel: '승인 링크',
          ingestedAt: '2026-06-12T04:10:00Z',
          dataStatus: 'ok',
          targetId: 'region-seoul-mapo',
          linkType: 'mentioned',
          confidence: 0.91,
          reviewState: 'approved'
        }
      ]
    })));
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountTargetDetail();

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/content?feed=all&limit=6');
    expect(wrapper.text()).toContain('content API 반영');
    expect(wrapper.text()).toContain('마포 전세 매물 체감 원문 확인');
    expect(wrapper.text()).toContain('땅집고');
    expect(wrapper.text()).toContain('2026-06-12 · 댓글 42');
    expect(wrapper.text()).not.toContain('원문 후보 묶음');
  });

  it('renders the embedded complex map fallback on region targets', async () => {
    const wrapper = await mountTargetDetail();

    expect(wrapper.find('[data-testid="kakao-complex-map"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="kakao-map-fallback"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="complex-map-inspector"]').text()).toContain('마포래미안푸르지오');
    expect(wrapper.text()).toContain('단지 위치 레이어');
    expect(wrapper.text()).toContain('mock fallback');
    expect(wrapper.text()).toContain('fixture fallback');
    expect(wrapper.text()).toContain('mock 좌표');
  });

  it('uses nearby complex API markers before the local fixture markers', async () => {
    const fetcher = vi.fn(async (input: string) => {
      if (input.includes('/nearby-complexes')) {
        return new Response(JSON.stringify({
          items: [
            {
              targetId: 'complex-api-marker',
              name: 'API 단지 marker',
              address: '서울 마포구 API로 일대',
              region: '서울 마포구',
              latitude: 37.551,
              longitude: 126.955,
              tone: 'up',
              price: '16.1억',
              change: '+0.44%',
              reaction: 'API 반응 요약',
              provider: 'complex_api_test',
              asOf: '2026-06-14T00:00:00Z',
              dataStatus: 'candidate',
              stale: true,
              note: 'API marker 우선 사용'
            }
          ]
        }));
      }
      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountTargetDetail();

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/nearby-complexes?limit=20');
    expect(wrapper.find('[data-testid="complex-map-inspector"]').text()).toContain('API 단지 marker');
    expect(wrapper.text()).toContain('marker API 반영');
    expect(wrapper.text()).toContain('candidate · stale');
    expect(wrapper.text()).not.toContain('마포래미안푸르지오');
  });

  it('uses target timeline API rows before the local fixture timeline', async () => {
    const fetcher = vi.fn(async (input: string) => {
      if (input.includes('/timeline')) {
        return new Response(JSON.stringify({
          items: [
            {
              id: 'timeline-policy-mapo-20260614',
              targetId: 'region-seoul-mapo',
              eventType: 'policy',
              sourceRefType: 'policy_event',
              sourceRefId: 'policy-mapo-20260614',
              title: '마포 주거정비 후보지 발표',
              summary: '정책 발표 이후 정비사업 기대와 가격 부담 우려가 함께 언급됩니다.',
              occurredAt: '2026-06-14T09:30:00Z',
              asOf: '2026-06-14T09:35:00Z',
              dataStatus: 'ok'
            }
          ]
        }));
      }
      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountTargetDetail();

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/timeline?limit=6');
    expect(wrapper.text()).toContain('timeline API 반영');
    expect(wrapper.text()).toContain('마포 주거정비 후보지 발표');
    expect(wrapper.text()).toContain('정책 발표 이후 정비사업 기대와 가격 부담 우려');
    expect(wrapper.text()).toContain('policy · ok');
    expect(wrapper.text()).not.toContain('전세 우려 급증');
  });

  it('keeps same-minute timeline API rows keyed without duplicate warnings', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const fetcher = vi.fn(async (input: string) => {
      if (input.includes('/timeline')) {
        return new Response(JSON.stringify({
          items: [
            {
              id: 'timeline-market-mapo-20260614-a',
              targetId: 'region-seoul-mapo',
              eventType: 'market_fact',
              sourceRefType: 'market_fact',
              sourceRefId: 'fact-a',
              title: '매매 실거래 공개',
              summary: '첫 번째 실거래 이벤트입니다.',
              occurredAt: '2026-06-14T09:00:00Z',
              asOf: '2026-06-14T09:05:00Z',
              dataStatus: 'ok'
            },
            {
              id: 'timeline-market-mapo-20260614-b',
              targetId: 'region-seoul-mapo',
              eventType: 'market_fact',
              sourceRefType: 'market_fact',
              sourceRefId: 'fact-b',
              title: '매매 실거래 공개',
              summary: '두 번째 실거래 이벤트입니다.',
              occurredAt: '2026-06-14T09:00:00Z',
              asOf: '2026-06-14T09:05:00Z',
              dataStatus: 'ok'
            }
          ]
        }));
      }
      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountTargetDetail();

    expect(wrapper.findAll('.vertical-timeline article')).toHaveLength(2);
    expect(wrapper.text()).toContain('첫 번째 실거래 이벤트입니다.');
    expect(wrapper.text()).toContain('두 번째 실거래 이벤트입니다.');
    expect(warnSpy.mock.calls.some((call) => String(call[0]).includes('Duplicate keys'))).toBe(false);
  });

  it('uses target evidence log API rows as the agent rationale card', async () => {
    const fetcher = vi.fn(async (input: string) => {
      if (input.includes('/evidence-logs')) {
        return new Response(JSON.stringify({
          items: [
            {
              evidenceLogId: 'evidence-region-seoul-mapo-20260614',
              targetId: 'region-seoul-mapo',
              snapshotId: 12,
              evaluationVersion: 'realestate-eval-v1',
              promptVersion: 'realestate-eval-prompt-v1',
              modelName: 'gpt-5-mini',
              tone: 'watch',
              summary: '전세 우려와 학군 기대가 함께 관찰됩니다.',
              subtitle: '반응 지표, 실거래, timeline event를 함께 본 룰 기반 평가',
              caveats: ['timeline_event_missing', 'market_fact_partial'],
              dataQuality: 'partial',
              confidence: 0.72,
              skipReason: null,
              evaluatedAt: '2026-06-14T09:20:00Z',
              asOf: '2026-06-14T09:15:00Z',
              evidenceItems: [
                {
                  evidenceItemId: 'evidence-item-reaction-1',
                  evidenceType: 'reaction',
                  refType: 'reaction_snapshot',
                  refId: 'snapshot-region-seoul-mapo',
                  label: '언급 증가',
                  valueText: '+42%',
                  severity: 'watch'
                },
                {
                  evidenceItemId: 'evidence-item-market-1',
                  evidenceType: 'market_fact',
                  refType: 'market_fact',
                  refId: 'fact-region-seoul-mapo',
                  label: '전세가율',
                  valueText: '64.8%',
                  severity: 'info'
                }
              ]
            }
          ]
        }));
      }
      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountTargetDetail();

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/evidence-logs?limit=3');
    expect(wrapper.text()).toContain('AI 근거 로그');
    expect(wrapper.text()).toContain('EvidenceLog API 반영');
    expect(wrapper.text()).toContain('전세 우려와 학군 기대가 함께 관찰됩니다.');
    expect(wrapper.text()).toContain('반응 지표, 실거래, timeline event를 함께 본 룰 기반 평가');
    expect(wrapper.text()).toContain('언급 증가');
    expect(wrapper.text()).toContain('+42%');
    expect(wrapper.text()).toContain('전세가율');
    expect(wrapper.text()).toContain('64.8%');
    expect(wrapper.text()).toContain('timeline_event_missing');
    expect(wrapper.text()).toContain('신뢰도 72%');
    expect(wrapper.text()).toContain('realestate-eval-v1');
  });

  it('opens a complex target detail with the same map and report frame', async () => {
    const wrapper = await mountTargetDetail('/realestate/targets/complex-mapo-raemian-prugio');

    expect(wrapper.find('.unsupported-region-state').exists()).toBe(false);
    expect(wrapper.text()).toContain('마포래미안푸르지오');
    expect(wrapper.text()).toContain('마래푸');
    expect(wrapper.text()).toContain('단지 위치 레이어');
    expect(wrapper.find('[data-testid="complex-map-inspector"]').text()).toContain('학군·역세권 언급 증가');
  });
});
