<script setup lang="ts">
type StockRankingRow = {
  rank: number;
  name: string;
  symbol: string;
  market: string;
  price: string;
  change: string;
  volume: string;
  volumeDelta: string;
  positive: number;
  negative: number;
  event: string;
  freshness: string;
  tone: 'up' | 'down';
};

const domesticRows: StockRankingRow[] = [
  { rank: 1, name: '삼성전자', symbol: '005930', market: 'KRX', price: '78,200원', change: '+1.24%', volume: '18.4M', volumeDelta: '+34%', positive: 54, negative: 27, event: 'HBM·서버 수요', freshness: '09:50 · 지연', tone: 'up' },
  { rank: 2, name: 'KODEX 200', symbol: '069500', market: 'ETF', price: '38,420원', change: '+0.42%', volume: '12.8M', volumeDelta: '+11%', positive: 39, negative: 24, event: '지수 추종', freshness: '09:50 · mock', tone: 'up' },
  { rank: 3, name: 'SK하이닉스', symbol: '000660', market: 'KRX', price: '184,800원', change: '+2.18%', volume: '9.8M', volumeDelta: '+27%', positive: 61, negative: 19, event: '메모리 가격', freshness: '09:49 · 지연', tone: 'up' },
  { rank: 4, name: '두산로보틱스', symbol: '454910', market: 'KRX', price: '132,100원', change: '+4.80%', volume: '7.4M', volumeDelta: '+29%', positive: 63, negative: 18, event: '로봇·공시', freshness: '09:46 · 지연', tone: 'up' },
  { rank: 5, name: 'NAVER', symbol: '035420', market: 'KRX', price: '182,600원', change: '+0.70%', volume: '6.2M', volumeDelta: '+18%', positive: 29, negative: 48, event: '비용 우려', freshness: '09:43 · 지연', tone: 'up' },
  { rank: 6, name: '에코프로', symbol: '086520', market: 'KRX', price: '128,600원', change: '-1.10%', volume: '5.9M', volumeDelta: '+24%', positive: 34, negative: 46, event: '2차전지 수급', freshness: '09:45 · 지연', tone: 'down' },
  { rank: 7, name: '한미반도체', symbol: '042700', market: 'KRX', price: '171,500원', change: '+3.20%', volume: '4.8M', volumeDelta: '+22%', positive: 58, negative: 21, event: '장비 수주', freshness: '09:47 · mock', tone: 'up' },
  { rank: 8, name: 'LG전자', symbol: '066570', market: 'KRX', price: '238,500원', change: '+0.90%', volume: '4.3M', volumeDelta: '+15%', positive: 44, negative: 32, event: '전장 키워드', freshness: '09:42 · 지연', tone: 'up' },
  { rank: 9, name: '현대차', symbol: '005380', market: 'KRX', price: '242,000원', change: '-0.80%', volume: '3.9M', volumeDelta: '+9%', positive: 36, negative: 41, event: '환율·수출', freshness: '09:41 · 지연', tone: 'down' },
  { rank: 10, name: '삼성SDI', symbol: '006400', market: 'KRX', price: '356,000원', change: '-1.30%', volume: '3.2M', volumeDelta: '+8%', positive: 31, negative: 47, event: '배터리 마진', freshness: '09:39 · mock', tone: 'down' }
];

const overseasRows: StockRankingRow[] = [
  { rank: 1, name: 'Tesla', symbol: 'TSLA', market: 'NASDAQ', price: '$176.49', change: '-0.42%', volume: '84.1M', volumeDelta: '+16%', positive: 38, negative: 39, event: '실적·인도량', freshness: 'mock', tone: 'down' },
  { rank: 2, name: 'NVIDIA', symbol: 'NVDA', market: 'NASDAQ', price: '$924.80', change: '+1.85%', volume: '51.7M', volumeDelta: '+31%', positive: 68, negative: 15, event: 'AI 수요', freshness: 'mock', tone: 'up' },
  { rank: 3, name: 'SoFi', symbol: 'SOFI', market: 'NASDAQ', price: '$9.42', change: '+3.10%', volume: '48.2M', volumeDelta: '+21%', positive: 49, negative: 28, event: '핀테크 관심', freshness: 'mock', tone: 'up' },
  { rank: 4, name: 'Palantir', symbol: 'PLTR', market: 'NYSE', price: '$21.80', change: '+2.70%', volume: '36.4M', volumeDelta: '+26%', positive: 57, negative: 22, event: 'AI 계약', freshness: 'mock', tone: 'up' },
  { rank: 5, name: 'AMD', symbol: 'AMD', market: 'NASDAQ', price: '$162.31', change: '+0.92%', volume: '32.8M', volumeDelta: '+14%', positive: 46, negative: 27, event: 'GPU 경쟁', freshness: 'mock', tone: 'up' },
  { rank: 6, name: 'Apple', symbol: 'AAPL', market: 'NASDAQ', price: '$190.20', change: '-0.30%', volume: '29.7M', volumeDelta: '+7%', positive: 35, negative: 36, event: 'AI 발표 대기', freshness: 'mock', tone: 'down' },
  { rank: 7, name: 'SOXS', symbol: 'SOXS', market: 'ETF', price: '$24.12', change: '+1.60%', volume: '24.5M', volumeDelta: '+13%', positive: 31, negative: 45, event: '반도체 변동성', freshness: 'mock', tone: 'up' },
  { rank: 8, name: 'MSFU', symbol: 'MSFU', market: 'ETF', price: '$43.62', change: '+6.09%', volume: '18.2M', volumeDelta: '+19%', positive: 52, negative: 26, event: '레버리지 ETF', freshness: 'mock', tone: 'up' },
  { rank: 9, name: 'TSMC', symbol: 'TSM', market: 'NYSE', price: '$151.20', change: '+0.68%', volume: '15.4M', volumeDelta: '+10%', positive: 48, negative: 22, event: '파운드리 수요', freshness: 'mock', tone: 'up' },
  { rank: 10, name: 'NuScale', symbol: 'SMR', market: 'NYSE', price: '$6.84', change: '-2.40%', volume: '13.9M', volumeDelta: '+18%', positive: 24, negative: 55, event: '원전 변동성', freshness: 'mock', tone: 'down' }
];

