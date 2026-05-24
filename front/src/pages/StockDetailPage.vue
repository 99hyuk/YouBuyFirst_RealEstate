<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import StockPriceChart from '../components/StockPriceChart.vue';
import quoteSnapshotFixtureSet from '../fixtures/quote-snapshots.json';
import type { StockChartCandle } from '../fixtures/stock-detail-chart';
import { stockChartFixtures } from '../fixtures/stock-detail-chart';
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

type StockCatalogItem = {
  symbol: string;
  apiSymbol: string;
  name: string;
  market: string;
  providerSymbol: string;
};

type ApiQuoteSnapshot = {
  symbol: string;
  name: string;
  market: string;
  currency: 'KRW' | 'USD';
  price: number;
  change: number;
  changePct: number;
  volume: number;
  asOf: string;
  provider: string;
  delayLabel: string;
  stale: boolean;
  dataStatus: string;
};

type ApiChartCandleBar = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

type ApiChartCandles = {
  symbol: string;
  name: string;
  market: string;
  currency: 'KRW' | 'USD';
  range: string;
  interval: string;
  provider: string;
  delayLabel: string;
  asOf: string;
  stale: boolean;
  dataStatus: string;
  bars: ApiChartCandleBar[];
  displayPolicy: {
    displayOnly: boolean;
    rawMinute: boolean;
    downloadable: boolean;
    maxBars: number;
  };
};

type ApiTechnicalIndicators = {
  symbol: string;
  provider: string;
  sourceProvider: string;
  asOf: string;
  stale: boolean;
  dataStatus: string;
  rsi: {
    period: number;
    points: { date: string; value: number | null }[];
  };
  bollingerBands: {
    period: number;
    multiplier: number;
    points: { date: string; upper: number | null; middle: number | null; lower: number | null }[];
  };
};

type ApiInvestorFlowLeg = {
  netAmount: number | null;
  netVolume: number;
  derived: boolean;
};

type ApiInvestorFlowSnapshot = {
  symbol: string;
  name: string;
  market: string;
  currency: 'KRW' | 'USD';
  tradeDate: string;
  provider: string;
  sourceLabel: string;
  delayLabel: string;
  asOf: string;
  stale: boolean;
  dataStatus: string;
  individual: ApiInvestorFlowLeg;
  foreign: ApiInvestorFlowLeg;
  institution: ApiInvestorFlowLeg;
};

type QuoteDisplay = {
  symbol: string;
  price: string;
  change: string;
  changeTone: 'up' | 'down';
  volume: string;
  asOf: string;
  provider: string;
  delayLabel: string;
  stale: boolean;
  dataStatus: string;
};

const route = useRoute();
const stockFixtures = stockDetailFixtureSet.items as StockDetailFixture[];
const quoteSnapshots = ref<ApiQuoteSnapshot[]>(quoteSnapshotFixtureSet.items as ApiQuoteSnapshot[]);
const quoteLoadState = ref<'fixture' | 'api' | 'error'>('fixture');
const chartCandles = ref<ApiChartCandles | null>(null);
const technicalIndicators = ref<ApiTechnicalIndicators | null>(null);
const chartLoadState = ref<'idle' | 'loading' | 'api' | 'hidden' | 'error'>('idle');
const chartBlockReason = ref('차트 API 응답을 기다리고 있습니다.');
const investorFlows = ref<ApiInvestorFlowSnapshot[]>([]);
const investorFlowLoadState = ref<'idle' | 'loading' | 'api' | 'hidden' | 'error'>('idle');
const isTestMode = typeof window !== 'undefined' && window.navigator.userAgent.includes('jsdom');
const quoteApiBaseUrl = '';
const hiddenChartStatuses = new Set(['INSUFFICIENT', 'PROVIDER_ERROR', 'MOCK']);
const visibleInvestorFlowStatuses = new Set(['OK', 'STALE']);

