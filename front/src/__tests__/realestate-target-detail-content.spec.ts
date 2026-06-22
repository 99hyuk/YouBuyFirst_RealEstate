import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterEach, describe, expect, it, vi } from 'vitest';

import RegionDetailPage from '../pages/RegionDetailPage.vue';

const mountTargetDetail = async (path = '/realestate/targets/region-seoul-mapo') => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/realestate/targets/:targetId', component: RegionDetailPage },
      { path: '/realestate/transactions', component: { template: '<div />' } }
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
    expect(wrapper.text()).toContain('근거 링크 반영');
    expect(wrapper.text()).toContain('마포 전세 매물 체감 원문 확인');
    expect(wrapper.text()).toContain('땅집고');
    expect(wrapper.text()).toContain('2026-06-12 · 댓글 42');
    expect(wrapper.text()).not.toContain('원문 후보 묶음');
  });

  it('keeps missing marker API data as insufficient instead of local fixture markers', async () => {
    const wrapper = await mountTargetDetail();

    expect(wrapper.find('[data-testid="kakao-complex-map"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('단지 좌표 수집 전');
    expect(wrapper.text()).toContain('단지 좌표 수집 전/insufficient');
    expect(wrapper.text()).toContain('검증된 단지 좌표가 들어오면');
    expect(wrapper.text()).not.toContain('좌표 후보/검증 전');
    expect(wrapper.text()).not.toContain('좌표 검증 전');
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
    expect(wrapper.text()).toContain('지도 좌표 반영');
    expect(wrapper.text()).toContain('좌표 후보 · 갱신 지연');
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
    expect(wrapper.text()).toContain('일정 반영');
    expect(wrapper.text()).toContain('마포 주거정비 후보지 발표');
    expect(wrapper.text()).toContain('정책 발표 이후 정비사업 기대와 가격 부담 우려');
    expect(wrapper.text()).toContain('정책 · 반영');
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
                },
                {
                  evidenceItemId: 'evidence-item-search-1',
                  evidenceType: 'search_candidate',
                  refType: 'content',
                  refId: 'serpapi-issue-mapo',
                  label: '최근 이슈 후보',
                  valueText: '마포 교통 정책 기사 후보',
                  severity: 'info',
                  sourceUrl: 'https://example.com/news/mapo-transport',
                  sourceId: 'serpapi:google_news',
                  sourceDomain: 'example.com',
                  publishedAt: '2026-06-14T08:00:00Z',
                  sourceDataStatus: 'candidate'
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

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul-mapo/evidence-logs?limit=1');
    expect(wrapper.text()).toContain('AI 근거 로그');
    expect(wrapper.text()).toContain('AI 근거 반영');
    expect(wrapper.text()).toContain('전세 우려와 학군 기대가 함께 관찰됩니다.');
    expect(wrapper.text()).toContain('반응 지표, 실거래, timeline event를 함께 본 룰 기반 평가');
    expect(wrapper.text()).toContain('언급 증가');
    expect(wrapper.text()).toContain('+42%');
    expect(wrapper.text()).toContain('전세가율');
    expect(wrapper.text()).toContain('64.8%');
    expect(wrapper.text()).toContain('최근 이슈 후보');
    expect(wrapper.text()).toContain('마포 교통 정책 기사 후보');
    const evidenceLink = wrapper.get('a[href="https://example.com/news/mapo-transport"]');
    expect(evidenceLink.text()).toContain('최근 이슈 후보');
    expect(evidenceLink.attributes('rel')).toContain('noopener');
    expect(wrapper.text()).toContain('serpapi:google_news');
    expect(wrapper.text()).toContain('candidate');
    expect(wrapper.text()).toContain('타임라인 미연결');
    expect(wrapper.text()).toContain('시장 사실 일부 반영');
    expect(wrapper.text()).toContain('신뢰도 72%');
    expect(wrapper.text()).toContain('realestate-eval-v1');
  });

  it('shows live evidence logs for top ranking targets that do not have local detail fixtures yet', async () => {
    const fetcher = vi.fn(async (input: string) => {
      if (input.includes('/evidence-logs')) {
        return new Response(JSON.stringify({
          items: [
            {
              evidenceLogId: 'evidence-region-seoul-20260615',
              targetId: 'region-seoul',
              snapshotId: 31,
              evaluationVersion: 'realestate-eval-v1',
              promptVersion: 'gms-evidence-v1',
              modelName: 'gpt-5-mini',
              tone: 'watch',
              summary: '서울특별시는 national_market_fact_only / similar_window_missing / asOf 상태를 함께 확인해야 하는 관찰 구간입니다.',
              subtitle: 'TOP10 반응 snapshot 및 시장 사실 기반 EvidenceLog입니다.',
              caveats: ['source_skewed', 'national_market_fact_only', 'similar_window_missing'],
              dataQuality: 'partial',
              confidence: 0.66,
              skipReason: null,
              evaluatedAt: '2026-06-15T01:00:00Z',
              asOf: '2026-06-15T00:00:00Z',
              evidenceItems: [
                {
                  evidenceItemId: 'evidence-item-seoul-reaction',
                  evidenceType: 'reaction',
                  refType: 'reaction_snapshot',
                  refId: 'snapshot-region-seoul',
                  label: '24시간 언급 TOP',
                  valueText: '1위',
                  severity: 'watch'
                }
              ]
            }
          ]
        }));
      }
      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountTargetDetail('/realestate/targets/region-seoul');

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/region-seoul/evidence-logs?limit=1');
    expect(wrapper.find('.unsupported-region-state').exists()).toBe(false);
    expect(wrapper.find('.live-evidence-region-state').exists()).toBe(true);
    expect(wrapper.text()).toContain('연결된 후보 리포트');
    expect(wrapper.text()).toContain('후보 상세 데이터가 먼저 연결되었습니다');
    expect(wrapper.text()).toContain('AI 근거 반영');
    expect(wrapper.text()).toContain('서울특별시는 전국 지표만 반영 / 유사 과거 미연결 / 기준 시각 상태를 함께 확인해야 하는 관찰 구간입니다.');
    expect(wrapper.text()).toContain('TOP10 반응 집계 자료 및 시장 사실 기반 근거 로그입니다.');
    expect(wrapper.text()).not.toContain('national_market_fact_only');
    expect(wrapper.text()).not.toContain('similar_window_missing');
    expect(wrapper.text()).not.toContain('EvidenceLog');
    expect(wrapper.text()).not.toContain('snapshot');
    expect(wrapper.text()).not.toContain('asOf');
    expect(wrapper.text()).toContain('24시간 언급 TOP');
    expect(wrapper.text()).toContain('gms-evidence-v1');
  });

  it('opens a complex target detail without filling local fixture report values', async () => {
    const wrapper = await mountTargetDetail('/realestate/targets/complex-mapo-raemian-prugio');

    expect(wrapper.find('.unsupported-region-state').exists()).toBe(false);
    expect(wrapper.text()).toContain('마포래미안푸르지오');
    expect(wrapper.text()).toContain('AI 근거 리포트 수집 전/insufficient');
    expect(wrapper.text()).toContain('단지 좌표 수집 전');
    expect(wrapper.text()).toContain('AI 근거 항목 수집 전/insufficient');
    expect(wrapper.text()).not.toContain('마래푸');
    expect(wrapper.find('[data-testid="complex-map-inspector"]').exists()).toBe(false);
  });

  it('loads map markers for dynamically registered apartment targets', async () => {
    const fetcher = vi.fn(async (input: string) => {
      if (input.includes('/nearby-complexes')) {
        return new Response(JSON.stringify({
          items: [
            {
              targetId: 'complex-community-imun-ipark-xi',
              name: '이문아이파크자이',
              address: '서울 동대문구 이문동 일대',
              region: '서울 동대문구',
              latitude: 37.601,
              longitude: 127.061,
              tone: 'up',
              price: '확인 필요',
              change: '+0.12%',
              reaction: '커뮤니티 언급 증가',
              provider: 'community_observed',
              asOf: '2026-06-16T00:00:00Z',
              dataStatus: 'candidate',
              stale: true,
              note: '커뮤니티 관찰 단지 좌표 후보'
            }
          ]
        }));
      }
      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountTargetDetail('/realestate/targets/complex-community-imun-ipark-xi');

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/complex-community-imun-ipark-xi/nearby-complexes?limit=20');
    expect(wrapper.find('[data-testid="kakao-complex-map"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="complex-map-inspector"]').text()).toContain('이문아이파크자이');
    expect(wrapper.text()).toContain('지도 좌표 반영');
    expect(wrapper.text()).not.toContain('아직 상세 리포트가 연결되지 않았습니다');
  });

  it('shows the latest apartment trades between the embedded map and AI evidence log', async () => {
    const fetcher = vi.fn(async (input: string) => {
      if (input.includes('/market-facts')) {
        return new Response(JSON.stringify({
          items: [
            {
              factType: 'apt_trade',
              provider: 'molit',
              providerDataset: 'molit_apt_trade',
              legalDongCode: '11680',
              observedAt: '2026-06-12',
              asOf: '2026-06-13',
              valueJson: {
                apartmentName: '래미안신반포팰리스',
                dealAmountManwon: 325000,
                exclusiveAreaM2: 84.93,
                floor: 12
              },
              dataStatus: 'ok',
              stale: false
            },
            {
              factType: 'apt_trade',
              provider: 'molit',
              providerDataset: 'molit_apt_trade',
              legalDongCode: '11680',
              observedAt: '2026-06-02',
              asOf: '2026-06-13',
              valueJson: {
                apartmentName: '래미안신반포팰리스',
                dealAmountManwon: 318000,
                exclusiveAreaM2: 84.97,
                floor: 8
              },
              dataStatus: 'ok',
              stale: false
            }
          ]
        }));
      }
      if (input.includes('/nearby-complexes')) {
        return new Response(JSON.stringify({
          items: [
            {
              targetId: 'complex-ssafy-home-11680-4474',
              name: '래미안신반포팰리스',
              address: '서울 서초구 잠원동',
              region: '서울 서초구',
              latitude: 37.514,
              longitude: 127.012,
              tone: 'up',
              price: '32.5억원',
              change: '+0.18%',
              reaction: '커뮤니티 관심 후보',
              provider: 'ssafy_home',
              asOf: '2026-06-13T00:00:00Z',
              dataStatus: 'verified',
              stale: false
            }
          ]
        }));
      }
      return new Response(JSON.stringify({ items: [] }));
    });
    vi.stubGlobal('fetch', fetcher);

    const wrapper = await mountTargetDetail('/realestate/targets/complex-ssafy-home-11680-4474');

    expect(fetcher).toHaveBeenCalledWith('/api/realestate/targets/complex-ssafy-home-11680-4474/market-facts?factType=apt_trade&limit=5&officialOnly=true');
    expect(wrapper.text()).toContain('최근 매매 거래');
    expect(wrapper.text()).toContain('거래 내역 반영');
    expect(wrapper.text()).toContain('래미안신반포팰리스');
    expect(wrapper.text()).toContain('32.50억원');
    expect(wrapper.text()).toContain('전용 84.93㎡');
    expect(wrapper.text()).toContain('12층');

    const mapIndex = wrapper.text().indexOf('단지 위치 레이어');
    const tradeIndex = wrapper.text().indexOf('최근 매매 거래');
    const evidenceIndex = wrapper.text().indexOf('AI 근거 로그');
    expect(mapIndex).toBeGreaterThanOrEqual(0);
    expect(tradeIndex).toBeGreaterThan(mapIndex);
    expect(evidenceIndex).toBeGreaterThan(tradeIndex);
  });
});
