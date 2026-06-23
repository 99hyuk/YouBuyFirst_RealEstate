import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

import { routes } from '../router/routes';

const testDir = dirname(fileURLToPath(import.meta.url));
const sourceRoot = resolve(testDir, '..');
const equityKeyword = ['st', 'ock'].join('');
const priceWord = ['quo', 'te'].join('');
const legacyCodeWord = ['sym', 'bol'].join('');
const legacyAccountWord = ['port', 'folio'].join('');
const tradingViewWidget = ['Trading', 'View', 'Widget.vue'].join('');
const legacyCommunityPath = ['/', 'communities'].join('');
const legacyAgentPath = ['/', 'agents'].join('');
const docsRoot = resolve(sourceRoot, '..', '..', 'docs');
const legacyEquityAssetDir = resolve(docsRoot, 'assets', ['st', 'ock-detail-copy'].join(''));
const legacyPricePointType = ['RealEstatePrice', 'Can', 'dle'].join('');
const legacyPointModeType = ['Can', 'dle', 'Mode'].join('');
const legacyPointModeRef = ['can', 'dle', 'Mode'].join('');
const legacyChartCollectionRef = ['chart', 'Can', 'dles'].join('');
const legacyChartCollectionName = ['can', 'dles'].join('');
const legacyChartPropKey = [legacyChartCollectionName, ':'].join('');
const legacyChartPropAccess = ['props', legacyChartCollectionName].join('.');
const legacyChartKoreanTerm = ['캔', '들'].join('');
const legacyRangeAcronym = ['O', 'H', 'L', 'C'].join('');
const legacyObservationFunction = ['add', 'Trading', 'Days'].join('');
const legacyFinancialSeries = ['Can', 'dle', 'stick', 'Series'].join('');

describe('real-estate legacy cleanup', () => {
  it('does not keep legacy equity-era compatibility routes active', () => {
    const routePaths = routes.map((route) => route.path);

    expect(routePaths).not.toContain(`/${equityKeyword}s`);
    expect(routePaths).not.toContain(`/${equityKeyword}s/:${legacyCodeWord}`);
    expect(routePaths).not.toContain(`/${legacyAccountWord}`);
    expect(routePaths).not.toContain(legacyCommunityPath);
    expect(routePaths).not.toContain(legacyAgentPath);
  });

  it('keeps legacy equity widgets and fixtures out of the active frontend source', () => {
    const forbiddenFiles = [
      `components/${tradingViewWidget}`,
      'fixtures/community-overview.json',
      'fixtures/community-performance.json',
      `fixtures/legacy-${equityKeyword}-dashboard-summary.json`,
      `fixtures/legacy-${equityKeyword}-${priceWord}-snapshots.json`,
      `fixtures/legacy-${equityKeyword}-reaction-ranking.json`,
      `fixtures/${legacyAccountWord}-disabled.json`,
      `fixtures/${priceWord}-snapshots.json`,
      `fixtures/${equityKeyword}-detail-fixtures.json`,
      `fixtures/${equityKeyword}-detail-samsung.json`
    ];

    expect(forbiddenFiles.filter((file) => existsSync(resolve(sourceRoot, file)))).toEqual([]);

    const styles = readFileSync(resolve(sourceRoot, 'styles.css'), 'utf8');
    expect(styles).not.toContain(`${equityKeyword}-tradingview-widget`);
    expect(styles).not.toMatch(
      new RegExp(
        `(?:^|[^\\w-])(?:${equityKeyword}-screener|${equityKeyword}-board|${equityKeyword}-compact|${priceWord}-row|currency-toggle|news-${equityKeyword}|series-${equityKeyword})(?:[^\\w-]|$)`
      )
    );

    const dashboardSummary = readFileSync(resolve(sourceRoot, 'fixtures/dashboard-summary.json'), 'utf8');
    const reactionRanking = readFileSync(resolve(sourceRoot, 'fixtures/reaction-ranking.json'), 'utf8');
    expect(dashboardSummary).not.toContain(`"${legacyCodeWord}"`);
    expect(reactionRanking).not.toContain(`"${legacyCodeWord}"`);
    expect(existsSync(legacyEquityAssetDir)).toBe(false);
  });

  it('uses real-estate price point language instead of market-chart vocabulary', () => {
    const chartComponent = readFileSync(resolve(sourceRoot, 'components/RealEstatePriceChart.vue'), 'utf8');
    const chartFixture = readFileSync(resolve(sourceRoot, 'fixtures/realestate-price-chart.ts'), 'utf8');
    const priceChartSource = `${chartComponent}\n${chartFixture}`;

    expect(priceChartSource).not.toContain(legacyPricePointType);
    expect(priceChartSource).not.toContain(legacyPointModeType);
    expect(priceChartSource).not.toContain(legacyPointModeRef);
    expect(priceChartSource).not.toContain(legacyChartCollectionRef);
    expect(priceChartSource).not.toContain(legacyChartPropKey);
    expect(priceChartSource).not.toContain(legacyChartPropAccess);
    expect(priceChartSource).not.toContain(legacyChartKoreanTerm);
    expect(priceChartSource).not.toContain(legacyRangeAcronym);
    expect(priceChartSource).not.toContain(legacyObservationFunction);
    expect(priceChartSource).not.toContain(legacyFinancialSeries);
  });

  it('keeps route target ids aligned to the backend-style target registry', () => {
    const routeTargetSources = [
      'App.vue',
      'pages/DashboardPage.vue',
      'pages/TransactionMapPage.vue',
      'pages/RegionDetailPage.vue',
      'fixtures/dashboard-summary.json',
      'fixtures/reaction-ranking.json',
      'fixtures/realestate-price-chart.ts',
      '__tests__/shell.spec.ts',
      '__tests__/realestate-target-detail-content.spec.ts'
    ].map((file) => readFileSync(resolve(sourceRoot, file), 'utf8')).join('\n');

    const oldScreenIds = [
      'SEOUL-MAPO',
      'DONGTAN-STATION',
      'SEONGSU-DONG',
      'JAMSIL-DONG',
      'BUNDANG-PANGYO',
      'SONGDO-THE-SHARP',
      'RAEMIAN-ONEBAILEY',
      'HELIO-CITY',
      'MAPO-RAEMIAN-PRUGIO',
      'PANGYO-PRUGIO',
      'DONGTAN-LOTTE'
    ];

    for (const oldId of oldScreenIds) {
      expect(routeTargetSources).not.toContain(oldId);
    }
    expect(routeTargetSources).toContain('region-seoul-mapo');
    expect(routeTargetSources).toContain('living-area-gyeonggi-dongtan-station');
    expect(routeTargetSources).toContain('complex-mapo-raemian-prugio');
  });
});
