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

const pricePoints = Array.from({ length: 25 }, (_, index) => {
  const close = 100 + index;

  return {
    time: `2026-05-${String(index + 1).padStart(2, '0')}`,
    open: close - 1,
    high: close + 2,
    low: close - 2,
    close,
    volume: 1000 + index,
    trade: 10 + index,
    rent: 6 + index,
    supply: index % 2 === 0 ? 1 : 0
  };
});

const baseProps = {
  title: '마포구 아파트',
  providerTargetId: 'region-seoul-mapo',
  priceUnit: '억원',
  volumeUnit: '건',
  flowUnit: '건',
  chartSource: 'molit_apt_trade',
  pricePoints,
  dataMode: 'actual' as const,
  showFlowSummary: false
};

const flushChartRender = async () => {
  await nextTick();
  await Promise.resolve();
  await nextTick();
};

describe('RealEstatePriceChart', () => {
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

  it('rerenders when backend market fact pricePoints change', async () => {
    const { default: RealEstatePriceChart } = await import('../components/RealEstatePriceChart.vue');
    const wrapper = mount(RealEstatePriceChart, {
      props: {
        ...baseProps
      },
      attachTo: document.body
    });

    await flushChartRender();

    expect(chartMocks.createChart).toHaveBeenCalledTimes(1);

    await wrapper.setProps({
      pricePoints: pricePoints.map((pricePoint, index) => ({
        ...pricePoint,
        close: pricePoint.close + (index === pricePoints.length - 1 ? 2 : 0)
      }))
    });
    await flushChartRender();

    expect(chartMocks.createChart).toHaveBeenCalledTimes(2);
  });
});
