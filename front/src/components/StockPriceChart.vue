<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  createChart,
  type IChartApi,
  type Time
} from 'lightweight-charts';

import type { StockChartCandle } from '../fixtures/stock-detail-chart';

const props = defineProps<{
  title: string;
  providerSymbol: string;
  currency: 'KRW' | 'USD';
  priceUnit: string;
  volumeUnit: string;
  flowUnit: string;
  chartSource: string;
  candles: StockChartCandle[];
}>();

const chartEl = ref<HTMLDivElement | null>(null);
const selectedRange = ref<'1M' | '3M' | '6M' | '1Y'>('3M');
const chartRanges = ['1M', '3M', '6M', '1Y'] as const;
const isTestMode = typeof window !== 'undefined' && window.navigator.userAgent.includes('jsdom');
const chartRendered = ref(false);

let chart: IChartApi | null = null;
let resizeObserver: ResizeObserver | null = null;

const rangeSize = computed(() => {
  const ranges = {
    '1M': 22,
    '3M': 66,
    '6M': 132,
    '1Y': 252
  };

  return ranges[selectedRange.value];
});

const visibleCandles = computed(() => props.candles.slice(-rangeSize.value));
const latest = computed(() => visibleCandles.value.at(-1) ?? props.candles.at(-1));
const previous = computed(() => visibleCandles.value.at(-2) ?? props.candles.at(-2));
const change = computed(() => {
  if (!latest.value || !previous.value) {
    return { value: 0, rate: 0, tone: 'flat' };
  }

  const value = latest.value.close - previous.value.close;
  return {
    value,
    rate: (value / previous.value.close) * 100,
    tone: value >= 0 ? 'up' : 'down'
  };
});

