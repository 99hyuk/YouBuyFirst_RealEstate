<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import TradingViewWidget from '../components/TradingViewWidget.vue';
import stockDetailFixtureSet from '../fixtures/stock-detail-fixtures.json';

type StockDetailFixture = {
  symbol: string;
  name: string;
  market: string;
  provider: string;
  providerSymbol: string;
  quoteSnapshot: {
    price: string;
    change: string;
    changeTone: 'up' | 'down';
    volume: string;
    asOf: string;
    stale: boolean;
    dataStatus: string;
    latencyLabel: string;
  };
  brief: {
    headline: string;
    summary: string;
    mood: string;
    note: string;
    score: string;
    scoreMeta: string;
    scoreLine: string;
    riskNote: string;
    reasons: string[];
  };
  yesterday: string[];
};

const route = useRoute();
const stockFixtures = stockDetailFixtureSet.items as StockDetailFixture[];

const routeSymbol = computed(() => String(route.params.symbol ?? stockFixtures[0].symbol).toUpperCase());
const stock = computed(
  () =>
    stockFixtures.find(
      (item) => item.symbol.toUpperCase() === routeSymbol.value || item.providerSymbol.toUpperCase() === routeSymbol.value
    ) ?? stockFixtures[0]
);
const quoteSnapshot = computed(() => stock.value.quoteSnapshot);
const topBrief = computed(() => stock.value.brief);
const tradingViewWidgets = [
  {
    marketLabel: '국내주식 위젯 테스트',
    title: '삼성전자',
    symbol: 'KRX:005930',
    note: 'TradingView 공개 위젯에서 KRX 심볼이 외부 embed로 표시되는지 확인하는 용도입니다.'
  },
  {
    marketLabel: '해외주식 위젯 테스트',
    title: 'NVIDIA',
    symbol: 'NASDAQ:NVDA',
    note: '미장 대표 심볼은 같은 공개 위젯에서 정상 표시되는지 비교합니다.'
  }
];

const topBriefMetrics = computed(() => [
  { label: '시황 점수', value: topBrief.value.score, meta: topBrief.value.scoreMeta },
  { label: '등락률', value: quoteSnapshot.value.change, meta: quoteSnapshot.value.price },
  { label: '거래량', value: quoteSnapshot.value.volume, meta: quoteSnapshot.value.dataStatus },
  { label: '시세 기준', value: quoteSnapshot.value.asOf.split(' ').at(-1) ?? quoteSnapshot.value.asOf, meta: quoteSnapshot.value.latencyLabel }
]);

const topBriefReasons = computed(() => topBrief.value.reasons);

const reactionTrend = [
  { period: '30분', mentions: 128, positive: 54, negative: 27, neutral: 19 },
  { period: '1일', mentions: 642, positive: 48, negative: 31, neutral: 21 },
  { period: '1주', mentions: 3184, positive: 43, negative: 34, neutral: 23 }
];

const quickStats = [
  { label: '반응 점수', value: '77', meta: '+12p · 30분' },
  { label: '언급 변화', value: '+34%', meta: '09:10 이후' },
  { label: '긍정/부정', value: '54 / 27', meta: '중립 19' },
  { label: '출처 수', value: '4개', meta: '편중 42%' },
  { label: '원문 링크', value: '5건', meta: '제목 링크' }
];

const keywordPulse = [
  { keyword: 'HBM', count: 46, tone: '긍정', delta: '+18' },
  { keyword: '수급', count: 31, tone: '중립', delta: '+9' },
  { keyword: '고가 부담', count: 19, tone: '부정', delta: '+7' },
  { keyword: '서버 수요', count: 17, tone: '긍정', delta: '+6' }
];

const intradaySnapshots = [
  { time: '09:00', mention: '42건', reaction: '+6p', price: '+0.2%' },
  { time: '09:15', mention: '81건', reaction: '+15p', price: '+0.5%' },
  { time: '09:30', mention: '119건', reaction: '+21p', price: '+1.0%' },
  { time: '09:45', mention: '128건', reaction: '+18p', price: '+1.2%' }
];

