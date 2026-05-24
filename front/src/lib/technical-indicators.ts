import type { StockChartCandle } from '../fixtures/stock-detail-chart';

export type RsiPoint = {
  time: string;
  value: number | null;
};

export type BollingerBandPoint = {
  time: string;
  upper: number | null;
  middle: number | null;
  lower: number | null;
};

const round = (value: number) => Math.round(value * 100) / 100;

export const calculateRsi = (bars: StockChartCandle[], period = 14): RsiPoint[] => {
  return bars.map((bar, index) => {
    if (index < period) {
      return { time: bar.time, value: null };
    }

    const window = bars.slice(index - period, index + 1);
    let gains = 0;
    let losses = 0;
    for (let cursor = 1; cursor < window.length; cursor += 1) {
      const delta = window[cursor].close - window[cursor - 1].close;
      if (delta >= 0) gains += delta;
      else losses += Math.abs(delta);
    }

    const averageGain = gains / period;
    const averageLoss = losses / period;
    if (averageLoss === 0) {
      return { time: bar.time, value: averageGain === 0 ? 50 : 100 };
    }

    const relativeStrength = averageGain / averageLoss;
    return {
      time: bar.time,
      value: round(100 - 100 / (1 + relativeStrength))
    };
  });
};

export const calculateBollingerBands = (
  bars: StockChartCandle[],
  period = 20,
  multiplier = 2
): BollingerBandPoint[] => {
  return bars.map((bar, index) => {
    if (index < period - 1) {
      return { time: bar.time, upper: null, middle: null, lower: null };
    }

    const window = bars.slice(index - period + 1, index + 1);
    const middle = window.reduce((sum, item) => sum + item.close, 0) / period;
    const variance = window.reduce((sum, item) => sum + (item.close - middle) ** 2, 0) / period;
    const bandWidth = Math.sqrt(variance) * multiplier;

    return {
      time: bar.time,
      upper: round(middle + bandWidth),
      middle: round(middle),
      lower: round(middle - bandWidth)
    };
  });
};
