import { mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { nextTick } from 'vue';

const chartMocks = vi.hoisted(() => {
  const series = {
    setData: vi.fn()
  };
  const timeScaleApi = {
    fitContent: vi.fn(),
    applyOptions: vi.fn(),
    setVisibleLogicalRange: vi.fn(),
    subscribeVisibleLogicalRangeChange: vi.fn()
  };
  const chartApi = {
    addSeries: vi.fn(() => series),
    applyOptions: vi.fn(),
    priceScale: vi.fn(() => ({ applyOptions: vi.fn() })),
    remove: vi.fn(),
    subscribeCrosshairMove: vi.fn(),
    timeScale: vi.fn(() => timeScaleApi)
  };

  return {
    chartApi,
    createChart: vi.fn(() => chartApi),
    createSeriesMarkers: vi.fn(),
    series,
    timeScaleApi
  };
});

vi.mock('lightweight-charts', () => ({
  CandlestickSeries: 'CandlestickSeries',
  ColorType: { Solid: 'solid' },
  CrosshairMode: { Normal: 'normal' },
  HistogramSeries: 'HistogramSeries',
  LineSeries: 'LineSeries',
  PriceScaleMode: { Logarithmic: 'logarithmic', Normal: 'normal' },
  TickMarkType: { Year: 0, Month: 1, DayOfMonth: 2, Time: 3, TimeWithSeconds: 4 },
  createChart: chartMocks.createChart,
  createSeriesMarkers: chartMocks.createSeriesMarkers
}));

const originalUserAgent = window.navigator.userAgent;

const candles = Array.from({ length: 25 }, (_, index) => {
  const close = 100 + index;

  return {
    time: `2026-05-${String(index + 1).padStart(2, '0')}`,
    open: close - 1,
    high: close + 2,
    low: close - 2,
    close,
    volume: 1000 + index,
    individual: 0,
    foreign: 0,
    institution: 0
  };
});

const technicalIndicators = (value: number) => ({
  provider: 'backend-derived',
  sourceProvider: 'yfinance',
  asOf: '2026-05-24T00:00:00Z',
  stale: false,
  dataStatus: 'OK',
  rsi: {
    period: 14,
    points: [{ date: '2026-05-20', value }]
  },
  bollingerBands: {
    period: 20,
    multiplier: 2,
    points: [{ date: '2026-05-20', upper: 130, middle: 120, lower: 110 }]
  }
});

const baseProps = {
  title: 'JPMorgan Chase',
  providerSymbol: 'JPM',
  currency: 'USD' as const,
  priceUnit: 'USD',
  volumeUnit: 'shares',
  flowUnit: 'shares',
  chartSource: 'yfinance',
  candles,
  dataMode: 'actual' as const,
  showFlowSummary: false
};

const flushChartRender = async () => {
  await nextTick();
  await Promise.resolve();
  await nextTick();
};

describe('StockPriceChart', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    Object.defineProperty(window.navigator, 'userAgent', {
      configurable: true,
      value: 'vitest-browser'
    });
    vi.stubGlobal(
      'ResizeObserver',
      class {
        observe = vi.fn();
        disconnect = vi.fn();
      }
    );
  });

  afterEach(() => {
    Object.defineProperty(window.navigator, 'userAgent', {
      configurable: true,
      value: originalUserAgent
    });
    vi.unstubAllGlobals();
  });

  it('rerenders when backend technical indicators arrive after candles', async () => {
    const { default: StockPriceChart } = await import('../components/StockPriceChart.vue');
    const wrapper = mount(StockPriceChart, {
      props: {
        ...baseProps,
        technicalIndicators: null
      },
      attachTo: document.body
    });

    await flushChartRender();

    expect(chartMocks.createChart).toHaveBeenCalledTimes(1);

    await wrapper.setProps({
      technicalIndicators: technicalIndicators(64)
    });
    await flushChartRender();

    expect(chartMocks.createChart).toHaveBeenCalledTimes(2);
  });
});