const formatPrice = (value: number) =>
  props.currency === 'KRW'
    ? `${Math.round(value).toLocaleString('ko-KR')}원`
    : `$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;

const formatCompact = (value: number) => {
  if (Math.abs(value) >= 100000000) {
    return `${(value / 100000000).toFixed(1)}억`;
  }

  if (Math.abs(value) >= 10000) {
    return `${(value / 10000).toFixed(1)}만`;
  }

  return value.toLocaleString('ko-KR');
};

const movingAverage = (source: StockChartCandle[], windowSize: number) =>
  source
    .map((item, index) => {
      if (index < windowSize - 1) {
        return null;
      }

      const window = source.slice(index - windowSize + 1, index + 1);
      const value = window.reduce((sum, candle) => sum + candle.close, 0) / window.length;

      return {
        time: item.time as Time,
        value
      };
    })
    .filter((item): item is { time: Time; value: number } => item !== null);

const flowSummary = computed(() => {
  const totals = visibleCandles.value.reduce(
    (acc, candle) => {
      acc.individual += candle.individual;
      acc.foreign += candle.foreign;
      acc.institution += candle.institution;
      return acc;
    },
    { individual: 0, foreign: 0, institution: 0 }
  );

  return [
    { label: '개인', value: totals.individual },
    { label: '외국인', value: totals.foreign },
    { label: '기관', value: totals.institution }
  ];
});

const maxFlow = computed(() => Math.max(...flowSummary.value.map((item) => Math.abs(item.value)), 1));

const renderChart = async () => {
  await nextTick();

  if (isTestMode || !chartEl.value || visibleCandles.value.length === 0) {
    return;
  }

  chartRendered.value = false;
  chart?.remove();
  resizeObserver?.disconnect();

  const width = chartEl.value.clientWidth || 960;

  chart = createChart(chartEl.value, {
    width,
    height: 430,
    layout: {
      background: { type: ColorType.Solid, color: '#ffffff' },
      textColor: '#58677a',
      attributionLogo: false
    },
    localization: {
      locale: 'ko-KR',
      priceFormatter: formatPrice
    },
    grid: {
      vertLines: { color: 'rgba(99, 113, 132, 0.11)' },
      horzLines: { color: 'rgba(99, 113, 132, 0.11)' }
    },
    crosshair: {
      mode: CrosshairMode.Normal
    },
    rightPriceScale: {
      borderColor: '#d7e0eb',
      scaleMargins: { top: 0.08, bottom: 0.28 }
    },
    timeScale: {
      borderColor: '#d7e0eb',
      timeVisible: true,
      secondsVisible: false
    }
  });

  const candleSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#ef3f55',
    downColor: '#2f6fed',
    borderUpColor: '#ef3f55',
    borderDownColor: '#2f6fed',
    wickUpColor: '#ef3f55',
    wickDownColor: '#2f6fed',
    priceFormat: {
      type: 'custom',
      formatter: formatPrice
    }
  });

  candleSeries.setData(
    visibleCandles.value.map((item) => ({
      time: item.time as Time,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close
    }))
  );

  const volumeSeries = chart.addSeries(HistogramSeries, {
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume',
    color: '#cbd5e1'
  });

  chart.priceScale('volume').applyOptions({
    scaleMargins: { top: 0.78, bottom: 0 }
  });

  volumeSeries.setData(
    visibleCandles.value.map((item) => ({
      time: item.time as Time,
      value: item.volume,
      color: item.close >= item.open ? 'rgba(239, 63, 85, 0.54)' : 'rgba(47, 111, 237, 0.52)'
    }))
  );

  [
    { window: 5, color: '#f59e0b' },
    { window: 20, color: '#2f6fed' },
    { window: 60, color: '#8b5cf6' }
  ].forEach((line) => {
    const series = chart?.addSeries(LineSeries, {
      color: line.color,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false
    });
    series?.setData(movingAverage(visibleCandles.value, line.window));
  });

  chart.timeScale().fitContent();
  chartRendered.value = true;

  resizeObserver = new ResizeObserver(() => {
    if (chartEl.value && chart) {
      chart.applyOptions({ width: chartEl.value.clientWidth });
    }
  });
  resizeObserver.observe(chartEl.value);
};

const setRange = (range: (typeof chartRanges)[number]) => {
  selectedRange.value = range;
};

onMounted(renderChart);
watch([visibleCandles, () => props.providerSymbol], renderChart);

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  chart?.remove();
});
</script>

<template>
  <div class="stock-price-chart-shell">
    <div class="stock-chart-toolbar">
      <div>
        <strong>{{ title }}</strong>
        <span>{{ providerSymbol }} · {{ chartSource }}</span>
      </div>
      <div class="chart-range-tabs" aria-label="차트 기간">
        <button
          v-for="range in chartRanges"
          :key="range"
          type="button"
          :class="{ active: selectedRange === range }"
          @click="setRange(range)"
        >
          {{ range }}
        </button>
      </div>
    </div>

    <div class="chart-ohlc-strip" v-if="latest">
      <span>O {{ formatPrice(latest.open) }}</span>
      <span>H {{ formatPrice(latest.high) }}</span>
      <span>L {{ formatPrice(latest.low) }}</span>
      <span>C {{ formatPrice(latest.close) }}</span>
      <strong :class="change.tone">{{ change.value >= 0 ? '+' : '' }}{{ formatPrice(change.value) }} · {{ change.rate.toFixed(2) }}%</strong>
    </div>

    <div ref="chartEl" class="stock-lightweight-chart">
      <div v-if="isTestMode || !chartRendered" class="stock-chart-test-fallback">
        <strong>{{ providerSymbol }}</strong>
        <span>{{ title }} · {{ visibleCandles.length }}개 캔들</span>
      </div>
    </div>

    <div class="stock-chart-lower-grid">
      <article class="volume-brief">
        <span>거래량</span>
        <strong>{{ latest ? formatCompact(latest.volume) : '-' }}{{ volumeUnit }}</strong>
        <em>캔들 하단 히스토그램 표시</em>
      </article>
      <article class="flow-brief">
        <div>
          <span>매매 동향</span>
          <strong>{{ selectedRange }} 누적</strong>
        </div>
        <div class="flow-bars">
          <div v-for="item in flowSummary" :key="item.label">
            <span>{{ item.label }}</span>
            <i>
              <mark
                :class="item.value >= 0 ? 'up' : 'down'"
                :style="{ width: `${Math.max(9, (Math.abs(item.value) / maxFlow) * 100)}%` }"
              ></mark>
            </i>
            <strong :class="item.value >= 0 ? 'up' : 'down'">
              {{ item.value >= 0 ? '+' : '' }}{{ item.value.toLocaleString('ko-KR') }}{{ flowUnit }}
            </strong>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