const stockCatalog: StockCatalogItem[] = [
  { symbol: '005930', apiSymbol: '005930.KS', name: 'Samsung Electronics', market: 'KRX', providerSymbol: 'KRX:005930' },
  { symbol: '000660', apiSymbol: '000660.KS', name: 'SK hynix', market: 'KRX', providerSymbol: 'KRX:000660' },
  { symbol: '069500', apiSymbol: '069500.KS', name: 'KODEX 200', market: 'ETF', providerSymbol: 'KRX:069500' },
  { symbol: '454910', apiSymbol: '454910.KS', name: 'Doosan Robotics', market: 'KRX', providerSymbol: 'KRX:454910' },
  { symbol: '035420', apiSymbol: '035420.KS', name: 'NAVER', market: 'KRX', providerSymbol: 'KRX:035420' },
  { symbol: '086520', apiSymbol: '086520.KQ', name: 'Ecopro', market: 'KOSDAQ', providerSymbol: 'KOSDAQ:086520' },
  { symbol: '042700', apiSymbol: '042700.KS', name: 'Hanmi Semiconductor', market: 'KRX', providerSymbol: 'KRX:042700' },
  { symbol: '066570', apiSymbol: '066570.KS', name: 'LG Electronics', market: 'KRX', providerSymbol: 'KRX:066570' },
  { symbol: '005380', apiSymbol: '005380.KS', name: 'Hyundai Motor', market: 'KRX', providerSymbol: 'KRX:005380' },
  { symbol: '006400', apiSymbol: '006400.KS', name: 'Samsung SDI', market: 'KRX', providerSymbol: 'KRX:006400' },
  { symbol: 'TSLA', apiSymbol: 'TSLA', name: 'Tesla', market: 'NASDAQ', providerSymbol: 'NASDAQ:TSLA' },
  { symbol: 'NVDA', apiSymbol: 'NVDA', name: 'NVIDIA', market: 'NASDAQ', providerSymbol: 'NASDAQ:NVDA' },
  { symbol: 'SOFI', apiSymbol: 'SOFI', name: 'SoFi Technologies', market: 'NASDAQ', providerSymbol: 'NASDAQ:SOFI' },
  { symbol: 'PLTR', apiSymbol: 'PLTR', name: 'Palantir', market: 'NYSE', providerSymbol: 'NYSE:PLTR' },
  { symbol: 'AMD', apiSymbol: 'AMD', name: 'Advanced Micro Devices', market: 'NASDAQ', providerSymbol: 'NASDAQ:AMD' },
  { symbol: 'AAPL', apiSymbol: 'AAPL', name: 'Apple', market: 'NASDAQ', providerSymbol: 'NASDAQ:AAPL' },
  { symbol: 'SOXS', apiSymbol: 'SOXS', name: 'SOXS', market: 'ETF', providerSymbol: 'NYSE:SOXS' },
  { symbol: 'MSFU', apiSymbol: 'MSFU', name: 'MSFU', market: 'ETF', providerSymbol: 'NASDAQ:MSFU' },
  { symbol: 'TSM', apiSymbol: 'TSM', name: 'Taiwan Semiconductor Manufacturing', market: 'NYSE', providerSymbol: 'NYSE:TSM' },
  { symbol: 'SMR', apiSymbol: 'SMR', name: 'NuScale Power', market: 'NYSE', providerSymbol: 'NYSE:SMR' },
  { symbol: 'MSFT', apiSymbol: 'MSFT', name: 'Microsoft', market: 'NASDAQ', providerSymbol: 'NASDAQ:MSFT' },
  { symbol: 'AMZN', apiSymbol: 'AMZN', name: 'Amazon', market: 'NASDAQ', providerSymbol: 'NASDAQ:AMZN' },
  { symbol: 'GOOGL', apiSymbol: 'GOOGL', name: 'Alphabet', market: 'NASDAQ', providerSymbol: 'NASDAQ:GOOGL' },
  { symbol: 'META', apiSymbol: 'META', name: 'Meta Platforms', market: 'NASDAQ', providerSymbol: 'NASDAQ:META' },
  { symbol: 'QQQ', apiSymbol: 'QQQ', name: 'Invesco QQQ Trust', market: 'ETF', providerSymbol: 'NASDAQ:QQQ' },
  { symbol: 'SPY', apiSymbol: 'SPY', name: 'SPDR S&P 500 ETF Trust', market: 'ETF', providerSymbol: 'NYSE:SPY' }
];

const routeSymbol = computed(() => String(route.params.symbol ?? stockFixtures[0].symbol).toUpperCase());
const quoteApiSymbolFor = (item: StockDetailFixture) =>
  item.providerSymbol.startsWith('KOSDAQ:') && /^\d{6}$/.test(item.symbol)
    ? `${item.symbol}.KQ`
    : (item.providerSymbol.startsWith('KRX:') || item.market === 'KRX') && /^\d{6}$/.test(item.symbol)
      ? `${item.symbol}.KS`
      : item.symbol;
