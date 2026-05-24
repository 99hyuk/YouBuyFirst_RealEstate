import { describe, expect, it } from 'vitest';

import { calculateBollingerBands, calculateRsi } from '../lib/technical-indicators';

const bars = (closes: number[]) =>
  closes.map((close, index) => ({
    time: `2026-05-${String(index + 1).padStart(2, '0')}`,
    open: close,
    high: close,
    low: close,
    close,
    volume: 1000 + index,
    individual: 0,
    foreign: 0,
    institution: 0
  }));

describe('technical indicators', () => {
  it('calculates RSI from chart bar closes', () => {
    const rsi = calculateRsi(bars([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]), 14);

    expect(rsi).toHaveLength(15);
    expect(rsi.slice(0, 14).every((point) => point.value === null)).toBe(true);
    expect(rsi[14]).toEqual({ time: '2026-05-15', value: 100 });
  });

  it('returns flat Bollinger bands when the window has no variance', () => {
    const bands = calculateBollingerBands(bars(Array.from({ length: 20 }, () => 10)), 20, 2);

    expect(bands).toHaveLength(20);
    expect(bands.slice(0, 19).every((point) => point.middle === null)).toBe(true);
    expect(bands[19]).toEqual({
      time: '2026-05-20',
      upper: 10,
      middle: 10,
      lower: 10
    });
  });
});
