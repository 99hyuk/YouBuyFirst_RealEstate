import { ref } from 'vue';

export type UserWatchTargetType = 'region' | 'complex';

export type UserWatchTarget = {
  watchId: string;
  targetType: UserWatchTargetType;
  targetId: string;
  displayName: string;
  landingPath: string;
  createdAt: string;
  updatedAt: string;
};

export type UserWatchTargetPayload = {
  targetType: UserWatchTargetType;
  targetId: string;
  displayName: string;
  landingPath: string;
};

export type UserWatchTargetLoadState = 'idle' | 'loading' | 'live' | 'empty' | 'unauthenticated' | 'error';

export const currentUserWatchTargets = ref<UserWatchTarget[]>([]);
export const userWatchTargetLoadState = ref<UserWatchTargetLoadState>('idle');

const jsonHeaders = {
  'Content-Type': 'application/json'
};

export const safeWatchTargetTestId = (value: string) => value.replace(/[^a-zA-Z0-9_-]/g, '-');

export function resetUserWatchTargets(state: UserWatchTargetLoadState = 'idle') {
  currentUserWatchTargets.value = [];
  userWatchTargetLoadState.value = state;
}

export function findUserWatchTarget(targetType: UserWatchTargetType, targetId: string): UserWatchTarget | null {
  return currentUserWatchTargets.value.find(
    (target) => target.targetType === targetType && target.targetId === targetId
  ) ?? null;
}

export function isUserWatchTargetSaved(targetType: UserWatchTargetType, targetId: string): boolean {
  return Boolean(findUserWatchTarget(targetType, targetId));
}

export async function loadUserWatchTargets(fetcher: typeof fetch = fetch): Promise<UserWatchTarget[]> {
  userWatchTargetLoadState.value = 'loading';
  const response = await fetcher('/api/realestate/watch-targets', {
    credentials: 'include'
  });

  if (response.status === 401) {
    resetUserWatchTargets('unauthenticated');
    return [];
  }

  if (!response.ok) {
    resetUserWatchTargets('error');
    throw new Error('관심 목록을 불러오지 못했습니다.');
  }

  const payload = await response.json() as { items?: UserWatchTarget[] };
  const items = Array.isArray(payload.items) ? payload.items : [];
  currentUserWatchTargets.value = items;
  userWatchTargetLoadState.value = items.length ? 'live' : 'empty';
  return items;
}

export async function saveUserWatchTarget(
  payload: UserWatchTargetPayload,
  fetcher: typeof fetch = fetch
): Promise<UserWatchTarget> {
  const response = await fetcher('/api/realestate/watch-targets', {
    body: JSON.stringify(payload),
    credentials: 'include',
    headers: jsonHeaders,
    method: 'POST'
  });

  if (response.status === 401) {
    resetUserWatchTargets('unauthenticated');
    throw new Error('로그인이 필요합니다.');
  }

  if (!response.ok) {
    throw new Error('관심 대상을 저장하지 못했습니다.');
  }

  const saved = await response.json() as UserWatchTarget;
  currentUserWatchTargets.value = [
    saved,
    ...currentUserWatchTargets.value.filter(
      (target) => !(target.targetType === saved.targetType && target.targetId === saved.targetId)
    )
  ];
  userWatchTargetLoadState.value = 'live';
  return saved;
}

export async function removeUserWatchTarget(
  targetType: UserWatchTargetType,
  targetId: string,
  fetcher: typeof fetch = fetch
): Promise<void> {
  const params = new URLSearchParams({ targetType, targetId });
  const response = await fetcher(`/api/realestate/watch-targets?${params.toString()}`, {
    credentials: 'include',
    method: 'DELETE'
  });

  if (response.status === 401) {
    resetUserWatchTargets('unauthenticated');
    throw new Error('로그인이 필요합니다.');
  }

  if (!response.ok) {
    throw new Error('관심 대상을 해제하지 못했습니다.');
  }

  currentUserWatchTargets.value = currentUserWatchTargets.value.filter(
    (target) => !(target.targetType === targetType && target.targetId === targetId)
  );
  userWatchTargetLoadState.value = currentUserWatchTargets.value.length ? 'live' : 'empty';
}
