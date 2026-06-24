import { RouterLinkStub, flushPromises, mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';

import DailyBriefingPage from '../pages/DailyBriefingPage.vue';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('daily briefing page', () => {
  it('renders the stored narrative briefing without time-window section labels', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost');

      if (url.pathname === '/api/realestate/daily-briefings/latest') {
        return new Response(JSON.stringify({
          briefingId: 'daily-briefing-20260624-v1',
          briefingDate: '2026-06-24',
          title: '오늘의 부동산 시장 브리핑',
          summaryHeadlines: [
            '수도권 전세 압력 재부각',
            '서울 동남권 거래 회복 흐름',
            '경기 남부 공급·정책 이슈 집중'
          ],
          sections: [
            {
              sectionId: 'flow',
              title: '오늘의 핵심 흐름',
              body: [
                '전세 압력과 거래 회복 흐름이 함께 관찰되는지가 오늘 브리핑의 출발점입니다.',
                '단기 뉴스만 떼어 보면 세제 논의와 공급 일정이 각각 분리된 사건처럼 보이지만, 실제 시장 체감은 전세 가격 부담, 매매 대기 수요, 입주 물량 기대가 겹치며 형성됩니다.',
                '따라서 이번 흐름은 가격 방향 단정이 아니라 수도권 핵심 생활권의 수급 압력이 다시 논의의 중심으로 올라왔다는 신호로 읽어야 합니다.'
              ].join('\n\n'),
              displayOrder: 1
            },
            {
              sectionId: 'regions',
              title: '주목할 지역과 이유',
              body: '서울 동남권과 경기 남부의 흐름을 같이 봅니다.',
              displayOrder: 2
            },
            {
              sectionId: 'variables',
              title: '시장 변수',
              body: '보유·양도세 방향과 미실현 이익 과세 논의가 핵심 변수입니다. 공급 일정은 별도 점검 사안입니다.',
              displayOrder: 3
            },
            {
              sectionId: 'sources',
              title: '관련 뉴스·리포트',
              body: '이번 브리핑은 세제 개편 보도와 지역별 거래·공급 흐름 자료를 함께 묶어 작성했습니다.',
              displayOrder: 4
            }
          ],
          focusRegions: [
            { targetId: 'region-seoul', label: '서울', reason: '거래 회복 흐름', displayOrder: 1 }
          ],
          sourceItems: [
            {
              sourceItemId: 'map-region-1',
              sourceType: 'map_layer',
              label: '전국 지역 지도',
              title: '서울특별시 지역 흐름',
              url: null,
              displayOrder: 1
            },
            {
              sourceItemId: 'source-news-1',
              sourceType: 'content',
              label: '정책 리포트',
              title: '수도권 전세 보고서',
              url: 'https://example.com/report',
              displayOrder: 2
            }
          ]
        }));
      }

      return new Response(JSON.stringify({}));
    }));

    const wrapper = mount(DailyBriefingPage, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub
        }
      }
    });
    await flushPromises();

    expect(wrapper.text()).toContain('오늘의 부동산 시장 브리핑');
    expect(wrapper.find('.daily-briefing-hero-panel').exists()).toBe(true);
    expect(wrapper.find('.daily-briefing-report-layout').exists()).toBe(true);
    expect(wrapper.find('.daily-briefing-primary-panel').exists()).toBe(true);
    expect(wrapper.get('.daily-briefing-column-lead').text()).toContain('오늘 브리핑의 출발점');
    expect(wrapper.findAll('.daily-briefing-column-body p')).toHaveLength(2);
    expect(wrapper.find('.daily-briefing-region-ledger').exists()).toBe(true);
    expect(wrapper.find('.daily-briefing-variable-list').exists()).toBe(true);
    expect(wrapper.findAll('.daily-briefing-variable-list li')).toHaveLength(2);
    expect(wrapper.findAll('.daily-briefing-variable-list li')[0].text()).toContain('보유·양도세 방향');
    expect(wrapper.find('.daily-briefing-source-ledger').exists()).toBe(true);
    expect(wrapper.findAll('.daily-briefing-headline-card strong').map((item) => item.text())).toEqual([
      '수도권 전세 압력 재부각',
      '서울 동남권 거래 회복 흐름',
      '경기 남부 공급·정책 이슈 집중'
    ]);
    expect(wrapper.text()).toContain('오늘의 핵심 흐름');
    expect(wrapper.text()).toContain('주목할 지역과 이유');
    expect(wrapper.text()).toContain('시장 변수');
    expect(wrapper.text()).toContain('관련 뉴스·리포트');
    expect(wrapper.findAll('.daily-briefing-source-row')[0].attributes('href')).toBe('https://example.com/report');
    expect(wrapper.findAll('.daily-briefing-source-row')[1].attributes('href')).toBeUndefined();
    expect(wrapper.get('.daily-briefing-source-summary').text()).toContain('세제 개편 보도');
    expect(wrapper.findAll('.daily-briefing-related-link').map((item) => item.text())).toEqual([
      expect.stringContaining('뉴스룸'),
      expect.stringContaining('정책·통계 리포트'),
      expect.stringContaining('주요 일정'),
      expect.stringContaining('전국 지역 지도')
    ]);
    expect(wrapper.text()).not.toContain('24시간');
    expect(wrapper.text()).not.toContain('7일');
    expect(wrapper.text()).not.toContain('1개월');
    expect(wrapper.text()).not.toContain('3개월');
    expect(wrapper.text()).not.toContain('본문 근거 요약');
    expect(wrapper.find('.daily-briefing-section-list').exists()).toBe(false);
  });

  it('links to internal evidence surfaces instead of repeating the body when source links are missing', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost');

      if (url.pathname === '/api/realestate/daily-briefings/latest') {
        return new Response(JSON.stringify({
          briefingId: 'daily-briefing-20260624-v1',
          briefingDate: '2026-06-24',
          title: '오늘의 부동산 시장 브리핑',
          summaryHeadlines: [
            '수도권 전세 압력 재부각',
            '서울 동남권 거래 회복 흐름',
            '경기 남부 공급·정책 이슈 집중'
          ],
          sections: [
            {
              sectionId: 'flow',
              title: '오늘의 핵심 흐름',
              body: '전세 압력과 거래 회복 흐름이 함께 관찰됩니다.',
              displayOrder: 1
            },
            {
              sectionId: 'sources',
              title: '관련 뉴스·리포트',
              body: '뉴스룸과 공식 일정에서 추가 확인합니다.',
              displayOrder: 4
            }
          ],
          focusRegions: [],
          sourceItems: []
        }));
      }

      return new Response(JSON.stringify({}));
    }));

    const wrapper = mount(DailyBriefingPage, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub
        }
      }
    });
    await flushPromises();

    expect(wrapper.findAll('.daily-briefing-source-row')).toHaveLength(0);
    expect(wrapper.find('.daily-briefing-related-links').exists()).toBe(true);
    expect(wrapper.findAll('.daily-briefing-related-link')).toHaveLength(4);
    expect(wrapper.text()).toContain('관련 확인 화면');
    expect(wrapper.text()).toContain('내부 자료로 이어보기');
    expect(wrapper.text()).not.toContain('본문 근거 요약');
  });
});
