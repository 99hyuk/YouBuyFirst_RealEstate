export type RecentRealEstateViewKind = 'region' | 'transaction';

export type RecentRealEstateView = {
  id: string;
  kind: RecentRealEstateViewKind;
  label: string;
  meta: string;
  href: string;
  visitedAt: number;
};

export type RecentRealEstateViewInput = Omit<RecentRealEstateView, 'visitedAt'> & {
  visitedAt?: number;
};

export const RECENT_REAL_ESTATE_VIEW_LIMIT = 15;
export const RECENT_REAL_ESTATE_VIEW_STORAGE_KEY = 'ybf-realestate-recent-views';
export const RECENT_REAL_ESTATE_VIEWS_CHANGED_EVENT = 'realestate:recent-views-changed';

type StorageLike = Pick<Storage, 'getItem' | 'setItem'>;

function browserStorage(): StorageLike | null {
  return typeof window === 'undefined' ? null : window.localStorage;
}

function normalizeRecentView(value: unknown): RecentRealEstateView | null {
  if (!value || typeof value !== 'object') return null;

  const source = value as Partial<RecentRealEstateView>;
  if (source.kind !== 'region' && source.kind !== 'transaction') return null;
  if (!source.id || !source.label || !source.href) return null;

  const visitedAt = Number(source.visitedAt);

  return {
    id: String(source.id),
    kind: source.kind,
    label: String(source.label),
    meta: source.meta ? String(source.meta) : (source.kind === 'region' ? '지역 분석' : '실거래'),
    href: String(source.href),
    visitedAt: Number.isFinite(visitedAt) ? visitedAt : 0
  };
}

export function loadRecentRealEstateViews(storage: StorageLike | null = browserStorage()): RecentRealEstateView[] {
  if (!storage) return [];

  try {
    const raw = storage.getItem(RECENT_REAL_ESTATE_VIEW_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) return [];

    return parsed
      .map(normalizeRecentView)
      .filter((item): item is RecentRealEstateView => Boolean(item))
      .sort((left, right) => right.visitedAt - left.visitedAt)
      .slice(0, RECENT_REAL_ESTATE_VIEW_LIMIT);
  } catch {
    return [];
  }
}

function persistRecentRealEstateViews(items: RecentRealEstateView[], storage: StorageLike | null): void {
  if (!storage) return;

  try {
    storage.setItem(RECENT_REAL_ESTATE_VIEW_STORAGE_KEY, JSON.stringify(items));
  } catch {
    // Recent views are a convenience cache; storage failures should not break navigation.
  }
}

function notifyRecentRealEstateViewsChanged(items: RecentRealEstateView[]): void {
  if (typeof window === 'undefined') return;

  window.dispatchEvent(new CustomEvent(RECENT_REAL_ESTATE_VIEWS_CHANGED_EVENT, { detail: items }));
}

export function recordRecentRealEstateView(
  input: RecentRealEstateViewInput,
  storage: StorageLike | null = browserStorage()
): RecentRealEstateView[] {
  const normalized = normalizeRecentView({
    ...input,
    visitedAt: input.visitedAt ?? Date.now()
  });
  if (!normalized) return loadRecentRealEstateViews(storage);

  const existing = loadRecentRealEstateViews(storage);
  const next = [
    normalized,
    ...existing.filter((item) => !(item.kind === normalized.kind && item.id === normalized.id))
  ].slice(0, RECENT_REAL_ESTATE_VIEW_LIMIT);

  persistRecentRealEstateViews(next, storage);
  notifyRecentRealEstateViewsChanged(next);

  return next;
}

export function subscribeRecentRealEstateViews(
  listener: (items: RecentRealEstateView[]) => void
): () => void {
  if (typeof window === 'undefined') return () => undefined;

  const refresh = () => listener(loadRecentRealEstateViews());
  const onStorage = (event: StorageEvent) => {
    if (event.key === RECENT_REAL_ESTATE_VIEW_STORAGE_KEY) {
      refresh();
    }
  };

  window.addEventListener(RECENT_REAL_ESTATE_VIEWS_CHANGED_EVENT, refresh);
  window.addEventListener('storage', onStorage);

  return () => {
    window.removeEventListener(RECENT_REAL_ESTATE_VIEWS_CHANGED_EVENT, refresh);
    window.removeEventListener('storage', onStorage);
  };
}