const matchingCatalogItem = computed(() =>
  stockCatalog.find(
    (item) =>
      item.symbol.toUpperCase() === routeSymbol.value.replace(/\.(KS|KQ)$/, '') ||
      item.apiSymbol.toUpperCase() === routeSymbol.value ||
      item.providerSymbol.toUpperCase() === routeSymbol.value
  )
);
const fallbackStockFor = (item: StockCatalogItem): StockDetailFixture => {
  const template = item.apiSymbol.endsWith('.KS') || item.apiSymbol.endsWith('.KQ') ? stockFixtures[0] : (stockFixtures[1] ?? stockFixtures[0]);

  return {
    ...template,
    symbol: item.symbol,
    name: item.name,
    market: item.market,
    provider: 'Yahoo Finance',
    providerSymbol: item.providerSymbol,
    quoteSnapshot: {
      ...template.quoteSnapshot,
      price: '-',
      change: '0.00%',
      changeTone: 'up',
      volume: '-',
      asOf: 'chart-candles on demand',
      stale: true,
      dataStatus: 'api-pending',
      latencyLabel: 'provider delayed'
    },
    brief: {
      ...template.brief,
      headline: `${item.name} price reaction check`,
      summary: `${item.apiSymbol} chart-candles API, quote snapshot, community reaction, and investor-flow slices are loaded separately.`,
      scoreLine: 'Reference-only market display. Not an investment signal.',
      riskNote: 'Provider-delayed observation data. Not advice.'
    }
  };
};
const stock = computed(
  () =>
    stockFixtures.find(
      (item) =>
        item.symbol.toUpperCase() === routeSymbol.value.replace(/\.KS$/, '') ||
        item.providerSymbol.toUpperCase() === routeSymbol.value ||
        quoteApiSymbolFor(item).toUpperCase() === routeSymbol.value
    ) ?? (matchingCatalogItem.value ? fallbackStockFor(matchingCatalogItem.value) : stockFixtures[0])
);
const quoteApiSymbol = computed(() => matchingCatalogItem.value?.apiSymbol ?? quoteApiSymbolFor(stock.value));
const quoteRequestSymbols = computed(() => Array.from(new Set(['005930.KS', '000660.KS', '069500.KS', 'AAPL', 'NVDA', 'TSLA', 'MSFT', quoteApiSymbol.value])));
const quoteApiUrl = computed(() => `${quoteApiBaseUrl}/api/quotes?symbols=${quoteRequestSymbols.value.join(',')}`);
const chartApiRequestUrl = computed(() => `/api/market/chart-candles?symbol=${quoteApiSymbol.value}&range=5Y&interval=1d`);
const technicalIndicatorApiRequestUrl = computed(
  () => `/api/market/technical-indicators?symbol=${quoteApiSymbol.value}&range=5Y&interval=1d&rsiPeriod=14&bollingerPeriod=20&bollingerMultiplier=2`
);
const investorFlowApiRequestUrl = computed(
  () => `/api/market/investor-flows/history?symbol=${encodeURIComponent(quoteApiSymbol.value)}&limit=20`
);
const apiQuoteSnapshot = computed(() =>
  quoteSnapshots.value.find((quote) => quote.symbol.toUpperCase() === quoteApiSymbol.value.toUpperCase())
);
const isDomesticInvestorFlowTarget = computed(() => quoteApiSymbol.value.toUpperCase().endsWith('.KS') || stock.value.market === 'KRX');
const topBrief = computed(() => stock.value.brief);
const chartFixture = computed(
  () =>
    stockChartFixtures.find(
      (item) =>
        item.symbol.toUpperCase() === stock.value.symbol.toUpperCase() ||
        item.providerSymbol.toUpperCase() === stock.value.providerSymbol.toUpperCase()
    ) ?? {
      ...stockChartFixtures[0],
      symbol: stock.value.symbol,
      providerSymbol: stock.value.providerSymbol,
      currency: quoteApiSymbol.value.endsWith('.KS') || quoteApiSymbol.value.endsWith('.KQ') ? 'KRW' : 'USD',
      priceUnit: quoteApiSymbol.value.endsWith('.KS') || quoteApiSymbol.value.endsWith('.KQ') ? '원' : '달러',
      flowUnit: quoteApiSymbol.value.endsWith('.KS') || quoteApiSymbol.value.endsWith('.KQ') ? '억원' : '백만달러',
      chartSource: 'market chart-candles API pending'
    }
);

const formatCurrency = (value: number, currency: ApiQuoteSnapshot['currency']) =>
  currency === 'KRW'
    ? `${Math.round(value).toLocaleString('ko-KR')}원`
    : `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const formatSignedCurrency = (value: number, currency: ApiQuoteSnapshot['currency']) => {
  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  return `${sign}${formatCurrency(Math.abs(value), currency)}`;
};

const formatVolume = (value: number) => {
  if (value >= 100000000) return `${(value / 100000000).toFixed(1)}억주`;
  if (value >= 10000) return `${(value / 10000).toFixed(1)}만주`;
  return `${value.toLocaleString('ko-KR')}주`;
};

const formatSignedNumber = (value: number) => {
  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  return `${sign}${Math.abs(value).toLocaleString('ko-KR')}`;
};

const formatSignedPct = (value: number) => `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;