const sources = [
  { name: '네이버 종토방', mentions: 84, positive: 41, negative: 33, note: '보합·관망 표현이 많음' },
  { name: '디시 주식', mentions: 47, positive: 56, negative: 24, note: 'HBM 수요 키워드 강함' },
  { name: '뽐뿌 증권포럼', mentions: 22, positive: 38, negative: 36, note: '가격 부담 언급 혼재' },
  { name: '에펨코리아 주식', mentions: 44, positive: 61, negative: 18, note: '인기글 확산 빠름' }
];

const timeline = [
  { time: '08:55', type: '뉴스', title: '반도체 업황 회복 기대 기사 노출', impact: 'HBM·서버 수요 키워드 증가' },
  { time: '09:10', type: '커뮤니티', title: '디시·에펨코리아에서 HBM 언급 증가', impact: '긍정 표현 30분 전 대비 +18%' },
  { time: '09:35', type: '가격', title: '장중 고가 갱신 뒤 변동성 확대', impact: '가격 기준 15분 지연' },
  { time: '09:50', type: '인기글', title: '네이버 종토방 조회수 상위권 글 등장', impact: '원문 확인 필요' },
  { time: '10:00', type: '리포트', title: '목표가 상향 리포트 제목 수집', impact: '본문 미수집, 제목 링크만 표시' }
];

const evidenceLinks = [
  { type: '뉴스', source: '연합뉴스', title: '반도체 수요 회복 기대감 기사', url: 'https://www.yna.co.kr/' },
  { type: '리포트', source: '네이버 리서치', title: '메모리 업황 점검 리포트', url: 'https://finance.naver.com/research/' },
  { type: '영상', source: 'YouTube', title: '장중 반도체 업종 해설 영상', url: 'https://www.youtube.com/results?search_query=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90+%EB%B0%98%EB%8F%84%EC%B2%B4' },
  { type: '블로그', source: '네이버 블로그', title: '메모리 사이클 정리 글', url: 'https://blog.naver.com/' },
  { type: '커뮤니티', source: '네이버 금융', title: '조회수 상위 종목 토론 글', url: 'https://finance.naver.com/' }
];

const reliability = [
  { label: '표본 수', value: '128건', state: '보통' },
  { label: '커뮤니티 편중', value: '42%', state: '주의' },
  { label: '출처 다양성', value: '4개 소스', state: '양호' },
  { label: '가격 지연', value: '15분', state: '주의' },
  { label: '원문 확인', value: '필요', state: '주의' }
];
</script>

