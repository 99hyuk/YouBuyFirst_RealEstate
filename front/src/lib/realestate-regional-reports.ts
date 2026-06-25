import { repairMojibake } from './text-encoding';

export type RealEstateRegionalReportSource = {
  reportSourceId: string;
  displayOrder: number;
  refType: string;
  refId?: string | null;
  label: string;
  title: string;
  url?: string | null;
  sourceName?: string | null;
  publishedAt?: string | null;
  dataStatus?: string | null;
};

export type RealEstateRegionalReport = {
  reportId: string;
  targetId: string;
  targetName: string;
  regionLevel?: string | null;
  regionCode?: string | null;
  reportVersion?: string | null;
  promptVersion?: string | null;
  modelName?: string | null;
  generatedBy?: string | null;
  title: string;
  headline: string;
  summary: string;
  body: string;
  expectationPoints: string[];
  concernPoints: string[];
  dataQuality?: string | null;
  confidence?: number | null;
  asOf?: string | null;
  publishedAt?: string | null;
  sources: RealEstateRegionalReportSource[];
};

type Fetcher = (input: string) => Promise<Response>;

export async function fetchRealEstateRegionalReport(
  targetId: string,
  fetcher: Fetcher = fetch
): Promise<RealEstateRegionalReport | null> {
  const response = await fetcher(`/api/realestate/targets/${encodeURIComponent(targetId)}/regional-report`);
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new Error(`real-estate regional report request failed: ${response.status}`);
  }

  const payload = await response.json() as Partial<RealEstateRegionalReport>;
  return normalizeRegionalReport(payload);
}

function normalizeRegionalReport(payload: Partial<RealEstateRegionalReport>): RealEstateRegionalReport | null {
  if (!payload.reportId || !payload.targetId || !payload.title || !payload.headline || !payload.body) {
    return null;
  }

  return {
    reportId: payload.reportId,
    targetId: payload.targetId,
    targetName: repairMojibake(payload.targetName) || payload.targetId,
    regionLevel: repairMojibake(payload.regionLevel),
    regionCode: repairMojibake(payload.regionCode),
    reportVersion: repairMojibake(payload.reportVersion),
    promptVersion: repairMojibake(payload.promptVersion),
    modelName: repairMojibake(payload.modelName),
    generatedBy: repairMojibake(payload.generatedBy),
    title: repairMojibake(payload.title),
    headline: repairMojibake(payload.headline),
    summary: repairMojibake(payload.summary),
    body: repairMojibake(payload.body),
    expectationPoints: normalizeTextList(payload.expectationPoints),
    concernPoints: normalizeTextList(payload.concernPoints),
    dataQuality: repairMojibake(payload.dataQuality),
    confidence: Number.isFinite(payload.confidence) ? payload.confidence as number : payload.confidence ?? null,
    asOf: repairMojibake(payload.asOf),
    publishedAt: repairMojibake(payload.publishedAt),
    sources: Array.isArray(payload.sources) ? payload.sources.map(normalizeSource).filter(isSource) : []
  };
}

function normalizeSource(source: RealEstateRegionalReportSource): RealEstateRegionalReportSource | null {
  if (!source?.reportSourceId || !source.title) return null;
  return {
    reportSourceId: source.reportSourceId,
    displayOrder: Number.isFinite(source.displayOrder) ? source.displayOrder : 0,
    refType: repairMojibake(source.refType) || 'external',
    refId: repairMojibake(source.refId),
    label: repairMojibake(source.label),
    title: repairMojibake(source.title),
    url: source.url,
    sourceName: repairMojibake(source.sourceName),
    publishedAt: source.publishedAt,
    dataStatus: repairMojibake(source.dataStatus)
  };
}

function isSource(source: RealEstateRegionalReportSource | null): source is RealEstateRegionalReportSource {
  return source !== null;
}

function normalizeTextList(values: unknown): string[] {
  if (!Array.isArray(values)) return [];
  return values
    .map((value) => repairMojibake(typeof value === 'string' ? value : ''))
    .filter((value) => value.trim().length > 0);
}