const formatNetAmount = (value: number | null, currency: ApiInvestorFlowSnapshot['currency']) => {
  if (value === null) return '-';

  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  const absolute = Math.abs(value);

  if (currency === 'KRW') {
    if (absolute >= 1000000000000) return `${sign}${(absolute / 1000000000000).toFixed(2)}조원`;
    if (absolute >= 100000000) return `${sign}${(absolute / 100000000).toLocaleString('ko-KR', { maximumFractionDigits: 1 })}억원`;
    if (absolute >= 10000) return `${sign}${(absolute / 10000).toLocaleString('ko-KR', { maximumFractionDigits: 1 })}만원`;
    return `${sign}${absolute.toLocaleString('ko-KR')}원`;
  }

  return formatSignedCurrency(value, currency);
};

const flowTone = (value: number) => {
  if (value > 0) return 'up';
  if (value < 0) return 'down';
  return 'flat';
};

const formatAsOf = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'Asia/Seoul'
  }).format(date);
};

const quoteSnapshot = computed<QuoteDisplay>(() => {
  const apiQuote = apiQuoteSnapshot.value;
  if (apiQuote) {
    const isLiveApi = quoteLoadState.value === 'api';

    return {
      symbol: apiQuote.symbol,
      price: formatCurrency(apiQuote.price, apiQuote.currency),
      change: `${formatSignedCurrency(apiQuote.change, apiQuote.currency)} (${apiQuote.changePct >= 0 ? '+' : ''}${apiQuote.changePct.toFixed(2)}%)`,
      changeTone: apiQuote.change >= 0 ? 'up' : 'down',
      volume: formatVolume(apiQuote.volume),
      asOf: formatAsOf(apiQuote.asOf),
      provider: isLiveApi ? apiQuote.provider : 'front mock fixture',
      delayLabel: isLiveApi ? apiQuote.delayLabel : 'quote API 미연결 · mock fixture',
      stale: isLiveApi ? apiQuote.stale : true,
      dataStatus: isLiveApi ? apiQuote.dataStatus : 'MOCK'
    };
  }

  return {
    symbol: quoteApiSymbol.value,
    price: stock.value.quoteSnapshot.price,
    change: stock.value.quoteSnapshot.change,
    changeTone: stock.value.quoteSnapshot.changeTone,
    volume: stock.value.quoteSnapshot.volume,
    asOf: stock.value.quoteSnapshot.asOf,
    provider: `${stock.value.provider} mock fixture`,
    delayLabel: 'quote API 미연결 · mock fixture',
    stale: true,
    dataStatus: 'MOCK'
  };
});

const topBriefMetrics = computed(() => [
  { label: '시황 점수', value: topBrief.value.score, meta: topBrief.value.scoreMeta },
  { label: '등락률', value: quoteSnapshot.value.change, meta: quoteSnapshot.value.price },
  { label: '거래량', value: quoteSnapshot.value.volume, meta: quoteSnapshot.value.dataStatus },
  { label: '시세 기준', value: quoteSnapshot.value.asOf, meta: quoteSnapshot.value.delayLabel }
]);

const topBriefReasons = computed(() => topBrief.value.reasons);

const requiredChartFields = [
  'symbol',
  'currency',
  'interval',
  'range',
  'bars[].date',
  'bars[].open/high/low/close',
  'bars[].volume',
  'asOf',
  'provider',
  'delayLabel',
  'stale',
  'dataStatus'
];