const rankingGroups = [
  {
    id: 'domestic',
    title: '국장 거래량 TOP 10',
    caption: 'KRX · ETF 포함',
    rows: domesticRows
  },
  {
    id: 'overseas',
    title: '해외 거래량 TOP 10',
    caption: 'NASDAQ · NYSE · ETF 포함',
    rows: overseasRows
  }
];

const filters = ['거래량 급증', '언급 증가', '가격 괴리', '부정 증가', '원문 링크 있음', 'stale 제외'];

const rankSummary = [
  { label: '정렬 기준', value: '거래량', meta: 'mock volume' },
  { label: '국장 표시', value: '10종목', meta: 'KRX·ETF' },
  { label: '해외 표시', value: '10종목', meta: 'US·ETF' },
  { label: '보조 지표', value: '반응', meta: '긍정/부정·이벤트' }
];

const hotThemes = [
  { theme: '반도체', count: 11, heat: 92 },
  { theme: '2차전지', count: 8, heat: 76 },
  { theme: '로봇', count: 6, heat: 68 },
  { theme: '미국주식', count: 10, heat: 81 }
];
</script>

<template>
  <section class="surface-page stocks-page">
    <section class="stock-board-shell">
      <div class="stock-board-top">
        <div>
          <p class="label">stock screener</p>
          <h2>종목 거래량 순위</h2>
          <span>국장과 해외를 나눠 보고, 반응 변화는 보조로 확인합니다.</span>
        </div>
        <div class="stock-board-search">
          <span aria-hidden="true">⌕</span>
          <strong>종목명·티커·키워드 검색</strong>
          <em>목록에서 종목을 눌러 상세로 이동</em>
        </div>
      </div>

      <div class="stock-filter-strip" aria-label="종목 필터">
        <button v-for="filter in filters" :key="filter" type="button">{{ filter }}</button>
      </div>

      <div class="rank-summary-strip" aria-label="랭킹 요약">
        <article v-for="item in rankSummary" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <em>{{ item.meta }}</em>
        </article>
      </div>

      <div class="market-ranking-grid" aria-label="국장과 해외 거래량 순위">
        <section
          v-for="group in rankingGroups"
          :key="group.id"
          class="stock-screener-table market-ranking-card"
          :aria-label="group.title"
        >
          <div class="market-ranking-title">
            <div>
              <p class="label">{{ group.caption }}</p>
              <h3>{{ group.title }}</h3>
            </div>
            <span class="status-pill subtle">거래량순 mock</span>
          </div>

          <div class="market-ranking-head">
            <span>순위</span>
            <span>종목</span>
            <span>거래량</span>
            <span>반응</span>
            <span>이벤트</span>
          </div>

          <RouterLink
            v-for="row in group.rows"
            :key="row.symbol"
            class="stock-screener-row market-ranking-row"
            :to="`/stocks/${row.symbol}`"
          >
            <b>{{ row.rank }}</b>
            <div>
              <strong>{{ row.name }}</strong>
              <small>{{ row.symbol }} · {{ row.market }} · {{ row.price }} <em :class="row.tone">{{ row.change }}</em></small>
            </div>
            <div>
              <strong>{{ row.volume }}</strong>
              <em>{{ row.volumeDelta }}</em>
            </div>
            <div class="stock-mini-ratio">
              <span>{{ row.positive }}</span>
              <i>
                <mark :style="{ width: `${row.positive}%` }"></mark>
                <mark class="down" :style="{ width: `${row.negative}%` }"></mark>
              </i>
              <span>{{ row.negative }}</span>
            </div>
            <div>
              <span>{{ row.event }}</span>
              <small>{{ row.freshness }}</small>
            </div>
          </RouterLink>
        </section>
      </div>

      <aside class="stock-side-console market-ranking-console" aria-label="랭킹 보조 지표">
        <section>
          <p class="label">theme heat</p>
          <h3>급증 테마</h3>
          <article v-for="theme in hotThemes" :key="theme.theme">
            <strong>{{ theme.theme }}</strong>
            <span>{{ theme.count }}종목</span>
            <i><mark :style="{ width: `${theme.heat}%` }"></mark></i>
          </article>
        </section>
        <section>
          <p class="label">data clock</p>
          <h3>데이터 기준</h3>
          <div class="clock-grid">
            <span>수집</span><strong>10:05</strong>
            <span>가격</span><strong>15분 지연</strong>
            <span>거래량</span><strong>mock</strong>
            <span>상태</span><strong>demo</strong>
          </div>
        </section>
      </aside>
    </section>
  </section>
</template>
