<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  PriceScaleMode,
  TickMarkType,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type SeriesMarker,
  type Time
} from 'lightweight-charts';

import type { StockChartCandle } from '../fixtures/stock-detail-chart';

type ChartRange = '1M' | '3M' | '6M' | '1Y' | '3Y' | '5Y';
type CandleMode = '일' | '주' | '월';
type MovingAverageOption = {
  id: string;
  label: string;
  window: number;
  color: string;
  group: 'short' | 'long';
};

const props = defineProps<{
  title: string;
  providerSymbol: string;
  currency: 'KRW' | 'USD';
  priceUnit: string;
  volumeUnit: string;
  flowUnit: string;
  chartSource: string;
  candles: StockChartCandle[];
  snapshotPrice?: number;
  snapshotVolume?: number;
  snapshotAsOf?: string;
  snapshotStatus?: string;
  dataMode?: 'fixture' | 'actual';
  showFlowSummary?: boolean;
}>();

const chartEl = ref<HTMLDivElement | null>(null);
const selectedRange = ref<ChartRange>('3M');
const candleMode = ref<CandleMode>('일');
const scaleMode = ref<'log' | 'linear'>('log');
const showSignals = ref(true);
const flowView = ref<'aggregate' | 'subjects'>('aggregate');
const activeShortMa = ref(new Set([5, 20]));
const activeLongMa = ref(new Set<number>());
const chartRanges = ['1M', '3M', '6M', '1Y', '3Y', '5Y'] as const satisfies readonly ChartRange[];
const candleModes = ['일', '주', '월'] as const;
const shortMovingAverages = [
  { id: 'short-5', label: 'MA5', window: 5, color: '#2f6fed', group: 'short' },
  { id: 'short-10', label: 'MA10', window: 10, color: '#10b981', group: 'short' },
  { id: 'short-20', label: 'MA20', window: 20, color: '#f59e0b', group: 'short' }
] as const satisfies readonly MovingAverageOption[];
const longMovingAverages = [
  { id: 'long-60', label: 'MA60', window: 60, color: '#8b5cf6', group: 'long' },
  { id: 'long-120', label: 'MA120', window: 120, color: '#ec4899', group: 'long' },
  { id: 'long-200', label: 'MA200', window: 200, color: '#64748b', group: 'long' }
] as const satisfies readonly MovingAverageOption[];
const isTestMode = typeof window !== 'undefined' && window.navigator.userAgent.includes('jsdom');
const chartRendered = ref(false);
const hoveredCandle = ref<StockChartCandle | null>(null);
const visibleLogicalRange = ref<{ from: number; to: number } | null>(null);

let chart: IChartApi | null = null;
let resizeObserver: ResizeObserver | null = null;

const tradingDayRanges = {
  '1M': 22,
  '3M': 66,
  '6M': 132,
  '1Y': 252,
  '3Y': 756,
  '5Y': 1260
} as const;

const chartDataMode = computed(() => props.dataMode ?? 'fixture');
const isFixtureChart = computed(() => chartDataMode.value === 'fixture');
const showFlowSummary = computed(() => props.showFlowSummary !== false);

const modeDivisor = computed(() => {
  if (candleMode.value === '주') return 5;
  if (candleMode.value === '월') return 21;
  return 1;
});