const normalizedChartStatus = computed(() => chartCandles.value?.dataStatus?.toUpperCase() ?? '');
const canRenderChart = computed(() => {
  const payload = chartCandles.value;
  if (chartLoadState.value !== 'api' || !payload?.bars?.length) return false;
  return !hiddenChartStatuses.has(normalizedChartStatus.value);
});
const chartDisplayCandles = computed<StockChartCandle[]>(() =>
  (chartCandles.value?.bars ?? []).map((bar) => ({
    time: bar.date,
    open: bar.open,
    high: bar.high,
    low: bar.low,
    close: bar.close,
    volume: bar.volume,
    individual: 0,
    foreign: 0,
    institution: 0
  }))
);
const isWeekendDate = (value: string) => {
  const day = new Date(`${value}T00:00:00`).getDay();
  return day === 0 || day === 6;
};
const chartCalendarWarning = computed(() => {
  const payload = chartCandles.value;
  if (!payload || !isDomesticInvestorFlowTarget.value) return '';

  const weekendBars = payload.bars.filter((bar) => isWeekendDate(bar.date));
  const barDates = new Set(payload.bars.map((bar) => bar.date));
  const missingFlowDates = investorFlowSnapshots.value
    .filter((snapshot) => !barDates.has(snapshot.tradeDate))
    .slice(0, 3)
    .map((snapshot) => snapshot.tradeDate.slice(5));

  if (!weekendBars.length && !missingFlowDates.length) return '';

  const issueParts = [];
  if (weekendBars.length) issueParts.push(`비거래일 bar ${weekendBars.length}개`);
  if (missingFlowDates.length) issueParts.push(`수급 날짜 미매칭 ${missingFlowDates.join(', ')}`);
  return `국장 차트 날짜 정합성 확인 필요: ${issueParts.join(' · ')}. 차트 API 날짜를 KRX 거래일 기준으로 보정하기 전까지 수급 표의 가격 칸은 같은 날짜만 붙입니다.`;
});
const chartStatusLabel = computed(() => {
  const payload = chartCandles.value;
  if (!payload) return chartLoadState.value === 'loading' ? 'chart API 확인 중' : 'chart API 대기';
  return `${payload.dataStatus} · ${payload.stale ? 'stale' : 'fresh'}`;
});
const chartMetadataItems = computed(() => {
  const payload = chartCandles.value;
  if (!payload) return [];

  return [
    { label: 'provider', value: payload.provider },
    { label: 'delay', value: payload.delayLabel },
    { label: 'asOf', value: formatAsOf(payload.asOf) },
    { label: 'status', value: chartStatusLabel.value }
  ];
});
const chartSourceLabel = computed(() => {
  const payload = chartCandles.value;
  if (!payload) return chartFixture.value.chartSource;
  return `${payload.provider} · ${payload.delayLabel}`;
});
const chartPriceUnit = computed(() => (chartCandles.value?.currency === 'USD' ? '달러' : '원'));
const chartBlockTitle = computed(() => {
  if (chartLoadState.value === 'loading') return `${chartFixture.value.providerSymbol} 차트 API 확인 중`;
  if (chartLoadState.value === 'hidden') return '차트 응답이 표시 조건을 만족하지 않습니다';
  if (chartLoadState.value === 'error') return '실제 차트 API가 아직 연결되지 않았습니다';
  return `실제 ${chartFixture.value.providerSymbol} 일자별 차트 API가 필요합니다`;
});
const investorFlowSnapshots = computed(() =>
  investorFlows.value
    .filter((item) => item.symbol.toUpperCase() === quoteApiSymbol.value.toUpperCase())
    .filter((item) => visibleInvestorFlowStatuses.has(item.dataStatus.toUpperCase()))
    .sort((first, second) => second.tradeDate.localeCompare(first.tradeDate))
);
const latestInvestorFlow = computed(() => investorFlowSnapshots.value[0] ?? null);
const canRenderInvestorFlow = computed(
  () => investorFlowLoadState.value === 'api' && isDomesticInvestorFlowTarget.value && investorFlowSnapshots.value.length > 0
);
const canShowInvestorFlowPanel = computed(() => isDomesticInvestorFlowTarget.value && investorFlowLoadState.value !== 'idle');
const chartPanelTitle = computed(() => (isDomesticInvestorFlowTarget.value ? '가격 차트와 일별 수급' : '가격 차트'));
const investorFlowStatusLabel = computed(() => {
  const payload = latestInvestorFlow.value;
  if (!payload) return investorFlowLoadState.value === 'loading' ? '수급 API 확인 중' : '수급 API 대기';
  return `${payload.dataStatus} · ${payload.stale ? 'stale' : 'fresh'}`;
});
const investorFlowEmptyMessage = computed(() => {
  if (investorFlowLoadState.value === 'loading') return '수급 history API를 확인하고 있습니다.';
  if (investorFlowLoadState.value === 'error') return '수급 history API 응답을 확인할 수 없습니다. 차트와 가격 영역은 그대로 볼 수 있습니다.';
  return '표시 가능한 OK/STALE 수급 row가 아직 없습니다. 실패/부족/mock 값은 0 수급처럼 보이지 않게 숨깁니다.';
});
const investorFlowMetaItems = computed(() => {
  const payload = latestInvestorFlow.value;
  if (!payload) return [];

  return [
    { label: '최근 거래일', value: payload.tradeDate },
    { label: 'provider', value: payload.provider },
    { label: 'delay', value: payload.delayLabel },
    { label: 'asOf', value: formatAsOf(payload.asOf) },
    { label: 'status', value: investorFlowStatusLabel.value }
  ];
});
const investorFlowSubjectLabels = computed(() => {
  const payload = latestInvestorFlow.value;
  const labelFor = (label: string, leg?: ApiInvestorFlowLeg) => (leg?.derived ? `${label}(잔차)` : label);

  return {
    individual: labelFor('개인', payload?.individual),
    foreign: labelFor('외국인', payload?.foreign),
    institution: labelFor('기관', payload?.institution)
  };
});
const investorFlowTableRows = computed(() => {
  const bars = chartCandles.value?.bars ?? [];

  return investorFlowSnapshots.value.map((snapshot) => {
    const barIndex = bars.findIndex((bar) => bar.date === snapshot.tradeDate);
    const bar = barIndex >= 0 ? bars[barIndex] : null;
    const previousBar = barIndex > 0 ? bars[barIndex - 1] : null;
    const priceChange = bar && previousBar ? bar.close - previousBar.close : null;
    const priceChangePct = priceChange !== null && previousBar?.close ? (priceChange / previousBar.close) * 100 : null;

    const flowCell = (leg: ApiInvestorFlowLeg) => ({
      volumeLabel: formatSignedNumber(leg.netVolume),
      amountLabel: formatNetAmount(leg.netAmount, snapshot.currency),
      derived: leg.derived,
      title: `${leg.derived ? '잔차 계산값' : '관찰값'} · 금액 ${formatNetAmount(leg.netAmount, snapshot.currency)}`,
      tone: flowTone(leg.netVolume || leg.netAmount || 0)
    });

    return {
      key: `${snapshot.symbol}-${snapshot.tradeDate}`,
      dateLabel: snapshot.tradeDate.slice(5),
      closeLabel: bar ? formatCurrency(bar.close, snapshot.currency) : '-',
      changeLabel: priceChange === null ? '-' : formatSignedCurrency(priceChange, snapshot.currency),
      changePctLabel: priceChangePct === null ? '-' : formatSignedPct(priceChangePct),
      changeTone: flowTone(priceChange ?? 0),
      volumeLabel: bar ? formatVolume(bar.volume) : '-',
      individual: flowCell(snapshot.individual),
      foreign: flowCell(snapshot.foreign),
      institution: flowCell(snapshot.institution)
    };
  });
});

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