<template>
  <section class="surface-page stock-detail-page">
    <section class="stock-roast-panel panel" aria-label="종목 한줄평">
      <div class="stock-roast-topline">
        <div>
          <strong>{{ stock.name }}</strong>
          <span>{{ stock.symbol }} · {{ stock.market }}</span>
        </div>
        <RouterLink class="stock-roast-close" to="/stocks" aria-label="종목 랭킹으로 돌아가기">×</RouterLink>
      </div>

      <article class="stock-roast-banner">
        <span>{{ topBrief.mood }}</span>
        <h2>{{ topBrief.headline }}</h2>
        <p>{{ topBrief.summary }}</p>
      </article>

      <div class="stock-roast-digest">
        <p>
          <strong>{{ topBrief.scoreLine }}</strong>
          <span>{{ topBrief.note }}</span>
        </p>
        <em>{{ topBrief.riskNote }}</em>
      </div>

      <div class="stock-roast-metric-row" aria-label="한줄평 근거 지표">
        <article v-for="metric in topBriefMetrics" :key="metric.label">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <em>{{ metric.meta }}</em>
        </article>
      </div>

      <div class="stock-roast-reasons" aria-label="요약 근거">
        <b v-for="reason in topBriefReasons" :key="reason">{{ reason }}</b>
      </div>
    </section>

    <section class="stock-hero panel">
      <div class="stock-identity">
        <RouterLink class="detail-link stock-back-link" to="/stocks">← 종목 랭킹으로</RouterLink>
        <p class="eyebrow">selected stock detail</p>
        <h2>{{ stock.name }} <span>{{ stock.symbol }} · {{ stock.market }}</span></h2>
        <p>뉴스, 커뮤니티 반응, 가격 변화를 시간순으로 묶어 왜 반응이 움직였는지 확인합니다.</p>
      </div>
      <div class="stock-quote-board">
        <div>
          <span>quote snapshot · 현재가</span>
          <strong>{{ quoteSnapshot.price }}</strong>
          <em :class="quoteSnapshot.changeTone">{{ quoteSnapshot.change }}</em>
        </div>
        <div>
          <span>거래량</span>
          <strong>{{ quoteSnapshot.volume }}</strong>
          <em>{{ quoteSnapshot.dataStatus }}</em>
        </div>
        <div>
          <span>시세 기준</span>
          <strong>{{ quoteSnapshot.asOf }}</strong>
          <em :class="quoteSnapshot.stale ? 'warn' : 'ok'">{{ quoteSnapshot.stale ? 'stale' : quoteSnapshot.latencyLabel }}</em>
        </div>
      </div>
    </section>

    <section class="stock-main-chart panel content-feed-card surface-data-card" aria-label="TradingView 공개 위젯 테스트">
      <div class="panel-header">
        <div>
          <p class="label">TradingView embed</p>
          <h3>국내/해외 TradingView 위젯 비교</h3>
        </div>
        <span class="status-pill subtle">KRX:005930 · NASDAQ:NVDA</span>
      </div>
      <div class="tradingview-widget-grid">
        <TradingViewWidget
          v-for="widget in tradingViewWidgets"
          :key="widget.symbol"
          :market-label="widget.marketLabel"
          :title="widget.title"
          :symbol="widget.symbol"
          :note="widget.note"
        />
      </div>
      <p class="chart-data-note">
        위 영역은 우리 데이터 재구성 차트가 아니라 TradingView 공개 embed 위젯입니다. 현재가·등락률·거래량·asOf·stale 상태는 기존 quote snapshot 영역과 분리해서 봅니다.
      </p>
    </section>

    <section class="dense-summary-strip stock-density-strip" aria-label="종목 요약 지표">
      <article v-for="item in quickStats" :key="item.label" class="panel dense-metric-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <em>{{ item.meta }}</em>
      </article>
    </section>

    <section class="stock-compact-grid">
      <article class="panel content-feed-card surface-data-card stock-keyword-card">
        <div class="panel-header compact">
          <div>
            <p class="label">keyword pulse</p>
            <h3>반응 키워드</h3>
          </div>
          <span class="status-pill subtle">30분</span>
        </div>
        <div class="keyword-pulse-grid">
          <article v-for="keyword in keywordPulse" :key="keyword.keyword">
            <strong>{{ keyword.keyword }}</strong>
            <span>{{ keyword.tone }}</span>
            <em>{{ keyword.count }}건 · {{ keyword.delta }}</em>
          </article>
        </div>
      </article>

      <article class="panel content-feed-card surface-data-card stock-snapshot-card">
        <div class="panel-header compact">
          <div>
            <p class="label">intraday snapshot</p>
            <h3>시간대별 변화</h3>
          </div>
        </div>
        <div class="mini-table-list">
          <article v-for="snapshot in intradaySnapshots" :key="snapshot.time">
            <time>{{ snapshot.time }}</time>
            <span>언급 {{ snapshot.mention }}</span>
            <strong>{{ snapshot.reaction }}</strong>
            <em>{{ snapshot.price }}</em>
          </article>
        </div>
      </article>
    </section>

    <section class="stock-layout-grid">
      <article class="panel content-feed-card surface-data-card reaction-trend-panel stock-reaction-card">
        <div class="panel-header">
          <div>
            <p class="label">reaction trend</p>
            <h3>커뮤니티 반응 추이</h3>
          </div>
          <span class="status-pill subtle">30분 · 1일 · 1주</span>
        </div>
        <div class="trend-period-grid">
          <article v-for="period in reactionTrend" :key="period.period">
            <div>
              <span>{{ period.period }}</span>
              <strong>{{ period.mentions }}건</strong>
            </div>
            <div class="ratio-track">
              <i class="positive" :style="{ width: `${period.positive}%` }"></i>
              <i class="negative" :style="{ width: `${period.negative}%` }"></i>
              <i class="neutral" :style="{ width: `${period.neutral}%` }"></i>
            </div>
            <p>긍정 {{ period.positive }} · 부정 {{ period.negative }} · 중립 {{ period.neutral }}</p>
          </article>
        </div>
      </article>

      <article class="panel content-feed-card surface-data-card yesterday-panel stock-delta-card">
        <div class="panel-header compact">
          <div>
            <p class="label">daily delta</p>
            <h3>어제와 달라진 점</h3>
          </div>
        </div>
        <ul class="clean-list">
          <li v-for="item in stock.yesterday" :key="item">{{ item }}</li>
        </ul>
      </article>
    </section>

    <section class="panel content-feed-card surface-data-card source-reaction-panel stock-source-card">
      <div class="panel-header">
        <div>
          <p class="label">source reaction</p>
          <h3>소스별 반응</h3>
        </div>
        <span class="status-pill warning">단일 소스 과신 금지</span>
      </div>
      <div class="source-reaction-grid">
        <article v-for="source in sources" :key="source.name">
          <div class="source-row-head">
            <strong>{{ source.name }}</strong>
            <span>{{ source.mentions }}건</span>
          </div>
          <div class="ratio-track">
            <i class="positive" :style="{ width: `${source.positive}%` }"></i>
            <i class="negative" :style="{ width: `${source.negative}%` }"></i>
            <i class="neutral" :style="{ width: `${100 - source.positive - source.negative}%` }"></i>
          </div>
          <p>{{ source.note }}</p>
        </article>
      </div>
    </section>

    <section class="panel content-feed-card surface-data-card stock-event-panel stock-timeline-card">
      <div class="panel-header">
        <div>
          <p class="label">event timeline</p>
          <h3>뉴스·공시·가격·커뮤니티 타임라인</h3>
        </div>
        <span class="status-pill subtle">시간순 mock</span>
      </div>
      <div class="vertical-timeline">
        <article v-for="event in timeline" :key="`${event.time}-${event.title}`">
          <time>{{ event.time }}</time>
          <span>{{ event.type }}</span>
          <div>
            <strong>{{ event.title }}</strong>
            <p>{{ event.impact }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="stock-layout-grid">
      <article class="panel content-feed-card surface-data-card evidence-panel stock-evidence-card">
        <div class="panel-header">
          <div>
            <p class="label">evidence links</p>
            <h3>근거 링크</h3>
          </div>
          <span class="status-pill subtle">제목 링크만 표시</span>
        </div>
        <div class="evidence-list">
          <a v-for="link in evidenceLinks" :key="link.title" :href="link.url" target="_blank" rel="noreferrer noopener">
            <span>{{ link.type }}</span>
            <strong>{{ link.title }}</strong>
            <em>{{ link.source }} →</em>
          </a>
        </div>
      </article>

      <article class="panel content-feed-card surface-data-card reliability-panel stock-reliability-card">
        <div class="panel-header compact">
          <div>
            <p class="label">signal reliability</p>
            <h3>신호 신뢰도</h3>
          </div>
        </div>
        <div class="reliability-grid">
          <div v-for="item in reliability" :key="item.label">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <em :class="item.state === '주의' ? 'warn' : 'ok'">{{ item.state }}</em>
          </div>
        </div>
      </article>
    </section>
  </section>
</template>
