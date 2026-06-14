export type RealEstateEvidenceItem = {
  evidenceItemId: string;
  evidenceType?: string | null;
  refType?: string | null;
  refId?: string | null;
  label: string;
  valueText?: string | null;
  severity?: string | null;
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
  return Array.isArray(payload.items) ? payload.items.filter(isEvidenceLog) : [];
}

function isEvidenceLog(item: RealEstateEvidenceLog): boolean {
  return typeof item.evidenceLogId === 'string'
    && item.evidenceLogId.trim().length > 0
    && typeof item.summary === 'string'
    && item.summary.trim().length > 0;
}