const loadQuoteSnapshots = async () => {
  if (isTestMode) {
    return;
  }

  try {
    const response = await fetch(quoteApiUrl.value, {
      headers: { Accept: 'application/json' }
    });
    if (!response.ok) {
      throw new Error(`quote snapshot request failed: ${response.status}`);
    }

    const contentType = response.headers.get('content-type') ?? '';
    if (!contentType.includes('application/json')) {
      throw new Error('quote snapshot response is not JSON');
    }

    const payload = (await response.json()) as ApiQuoteSnapshot[] | { items?: ApiQuoteSnapshot[] };
    const items = Array.isArray(payload) ? payload : payload.items;

    if (!items?.length) {
      throw new Error('quote snapshot payload is empty');
    }

    quoteSnapshots.value = items;
    quoteLoadState.value = 'api';
  } catch {
    quoteLoadState.value = 'error';
  }
};

const loadChartCandles = async () => {
  if (isTestMode) {
    return;
  }

  chartLoadState.value = 'loading';
  chartBlockReason.value = '실제 일자별 캔들 API를 호출하고 있습니다.';

  try {
    const response = await fetch(chartApiRequestUrl.value, {
      headers: { Accept: 'application/json' }
    });
    if (!response.ok) {
      throw new Error(`chart candles request failed: ${response.status}`);
    }

    const contentType = response.headers.get('content-type') ?? '';
    if (!contentType.includes('application/json')) {
      throw new Error('chart candles response is not JSON');
    }

    const payload = (await response.json()) as ApiChartCandles;
    chartCandles.value = payload;

    if (!payload.bars?.length) {
      chartLoadState.value = 'hidden';
      chartBlockReason.value = 'bars가 비어 있어 차트를 표시하지 않습니다.';
      return;
    }

    if (hiddenChartStatuses.has(payload.dataStatus.toUpperCase())) {
      chartLoadState.value = 'hidden';
      chartBlockReason.value = `dataStatus=${payload.dataStatus} 상태라 차트를 표시하지 않습니다.`;
      return;
    }

    chartLoadState.value = 'api';
  } catch {
    chartCandles.value = null;
    chartLoadState.value = 'error';
    chartBlockReason.value = '현재 브랜치의 backend에는 chart-candles public endpoint가 아직 없거나 응답이 실패했습니다.';
  }
};