const aggregateCandles = (candles: StockChartCandle[], mode: Exclude<CandleMode, '일'>) => {
  const groups = new Map<string, StockChartCandle[]>();

  candles.forEach((candle) => {
    const date = new Date(`${candle.time}T00:00:00`);
    const key =
      mode === '월'
        ? `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
        : `${date.getFullYear()}-${String(Math.ceil((date.getDate() + new Date(date.getFullYear(), date.getMonth(), 1).getDay()) / 7)).padStart(2, '0')}-${date.getMonth()}`;
    const group = groups.get(key) ?? [];
    group.push(candle);
    groups.set(key, group);
  });

  return [...groups.values()].map((group) => ({
    time: group.at(-1)?.time ?? group[0].time,
    open: group[0].open,
    high: Math.max(...group.map((item) => item.high)),
    low: Math.min(...group.map((item) => item.low)),
    close: group.at(-1)?.close ?? group[0].close,
    volume: group.reduce((sum, item) => sum + item.volume, 0),
    individual: group.reduce((sum, item) => sum + item.individual, 0),
    foreign: group.reduce((sum, item) => sum + item.foreign, 0),
    institution: group.reduce((sum, item) => sum + item.institution, 0)
  }));
};

const chartCandles = computed(() => {
  if (candleMode.value === '일') return props.candles;
  return aggregateCandles(props.candles, candleMode.value);
});

const rangeSize = computed(() => {
  const days = tradingDayRanges[selectedRange.value];
  if (!Number.isFinite(days)) return chartCandles.value.length;
  return Math.max(1, Math.ceil(days / modeDivisor.value));
});

const selectedLogicalWindow = computed(() => {
  const count = chartCandles.value.length;
  if (count === 0) return null;

  const size = Math.min(rangeSize.value, count);
  return {
    from: Math.max(0, count - size),
    to: count - 1
  };
});

const candlesInLogicalRange = (range: { from: number; to: number } | null) => {
  const candles = chartCandles.value;
  if (!range || candles.length === 0) return candles;

  const from = Math.max(0, Math.floor(range.from));
  const to = Math.min(candles.length - 1, Math.ceil(range.to));
  if (from > to) return [];

  return candles.slice(from, to + 1);
};

const visibleRangeCandles = computed(() => candlesInLogicalRange(visibleLogicalRange.value ?? selectedLogicalWindow.value));
const inspectedCandle = computed(() => hoveredCandle.value ?? visibleRangeCandles.value.at(-1) ?? chartCandles.value.at(-1));
const latest = computed(() => inspectedCandle.value);
const previous = computed(() => {
  const index = chartCandles.value.findIndex((item) => item.time === inspectedCandle.value?.time);
  return chartCandles.value[index - 1] ?? visibleRangeCandles.value.at(-2) ?? chartCandles.value.at(-2);
});
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
const changeSummary = computed(() => {
  const direction = change.value.rate > 0 ? '상승' : change.value.rate < 0 ? '하락' : '보합';
  const sign = change.value.rate > 0 ? '+' : '';
  const close = latest.value ? formatPrice(latest.value.close) : '-';

  return `${close} · ${sign}${change.value.rate.toFixed(2)}% ${direction}`;
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

const formatSignedFlow = (value: number) => {
  const normalized = Object.is(value, -0) ? 0 : value;
  const sign = normalized > 0 ? '+' : '';
  return `${sign}${normalized.toLocaleString('ko-KR')}${props.flowUnit}`;
};

const formatAxisDate = (value?: string) => {
  if (!value) return '-';
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat('ko-KR', {
    year: candleMode.value === '월' ? 'numeric' : undefined,
    month: '2-digit',
    day: candleMode.value === '월' ? undefined : '2-digit'
  }).format(date);
};

const formatBoundaryDate = (value: string | undefined, includeYear: boolean) => {
  if (!value) return '-';
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat('ko-KR', {
    year: includeYear ? '2-digit' : undefined,
    month: '2-digit',
    day: candleMode.value === '월' ? undefined : '2-digit'
  }).format(date);
};

const toChartDate = (value?: string) => {
  if (!value) return null;
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
};

const timeToDateString = (time: Time) => {
  if (typeof time === 'string') return time;
  if (typeof time === 'object' && 'year' in time) {
    return `${time.year}-${String(time.month).padStart(2, '0')}-${String(time.day).padStart(2, '0')}`;
  }

  return String(time);
};

const formatTickMark = (time: Time, tickMarkType: TickMarkType) => {
  const dateValue = timeToDateString(time);
  const date = new Date(`${dateValue}T00:00:00`);
  if (Number.isNaN(date.getTime())) return dateValue;

  if (tickMarkType === TickMarkType.Year) {
    return new Intl.DateTimeFormat('ko-KR', { year: 'numeric' }).format(date);
  }

  if (tickMarkType === TickMarkType.Month) {
    return new Intl.DateTimeFormat('ko-KR', { month: 'short' }).format(date);
  }

  return new Intl.DateTimeFormat('ko-KR', { month: '2-digit', day: '2-digit' }).format(date);
};

const formatSnapshotTime = (value?: string) => {
  if (!value) return 'snapshot 대기';
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

const visibleAxisCandles = computed(() => {
  const candles = visibleRangeCandles.value;
  return candles.length ? candles : chartCandles.value;
});

const formatAxisTickLabel = (value: string, index: number, candles: StockChartCandle[]) => {
  const date = toChartDate(value);
  if (!date) return value;

  const visibleCount = candles.length;
  if (candleMode.value === '월' || visibleCount >= 900) {
    return `${String(date.getFullYear()).slice(2)}년`;
  }

  if (visibleCount >= 260) {
    return `${String(date.getFullYear()).slice(2)}.${String(date.getMonth() + 1).padStart(2, '0')}`;
  }

  if (candleMode.value === '주' || visibleCount >= 110) {
    return `${date.getMonth() + 1}월`;
  }

  const previous = toChartDate(candles[index - 1]?.time);
  if (!previous || previous.getMonth() !== date.getMonth() || previous.getFullYear() !== date.getFullYear()) {
    return `${date.getMonth() + 1}월`;
  }

  return `${date.getMonth() + 1}/${date.getDate()}`;
};

const axisTickLabels = computed(() => {
  const candles = visibleAxisCandles.value;
  if (!candles.length) return [];

  const indexes = new Set<number>();
  if (candles.length >= 900) {
    let currentYear: number | null = null;
    indexes.add(0);
    candles.forEach((candle, index) => {
      const year = toChartDate(candle.time)?.getFullYear();
      if (year && year !== currentYear) {
        indexes.add(index);
        currentYear = year;
      }
    });
  } else {
    const targetCount = Math.min(candles.length, 9);
    for (let tickIndex = 0; tickIndex < targetCount; tickIndex += 1) {
      indexes.add(Math.round((tickIndex * (candles.length - 1)) / (targetCount - 1)));
    }
  }

  const ticks = [...indexes]
    .sort((a, b) => a - b)
    .map((index) => ({
      key: `${candles[index].time}-${index}`,
      label: formatAxisTickLabel(candles[index].time, index, candles)
    }));

  return ticks.filter((tick, index) => index === 0 || tick.label !== ticks[index - 1].label);
});

const axisSummary = computed(() => {
  const candles = visibleAxisCandles.value;
  const start = candles.at(0)?.time;
  const end = candles.at(-1)?.time;
  const startYear = start ? new Date(`${start}T00:00:00`).getFullYear() : null;
  const endYear = end ? new Date(`${end}T00:00:00`).getFullYear() : null;
  const includeYear = candleMode.value === '월' || candles.length >= 132 || startYear !== endYear;

  return {
    start: formatBoundaryDate(start, includeYear),
    end: formatBoundaryDate(end, includeYear),
    count: candles.length,
    mode: `${candleMode.value}봉`,
    range: selectedRange.value
  };
});

const chartSourceLabel = computed(() =>
  isFixtureChart.value ? `${props.chartSource} · 실제 ${props.providerSymbol} 일봉 아님` : props.chartSource
);

const chartBarSpacing = (width: number, visibleCount: number) =>
  Math.max(0.35, Math.min(32, (width - 72) / Math.max(visibleCount, 1)));

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

const movingAverageLines = computed(() => {
  const shortLines = shortMovingAverages.filter((line) => activeShortMa.value.has(line.window));
  const longLines = longMovingAverages.filter((line) => activeLongMa.value.has(line.window));

  return [...shortLines, ...longLines].sort((a, b) => a.window - b.window || a.id.localeCompare(b.id));
});

const movingAverageLegend = computed(() =>
  [...shortMovingAverages, ...longMovingAverages].map((line) => ({
    ...line,
    active: line.group === 'short' ? activeShortMa.value.has(line.window) : activeLongMa.value.has(line.window)
  }))
);

const signalMarkers = computed<SeriesMarker<Time>[]>(() => {
  if (!showSignals.value) return [];

  const markers: SeriesMarker<Time>[] = [];

  chartCandles.value.forEach((item, index) => {
    const spread = item.close - item.open;

    if (index % 17 === 6 && spread >= 0) {
      markers.push({
        time: item.time as Time,
        position: 'belowBar',
        color: '#2f6fed',
        shape: 'arrowUp',
        text: 'B'
      });
    }

    if (index % 19 === 10 && spread < 0) {
      markers.push({
        time: item.time as Time,
        position: 'aboveBar',
        color: '#ef3f55',
        shape: 'arrowDown',
        text: 'S'
      });
    }
  });

  return markers.slice(-24);
});

const flowSummary = computed(() => {
  const rangeCandles = visibleRangeCandles.value.length ? visibleRangeCandles.value : chartCandles.value;
  const totals = rangeCandles.reduce(
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

const flowBars = computed(() => {
  if (flowView.value === 'subjects') return flowSummary.value;

  const buy = flowSummary.value.filter((item) => item.value > 0).reduce((sum, item) => sum + item.value, 0);
  const sell = flowSummary.value.filter((item) => item.value < 0).reduce((sum, item) => sum + Math.abs(item.value), 0);
  const flowWindowSize = Math.max((visibleRangeCandles.value.length ? visibleRangeCandles.value : chartCandles.value).length, 1);
  const ma = Math.round((buy - sell) / flowWindowSize);

  return [
    { label: '매수', value: buy },
    { label: '매도', value: -sell },
    { label: '20MA', value: ma }
  ];
});

const maxFlow = computed(() => Math.max(...flowBars.value.map((item) => Math.abs(item.value)), 1));

const toggleShortMa = (value: number) => {
  const next = new Set(activeShortMa.value);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  activeShortMa.value = next;
};

const toggleLongMa = (value: number) => {
  const next = new Set(activeLongMa.value);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  activeLongMa.value = next;
};

const clearLongMa = () => {
  activeLongMa.value = new Set();
};

const setCandleMode = (mode: (typeof candleModes)[number]) => {
  candleMode.value = mode;
  hoveredCandle.value = null;
};

const applySelectedWindow = () => {
  if (!chart || !chartEl.value) return;

  const window = selectedLogicalWindow.value;
  if (!window) {
    chart.timeScale().fitContent();
    visibleLogicalRange.value = null;
    return;
  }

  const visibleCount = Math.max(1, window.to - window.from + 1);
  chart.timeScale().applyOptions({
    barSpacing: chartBarSpacing(chartEl.value.clientWidth || 960, visibleCount),
    rightOffset: 0
  });
  chart.timeScale().setVisibleLogicalRange(window);
  visibleLogicalRange.value = window;
};

const renderChart = async () => {
  await nextTick();

  if (isTestMode || !chartEl.value || chartCandles.value.length === 0) {
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
    handleScroll: {
      horzTouchDrag: true,
      mouseWheel: true,
      pressedMouseMove: true
    },
    handleScale: {
      axisPressedMouseMove: true,
      mouseWheel: true,
      pinch: true
    },
    localization: {
      locale: 'ko-KR',
      priceFormatter: formatPrice,
      timeFormatter: (time: Time) => formatAxisDate(timeToDateString(time))
    },
    grid: {
      vertLines: { color: 'rgba(99, 113, 132, 0.11)' },
      horzLines: { color: 'rgba(99, 113, 132, 0.11)' }
    },
    crosshair: {
      mode: CrosshairMode.Normal
    },
    rightPriceScale: {
      mode: scaleMode.value === 'log' ? PriceScaleMode.Logarithmic : PriceScaleMode.Normal,
      borderColor: '#d7e0eb',
      scaleMargins: { top: 0.08, bottom: 0.28 }
    },
    timeScale: {
      borderColor: '#d7e0eb',
      rightOffset: 0,
      barSpacing: chartBarSpacing(width, rangeSize.value),
      minBarSpacing: 0.35,
      fixLeftEdge: true,
      fixRightEdge: true,
      rightBarStaysOnScroll: true,
      timeVisible: true,
      secondsVisible: false,
      tickMarkFormatter: formatTickMark
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
    chartCandles.value.map((item) => ({
      time: item.time as Time,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close
    }))
  );

  if (showSignals.value) {
    createSeriesMarkers(candleSeries, signalMarkers.value);
  }

  const volumeSeries = chart.addSeries(HistogramSeries, {
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume',
    color: '#cbd5e1'
  });

  chart.priceScale('volume').applyOptions({
    scaleMargins: { top: 0.78, bottom: 0 }
  });

  volumeSeries.setData(
    chartCandles.value.map((item) => ({
      time: item.time as Time,
      value: item.volume,
      color: item.close >= item.open ? 'rgba(239, 63, 85, 0.54)' : 'rgba(47, 111, 237, 0.52)'
    }))
  );

  movingAverageLines.value.forEach((line) => {
    const series = chart?.addSeries(LineSeries, {
      color: line.color,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false
    });
    series?.setData(movingAverage(chartCandles.value, line.window));
  });

  chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
    visibleLogicalRange.value = range ? { from: range.from, to: range.to } : null;
  });
  applySelectedWindow();
  chart.subscribeCrosshairMove((param) => {
    if (!param.time) {
      hoveredCandle.value = null;
      return;
    }

    const hoverTime = param.time;
    hoveredCandle.value = hoverTime ? chartCandles.value.find((item) => item.time === timeToDateString(hoverTime)) ?? null : null;
  });
  chartRendered.value = true;

  resizeObserver = new ResizeObserver(() => {
    if (chartEl.value && chart) {
      chart.applyOptions({ width: chartEl.value.clientWidth });
      applySelectedWindow();
    }
  });
  resizeObserver.observe(chartEl.value);
};

const setRange = (range: ChartRange) => {
  selectedRange.value = range;
  hoveredCandle.value = null;
};

onMounted(renderChart);
watch(
  [
    () => props.candles,
    () => props.providerSymbol,
    candleMode,
    selectedRange,
    scaleMode,
    showSignals,
    activeShortMa,
    activeLongMa
  ],
  renderChart
);

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
        <span>{{ providerSymbol }} · {{ chartSourceLabel }}</span>
      </div>
      <span class="status-pill subtle">{{ props.snapshotStatus ?? 'front-only chart shell' }}</span>
    </div>

    <div v-if="isFixtureChart" class="chart-source-warning" role="note">
      <strong>차트 UI fixture</strong>
      <span>현재가 quote만 API 값입니다. 이 캔들 모양과 날짜별 OHLC는 실제 일자별 {{ providerSymbol }} 데이터가 아닙니다.</span>
    </div>

    <div class="chart-feature-strip" aria-label="차트 기능">
      <div class="chart-feature-group">
        <span class="chart-feature-label">봉</span>
        <div class="chart-feature-controls">
          <button
            v-for="mode in candleModes"
            :key="mode"
            type="button"
            :class="{ active: candleMode === mode }"
            @click="setCandleMode(mode)"
          >
            {{ mode }}
          </button>
        </div>
      </div>
      <div class="chart-feature-group wide">
        <span class="chart-feature-label">기간</span>
        <div class="chart-feature-controls">
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
      <div class="chart-feature-group wide">
        <span class="chart-feature-label">표시</span>
        <div class="chart-feature-controls">
          <button type="button" :class="{ active: showSignals }" @click="showSignals = !showSignals">B/S</button>
          <button type="button" :class="{ active: scaleMode === 'log' }" @click="scaleMode = 'log'">로그</button>
          <button type="button" :class="{ active: scaleMode === 'linear' }" @click="scaleMode = 'linear'">선형</button>
        </div>
      </div>
      <div class="chart-feature-group">
        <span class="chart-feature-label">단기</span>
        <div class="chart-feature-controls">
          <button
            v-for="line in shortMovingAverages"
            :key="line.id"
            type="button"
            :class="{ active: activeShortMa.has(line.window) }"
            @click="toggleShortMa(line.window)"
          >
            {{ line.window }}
          </button>
        </div>
      </div>
      <div class="chart-feature-group">
        <span class="chart-feature-label">장기</span>
        <div class="chart-feature-controls">
          <button type="button" :class="{ active: activeLongMa.size === 0 }" @click="clearLongMa">OFF</button>
          <button
            v-for="line in longMovingAverages"
            :key="line.id"
            type="button"
            :class="{ active: activeLongMa.has(line.window) }"
            @click="toggleLongMa(line.window)"
          >
            {{ line.window }}
          </button>
        </div>
      </div>
    </div>

    <div class="chart-ma-legend" aria-label="이동평균선 색상">
      <span
        v-for="line in movingAverageLegend"
        :key="line.id"
        :class="{ muted: !line.active }"
      >
        <i :style="{ backgroundColor: line.color }"></i>{{ line.label }}
      </span>
    </div>

    <div v-if="showSignals" class="chart-signal-legend" aria-label="B/S 관찰 신호 설명">
      <span><b>B</b> 하단권 + 수급 유입</span>
      <span><b>S</b> 상단권 + 수급 유출</span>
      <em>참고용 관찰 표시 · 실시간 매매 신호 아님</em>
    </div>

    <div class="chart-ohlc-strip" v-if="latest">
      <span>{{ latest.time }}<template v-if="isFixtureChart"> · fixture</template></span>
      <span>O {{ formatPrice(latest.open) }}</span>
      <span>H {{ formatPrice(latest.high) }}</span>
      <span>L {{ formatPrice(latest.low) }}</span>
      <span>C {{ formatPrice(latest.close) }}</span>
      <strong :class="change.tone">{{ changeSummary }}</strong>
    </div>

    <div ref="chartEl" class="stock-lightweight-chart">
      <div v-if="isTestMode || !chartRendered" class="stock-chart-test-fallback">
        <strong>{{ providerSymbol }}</strong>
        <span>{{ title }} · {{ chartCandles.length }}개 캔들</span>
      </div>
    </div>

    <div class="chart-axis-strip" aria-label="차트 날짜 축 요약">
      <div class="chart-axis-ticks">
        <span v-for="tick in axisTickLabels" :key="tick.key">{{ tick.label }}</span>
      </div>
      <div class="chart-axis-meta">
        <strong>{{ axisSummary.mode }} · {{ axisSummary.range }} · {{ axisSummary.count }}개</strong>
        <em>{{ isFixtureChart ? '샘플 축' : `기준 ${formatSnapshotTime(props.snapshotAsOf)}` }}</em>
      </div>
    </div>

    <div class="stock-chart-lower-grid" :class="{ 'volume-only': !showFlowSummary }">
      <article class="volume-brief">
        <span>거래량</span>
        <strong>{{ latest ? formatCompact(latest.volume) : '-' }}{{ volumeUnit }}</strong>
        <em>캔들 하단 히스토그램 표시</em>
      </article>
      <article v-if="showFlowSummary" class="flow-brief">
        <div>
          <span>매매 동향</span>
          <div class="flow-mode-tabs" aria-label="매매동향 보기 방식">
            <button type="button" :class="{ active: flowView === 'aggregate' }" @click="flowView = 'aggregate'">합산</button>
            <button type="button" :class="{ active: flowView === 'subjects' }" @click="flowView = 'subjects'">주체별</button>
          </div>
          <strong>{{ selectedRange }} 누적</strong>
        </div>
        <div class="flow-bars">
          <div v-for="item in flowBars" :key="item.label">
            <span>{{ item.label }}</span>
            <i>
              <mark
                :class="item.value >= 0 ? 'up' : 'down'"
                :style="{ width: `${Math.max(9, (Math.abs(item.value) / maxFlow) * 100)}%` }"
              ></mark>
            </i>
            <strong :class="item.value >= 0 ? 'up' : 'down'">
              {{ formatSignedFlow(item.value) }}
            </strong>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
