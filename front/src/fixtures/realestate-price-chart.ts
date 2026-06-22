export type RealEstatePricePoint = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  trade: number;
  rent: number;
  supply: number;
};

export type RealEstatePriceChartFixture = {
  targetId: string;
  providerTargetId: string;
  priceUnit: string;
  volumeUnit: string;
  flowUnit: string;
  chartSource: string;
  pricePoints: RealEstatePricePoint[];
};

const pad = (value: number) => String(value).padStart(2, '0');

const addObservationDates = (start: Date, count: number) => {
  const days: string[] = [];
  const cursor = new Date(start);

  while (days.length < count) {
    days.push(`${cursor.getFullYear()}-${pad(cursor.getMonth() + 1)}-${pad(cursor.getDate())}`);
    cursor.setDate(cursor.getDate() + 1);
  }

  return days;
};

const buildPricePoints = ({
  targetId,
  providerTargetId,
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
}: Omit<RealEstatePriceChartFixture, 'pricePoints'> & {
  startDate: string;
  startPrice: number;
  targetClose: number;
  points: number;
  drift: number;
  wave: number;
  volumeBase: number;
  flowBase: number;
}) => {
  const dates = addObservationDates(new Date(startDate), points);
  let previousClose = startPrice;

  const pricePoints = dates.map((time, index) => {
    const direction = Math.sin(index / 4.2) * wave + Math.cos(index / 9) * wave * 0.45 + drift;
    const open = previousClose * (1 + Math.sin(index / 7) * 0.004);
    const close = Math.max(open * (1 + direction / 100), startPrice * 0.72);
    const high = Math.max(open, close) * (1 + (0.009 + Math.abs(Math.sin(index / 3)) * 0.011));
    const low = Math.min(open, close) * (1 - (0.008 + Math.abs(Math.cos(index / 5)) * 0.009));
    const volume = Math.round(volumeBase * (1 + Math.abs(direction) * 0.2 + Math.abs(Math.sin(index / 2.8)) * 0.85));
    const trade = Math.max(0, Math.round(volumeBase * (0.55 + Math.abs(direction) * 0.08)));
    const rent = Math.max(0, Math.round(volumeBase * (0.34 + Math.abs(Math.sin(index / 3.1)) * 0.12)));
    const supply = Math.round(Math.cos(index / 4.8) * flowBase * 0.72 + direction * flowBase * 0.32);

    previousClose = close;

    return {
      time,
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
      volume,
      trade,
      rent,
      supply
    };
  });

  const lastClose = pricePoints.at(-1)?.close ?? startPrice;
  const scale = targetClose / lastClose;
  const scaledPricePoints = pricePoints.map((pricePoint) => ({
    ...pricePoint,
    open: Math.round(pricePoint.open * scale * 100) / 100,
    high: Math.round(pricePoint.high * scale * 100) / 100,
    low: Math.round(pricePoint.low * scale * 100) / 100,
    close: Math.round(pricePoint.close * scale * 100) / 100
  }));

  return {
    targetId,
    providerTargetId,
    priceUnit,
    volumeUnit,
    flowUnit,
    chartSource,
    pricePoints: scaledPricePoints
  };
};

export const realEstatePriceChartFixtures: RealEstatePriceChartFixture[] = [
  buildPricePoints({
    targetId: 'region-seoul-mapo',
    providerTargetId: 'region-seoul-mapo',
    startDate: '2024-05-24',
    startPrice: 13.8,
    targetClose: 14.5,
    points: 520,
    drift: 0.13,
    wave: 1.45,
    volumeBase: 42,
    flowBase: 72,
    priceUnit: '억원',
    volumeUnit: '건',
    flowUnit: '건',
    chartSource: '국토부 실거래 수집 전 · 실시간 갱신 없음 · 시장 사실 API 연결 후보'
  }),
  buildPricePoints({
    targetId: 'living-area-gyeonggi-dongtan-station',
    providerTargetId: 'living-area-gyeonggi-dongtan-station',
    startDate: '2024-05-24',
    startPrice: 9.2,
    targetClose: 9.8,
    points: 520,
    drift: 0.17,
    wave: 2.2,
    volumeBase: 57,
    flowBase: 185,
    priceUnit: '억원',
    volumeUnit: '건',
    flowUnit: '건',
    chartSource: '국토부 실거래 수집 전 · 실시간 갱신 없음 · 시장 사실 API 연결 후보'
  })
];