const loadTechnicalIndicators = async () => {
  technicalIndicators.value = null;

  if (isTestMode) {
    return;
  }

  try {
    const response = await fetch(technicalIndicatorApiRequestUrl.value, {
      headers: { Accept: 'application/json' }
    });
    if (!response.ok) {
      throw new Error(`technical indicators request failed: ${response.status}`);
    }

    const contentType = response.headers.get('content-type') ?? '';
    if (!contentType.includes('application/json')) {
      throw new Error('technical indicators response is not JSON');
    }

    const payload = (await response.json()) as ApiTechnicalIndicators;
    if (payload.symbol.toUpperCase() === quoteApiSymbol.value.toUpperCase() && payload.dataStatus.toUpperCase() !== 'INSUFFICIENT') {
      technicalIndicators.value = payload;
    }
  } catch {
    technicalIndicators.value = null;
  }
};

const loadInvestorFlows = async () => {
  investorFlows.value = [];

  if (isTestMode) {
    return;
  }

  if (!isDomesticInvestorFlowTarget.value) {
    investorFlowLoadState.value = 'hidden';
    return;
  }

  investorFlowLoadState.value = 'loading';

  try {
    const response = await fetch(investorFlowApiRequestUrl.value, {
      headers: { Accept: 'application/json' }
    });
    if (!response.ok) {
      throw new Error(`investor flow request failed: ${response.status}`);
    }

    const contentType = response.headers.get('content-type') ?? '';
    if (!contentType.includes('application/json')) {
      throw new Error('investor flow response is not JSON');
    }

    const payload = (await response.json()) as ApiInvestorFlowSnapshot[] | { items?: ApiInvestorFlowSnapshot[] };
    const items = Array.isArray(payload) ? payload : payload.items;
    const snapshots =
      items?.filter(
        (item) =>
          item.symbol.toUpperCase() === quoteApiSymbol.value.toUpperCase() &&
          visibleInvestorFlowStatuses.has(item.dataStatus.toUpperCase())
      ) ?? [];

    if (!snapshots.length) {
      investorFlowLoadState.value = 'hidden';
      return;
    }

    investorFlows.value = snapshots;
    investorFlowLoadState.value = 'api';
  } catch {
    investorFlows.value = [];
    investorFlowLoadState.value = 'error';
  }
};

const loadMarketSlices = () => {
  void loadQuoteSnapshots();
  void loadChartCandles();
  void loadTechnicalIndicators();
  void loadInvestorFlows();
};

onMounted(() => {
  loadMarketSlices();
});

