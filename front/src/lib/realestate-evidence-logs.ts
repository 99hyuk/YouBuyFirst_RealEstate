import { repairMojibake } from './text-encoding';

export type RealEstateEvidenceItem = {
  evidenceItemId: string;
  evidenceType?: string | null;
  refType?: string | null;
  refId?: string | null;
  label: string;
  valueText?: string | null;
  severity?: string | null;
  sourceUrl?: string | null;
  sourceId?: string | null;
  sourceDomain?: string | null;
  publishedAt?: string | null;
  sourceAsOf?: string | null;
  sourceDataStatus?: string | null;
};

export type RealEstateEvidenceLog = {
  evidenceLogId: string;
  targetId?: string | null;
  snapshotId?: number | null;
  evaluationVersion?: string | null;
  promptVersion?: string | null;
  modelName?: string | null;
  tone?: string | null;
  summary: string;
  subtitle?: string | null;
  caveats?: string[] | null;
  dataQuality?: string | null;
  confidence?: number | null;
  skipReason?: string | null;
  evaluatedAt?: string | null;
  asOf?: string | null;
  evidenceItems?: RealEstateEvidenceItem[] | null;
};

export type FetchRealEstateTargetEvidenceLogsParams = {
  limit?: number;
};

type Fetcher = (input: string) => Promise<Response>;

export async function fetchRealEstateTargetEvidenceLogs(
  targetId: string,
  params: FetchRealEstateTargetEvidenceLogsParams = {},
  fetcher: Fetcher = fetch
): Promise<RealEstateEvidenceLog[]> {
  const query = new URLSearchParams();
  query.set('limit', String(params.limit ?? 10));

  const response = await fetcher(`/api/realestate/targets/${encodeURIComponent(targetId)}/evidence-logs?${query.toString()}`);
  if (!response.ok) {
    throw new Error(`real-estate target evidence logs request failed: ${response.status}`);
  }

  const payload = await response.json() as { items?: RealEstateEvidenceLog[] };
  return Array.isArray(payload.items) ? payload.items.map(normalizeEvidenceLog).filter(isEvidenceLog) : [];
}

function isEvidenceLog(item: RealEstateEvidenceLog): boolean {
  return typeof item.evidenceLogId === 'string'
    && item.evidenceLogId.trim().length > 0
    && typeof item.summary === 'string'
    && item.summary.trim().length > 0;
}

function normalizeEvidenceLog(item: RealEstateEvidenceLog): RealEstateEvidenceLog {
  return {
    ...item,
    targetId: repairMojibake(item.targetId),
    evaluationVersion: repairMojibake(item.evaluationVersion),
    promptVersion: repairMojibake(item.promptVersion),
    modelName: repairMojibake(item.modelName),
    tone: repairMojibake(item.tone),
    summary: repairMojibake(item.summary),
    subtitle: repairMojibake(item.subtitle),
    caveats: Array.isArray(item.caveats) ? item.caveats.map(repairMojibake) : item.caveats,
    dataQuality: repairMojibake(item.dataQuality),
    skipReason: repairMojibake(item.skipReason),
    evidenceItems: Array.isArray(item.evidenceItems) ? item.evidenceItems.map(normalizeEvidenceItem) : item.evidenceItems
  };
}

function normalizeEvidenceItem(item: RealEstateEvidenceItem): RealEstateEvidenceItem {
  return {
    ...item,
    evidenceType: repairMojibake(item.evidenceType),
    refType: repairMojibake(item.refType),
    label: repairMojibake(item.label),
    valueText: repairMojibake(item.valueText),
    severity: repairMojibake(item.severity),
    sourceId: repairMojibake(item.sourceId),
    sourceDomain: repairMojibake(item.sourceDomain),
    sourceDataStatus: repairMojibake(item.sourceDataStatus)
  };
}
