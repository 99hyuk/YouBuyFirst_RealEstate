export type StockChartCandle = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  individual: number;
  foreign: number;
  institution: number;
};

export type StockChartFixture = {
  symbol: string;
  providerSymbol: string;
  currency: 'KRW' | 'USD';
  priceUnit: string;
  volumeUnit: string;
  flowUnit: string;
  chartSource: string;
  candles: StockChartCandle[];
};

const pad = (value: number) => String(value).padStart(2, '0');

const addTradingDays = (start: Date, count: number) => {
  const days: string[] = [];
  const cursor = new Date(start);

  while (days.length < count) {
    const day = cursor.getDay();
    if (day !== 0 && day !== 6) {
      days.push(`${cursor.getFullYear()}-${pad(cursor.getMonth() + 1)}-${pad(cursor.getDate())}`);
    }
    cursor.setDate(cursor.getDate() + 1);
  }

  return days;
};

const buildCandles = ({
  symbol,
  providerSymbol,
  currency,
  startDate,
  startPrice,
  targetClose,
  points,
  drift,
  wave,
  volumeBase,
  flowBase,
  priceUnit,
  volumeUnit,
  flowUnit,
  chartSource
}: Omit<StockChartFixture, 'candles'> & {
  startDate: string;
  startPrice: number;
  targetClose: number;
  points: number;
  drift: number;
  wave: number;
  volumeBase: number;
  flowBase: number;
}) => {
  const dates = addTradingDays(new Date(startDate), points);
  let previousClose = startPrice;

  const candles = dates.map((time, index) => {
    const direction = Math.sin(index / 4.2) * wave + Math.cos(index / 9) * wave * 0.45 + drift;
    const open = previousClose * (1 + Math.sin(index / 7) * 0.004);
    const close = Math.max(open * (1 + direction / 100), startPrice * 0.72);
    const high = Math.max(open, close) * (1 + (0.009 + Math.abs(Math.sin(index / 3)) * 0.011));
    const low = Math.min(open, close) * (1 - (0.008 + Math.abs(Math.cos(index / 5)) * 0.009));
    const volume = Math.round(volumeBase * (1 + Math.abs(direction) * 0.2 + Math.abs(Math.sin(index / 2.8)) * 0.85));
    const foreign = Math.round(Math.sin(index / 3.1) * flowBase + direction * flowBase * 0.48);
    const institution = Math.round(Math.cos(index / 4.8) * flowBase * 0.72 + direction * flowBase * 0.32);
    const individual = Math.round((foreign + institution) * -0.82 + Math.sin(index / 2) * flowBase * 0.25);

    previousClose = close;

    return {
      time,
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
      volume,
      individual,
      foreign,
      institution
    };
  });

  const lastClose = candles.at(-1)?.close ?? startPrice;
  const scale = targetClose / lastClose;
  const scaledCandles = candles.map((candle) => ({
    ...candle,
    open: Math.round(candle.open * scale * 100) / 100,
    high: Math.round(candle.high * scale * 100) / 100,
    low: Math.round(candle.low * scale * 100) / 100,
    close: Math.round(candle.close * scale * 100) / 100
  }));

  return {
    symbol,
    providerSymbol,
    currency,
    priceUnit,
    volumeUnit,
    flowUnit,
    chartSource,
    candles: scaledCandles
  };
};

export const stockChartFixtures: StockChartFixture[] = [
  buildCandles({
    symbol: '005930',
    providerSymbol: 'KRX:005930',
    currency: 'KRW',
    startDate: '2024-05-24',
    startPrice: 69500,
    targetClose: 78200,
    points: 520,
    drift: 0.13,
    wave: 1.45,
    volumeBase: 11200000,
    flowBase: 72,
    priceUnit: '원',
    volumeUnit: '주',
    flowUnit: '억원',
    chartSource: 'KRX 원화 mock · 실시간 갱신 없음 · market API 연결 후보'
  }),
  buildCandles({
    symbol: 'NVDA',
    providerSymbol: 'NASDAQ:NVDA',
    currency: 'USD',
    startDate: '2024-05-24',
    startPrice: 835,
    targetClose: 924.8,
    points: 520,
    drift: 0.17,
    wave: 2.2,
    volumeBase: 36200000,
    flowBase: 185,
    priceUnit: '달러',
    volumeUnit: '주',
    flowUnit: '백만달러',
    chartSource: 'NASDAQ mock · 실시간 갱신 없음 · market API 연결 후보'
  })
];