watch(quoteApiSymbol, () => {
  loadMarketSlices();
});
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
        <div class="quote-primary-card">
          <span>quote snapshot · 현재가</span>
          <strong>{{ quoteSnapshot.price }}</strong>
          <em :class="quoteSnapshot.changeTone">{{ quoteSnapshot.change }}</em>
          <div class="quote-meta-list" aria-label="quote snapshot metadata">
            <small>{{ quoteSnapshot.asOf }}</small>
            <small>{{ quoteSnapshot.provider }}</small>
            <small>{{ quoteSnapshot.delayLabel }}</small>
            <small :class="quoteSnapshot.stale ? 'warn' : 'ok'">{{ quoteSnapshot.dataStatus }} · {{ quoteSnapshot.stale ? 'stale' : 'fresh' }}</small>
          </div>
        </div>
        <div>
          <span>거래량</span>
          <strong>{{ quoteSnapshot.volume }}</strong>
          <em>{{ quoteSnapshot.dataStatus }}</em>
        </div>
        <div>
          <span>데이터 상태</span>
          <strong>{{ quoteSnapshot.symbol }}</strong>
          <em :class="quoteLoadState === 'api' ? 'ok' : 'warn'">
            {{ quoteLoadState === 'api' ? 'API 연결' : quoteLoadState === 'error' ? 'API 미연결' : 'fixture 준비' }}
          </em>
        </div>
      </div>
    </section>

    <section class="stock-main-chart panel content-feed-card surface-data-card" :aria-label="`종목 ${chartPanelTitle}`">
      <div class="panel-header">
        <div>
          <p class="label">chart lab</p>
          <h3>{{ chartPanelTitle }}</h3>
        </div>
        <span class="status-pill subtle">{{ canRenderChart ? 'chart API 연결' : '실제 차트 API 대기' }}</span>
      </div>

      <div v-if="chartCandles" class="chart-source-meta-grid" aria-label="chart candle metadata">
        <article v-for="item in chartMetadataItems" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </div>

      <p v-if="chartCalendarWarning" class="chart-data-warning" role="note">
        {{ chartCalendarWarning }}
      </p>

      <StockPriceChart
        v-if="canRenderChart && chartCandles"
        :title="chartCandles.name || stock.name"
        :provider-symbol="chartCandles.symbol"
        :currency="chartCandles.currency"
        :price-unit="chartPriceUnit"
        volume-unit="주"
        :flow-unit="chartFixture.flowUnit"
        :chart-source="chartSourceLabel"
        :candles="chartDisplayCandles"
        :snapshot-as-of="chartCandles.asOf"
        :snapshot-status="chartStatusLabel"
        data-mode="actual"
        :show-flow-summary="false"
        :technical-indicators="technicalIndicators"
      />

      <div v-else class="chart-api-blocker" role="note" aria-label="실제 차트 API 요청">
        <div class="chart-api-blocker-copy">
          <p class="label">actual chart blocked</p>
          <h4>{{ chartBlockTitle }}</h4>
          <p>
            현재 연결된 <code>/api/quotes</code>는 현재가 snapshot만 내려줍니다. 메인 차트는 <code>/api/market/chart-candles</code>가 유효한 bars를 줄 때만 표시합니다. {{ chartBlockReason }}
          </p>
        </div>
        <div class="chart-api-request-grid">
          <article>
            <span>현재 API</span>
            <strong>/api/quotes</strong>
            <em>현재가·등락률·거래량 snapshot only</em>
          </article>
          <article>
            <span>요청 API</span>
            <strong>{{ chartApiRequestUrl }}</strong>
            <em>일/주/월 OHLC + volume display bars</em>
          </article>
          <article>
            <span>표시 범위</span>
            <strong>1M · 3M · 6M · 1Y · 3Y · 5Y</strong>
            <em>5Y bars를 받아 화면 범위만 줄여 이평선 끊김을 줄임</em>
          </article>
        </div>
        <div class="chart-contract-fields" aria-label="차트 API 필수 응답 필드">
          <b>필수 응답 필드</b>
          <span v-for="field in requiredChartFields" :key="field">{{ field }}</span>
        </div>
      </div>

      <section v-if="canShowInvestorFlowPanel" class="investor-flow-panel" aria-label="일별 수급">
        <div class="investor-flow-head">
          <div>
            <p class="label">investor flow</p>
            <h4>일별 수급 추정치</h4>
          </div>
          <span class="status-pill subtle">{{ investorFlowStatusLabel }}</span>
        </div>

        <div v-if="canRenderInvestorFlow" class="investor-flow-meta" aria-label="수급 데이터 기준">
          <span v-for="item in investorFlowMetaItems" :key="item.label">
            <b>{{ item.label }}</b>
            {{ item.value }}
          </span>
        </div>

        <div v-if="canRenderInvestorFlow" class="investor-flow-table-wrap" aria-label="최근 거래일 수급 표">
          <table class="investor-flow-table">
            <thead>
              <tr>
                <th>날짜</th>
                <th>종가</th>
                <th>전일비</th>
                <th>등락률</th>
                <th>거래량</th>
                <th>{{ investorFlowSubjectLabels.individual }}</th>
                <th>{{ investorFlowSubjectLabels.foreign }}</th>
                <th>{{ investorFlowSubjectLabels.institution }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in investorFlowTableRows" :key="row.key">
                <td>{{ row.dateLabel }}</td>
                <td>{{ row.closeLabel }}</td>
                <td :class="row.changeTone">{{ row.changeLabel }}</td>
                <td :class="row.changeTone">{{ row.changePctLabel }}</td>
                <td>{{ row.volumeLabel }}</td>
                <td :class="[row.individual.tone, { derived: row.individual.derived }]" :title="row.individual.title">
                  {{ row.individual.volumeLabel }}
                </td>
                <td :class="[row.foreign.tone, { derived: row.foreign.derived }]" :title="row.foreign.title">
                  {{ row.foreign.volumeLabel }}
                </td>
                <td :class="[row.institution.tone, { derived: row.institution.derived }]" :title="row.institution.title">
                  {{ row.institution.volumeLabel }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="investor-flow-empty" aria-label="수급 데이터 없음">
          {{ investorFlowEmptyMessage }}
        </div>

        <p class="investor-flow-note">
          수급은 공개 표 기반 추정치라 실제 확정값과 다를 수 있습니다. 개인(잔차)은 외국인/기관 관찰 수량으로 계산한 값이며,
          종가·전일비·거래량은 차트 API에 같은 날짜 bar가 없으면 -로 표시합니다.
        </p>
      </section>
      <p class="chart-data-note">
        현재가·등락률·거래량은 quote snapshot API, 메인 차트는 chart-candles API, 일별 수급은 investor-flows/history API를 각각 따로 사용합니다.
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
