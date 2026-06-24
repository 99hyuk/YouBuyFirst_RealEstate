export type RealEstateDailyBriefingSection = {
  sectionId: string;
  title: string;
  body: string;
  displayOrder: number;
};

export type RealEstateDailyBriefingFocusRegion = {
  targetId?: string | null;
  label: string;
  reason?: string | null;
  displayOrder?: number | null;
};

export type RealEstateDailyBriefingSourceItem = {
  sourceItemId: string;
  sourceType: string;
  refId?: string | null;
  label?: string | null;
  title: string;
  url?: string | null;
  displayOrder: number;
};

export type RealEstateDailyBriefing = {
  briefingId: string;
  briefingDate: string;
  title: string;
  summaryHeadlines: string[];
  sections: RealEstateDailyBriefingSection[];
  focusRegions: RealEstateDailyBriefingFocusRegion[];
  modelName?: string | null;
  promptVersion?: string | null;
  generatedAt: string;
  sourceItems: RealEstateDailyBriefingSourceItem[];
};

type Fetcher = (input: string) => Promise<Response>;

export async function fetchLatestRealEstateDailyBriefing(
  fetcher: Fetcher = fetch
): Promise<RealEstateDailyBriefing | null> {
  const response = await fetcher('/api/realestate/daily-briefings/latest');
  if (response.status === 204) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`real-estate daily briefing request failed: ${response.status}`);
  }
  const payload = await response.json() as Partial<RealEstateDailyBriefing>;
  if (!payload || !Array.isArray(payload.summaryHeadlines)) {
    return null;
  }
  return {
    briefingId: String(payload.briefingId ?? ''),
    briefingDate: String(payload.briefingDate ?? ''),
    title: String(payload.title ?? '오늘의 부동산 시장 브리핑'),
    summaryHeadlines: payload.summaryHeadlines.map((item) => String(item ?? '').trim()).filter(Boolean),
    sections: Array.isArray(payload.sections)
      ? payload.sections.map(normalizeSection).filter((section) => section.title && section.body)
      : [],
    focusRegions: Array.isArray(payload.focusRegions)
      ? payload.focusRegions.map(normalizeFocusRegion).filter((region) => region.label)
      : [],
    modelName: payload.modelName ?? null,
    promptVersion: payload.promptVersion ?? null,
    generatedAt: String(payload.generatedAt ?? ''),
    sourceItems: Array.isArray(payload.sourceItems)
      ? payload.sourceItems.map(normalizeSourceItem).filter((item) => item.title)
      : []
  };
}

function normalizeSection(section: Partial<RealEstateDailyBriefingSection>): RealEstateDailyBriefingSection {
  return {
    sectionId: String(section.sectionId ?? ''),
    title: String(section.title ?? ''),
    body: String(section.body ?? ''),
    displayOrder: Number(section.displayOrder ?? 100)
  };
}

function normalizeFocusRegion(region: Partial<RealEstateDailyBriefingFocusRegion>): RealEstateDailyBriefingFocusRegion {
  return {
    targetId: region.targetId ?? null,
    label: String(region.label ?? ''),
    reason: region.reason ?? null,
    displayOrder: Number(region.displayOrder ?? 100)
  };
}

function normalizeSourceItem(item: Partial<RealEstateDailyBriefingSourceItem>): RealEstateDailyBriefingSourceItem {
  return {
    sourceItemId: String(item.sourceItemId ?? ''),
    sourceType: String(item.sourceType ?? 'content'),
    refId: item.refId ?? null,
    label: item.label ?? null,
    title: String(item.title ?? ''),
    url: item.url ?? null,
    displayOrder: Number(item.displayOrder ?? 100)
  };
}
