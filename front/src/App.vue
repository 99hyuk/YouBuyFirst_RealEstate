<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import {
  fetchRealEstateReactionRankingWithFallback,
  type RealEstateReactionRankingItem
} from './lib/realestate-reactions';
import { currentAuthUser, loadCurrentUser, logout } from './lib/auth-session';
import {
  buildNewsroomFeedItems,
  fetchRealEstateNewsroom,
  type RealEstateContentItem,
  type NewsroomFeedItem
} from './lib/realestate-content';
import {
  currentMonth,
  fetchMarketDataSchedules,
  type MarketDataScheduleEvent
} from './lib/realestate-schedules';
import {
  fetchRealEstateMapLayer,
  type PeriodKey,
  type RealEstateMapLayerTarget
} from './lib/realestate-map';
import {
  subscribeRealEstateBatchUpdates,
  type BatchUpdateSubscription,
  type RealEstateBatchUpdateEvent
} from './lib/realestate-batch-updates';
import {
  loadRecentRealEstateViews,
  subscribeRecentRealEstateViews,
  type RecentRealEstateView
} from './lib/realestate-recent-views';
import {
  currentUserWatchTargets,
  loadUserWatchTargets,
  removeUserWatchTarget,
  resetUserWatchTargets,
  safeWatchTargetTestId,
  userWatchTargetLoadState,
  type UserWatchTarget
} from './lib/user-watch-targets';

type RailItem = {
  id: 'watch' | 'recent' | 'chat';
  label: string;
  shortcut?: string;
  icon?: 'chat';
};

const railItems: RailItem[] = [
  { id: 'watch', label: '관심', shortcut: 'W' },
  { id: 'recent', label: '최근 본', shortcut: 'R' },
  { id: 'chat', label: '채팅', icon: 'chat' }
];

const activeRailItem = ref('chat');
const railExpanded = ref(true);
const newsroomMenuDismissed = ref(false);
const shellRankingItems = ref<RealEstateReactionRankingItem[]>([]);
const shellReactionState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const shellTickerItems = ref<ShellTickerItem[]>([]);
const shellTickerState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');
const authState = ref<'checking' | 'guest' | 'authenticated'>('checking');
const edgeChatDraft = ref('');
const edgeChatDraftAttachment = ref<ChatAttachment | null>(null);
const edgeChatParticipantCount = ref(1);
const edgeChatPresenceState = ref<'loading' | 'live' | 'error'>('loading');
const edgeChatFontLevel = ref(5);
let edgeChatPresenceTimer: number | null = null;
let edgeChatMessageStream: EventSource | null = null;
const chatInputRef = ref<HTMLTextAreaElement | null>(null);
const edgeChatFeedRef = ref<HTMLDivElement | null>(null);
const edgeChatNicknameInputRef = ref<HTMLInputElement | null>(null);
const edgeChatGuestNameInputRef = ref<HTMLInputElement | null>(null);
const edgeChatNicknameDraft = ref('');
const edgeChatNicknamePopoverOpen = ref(false);
const edgeChatNicknameOverride = ref<{ userId: string; displayName: string } | null>(null);
const edgeChatGuestDisplayName = ref('');
const edgeChatGuestNameDraft = ref('');
const edgeChatGuestNameError = ref('');
const edgeChatGuestNameChecking = ref(false);
const edgeChatGuestJoinMode = ref<'choice' | 'nickname'>('choice');
const recentViews = ref<RecentRealEstateView[]>(loadRecentRealEstateViews());
const route = useRoute();
const router = useRouter();
const authUser = currentAuthUser;
const activeRailLabel = computed(() => railItems.find((item) => item.id === activeRailItem.value)?.label ?? '관심');
const newsroomFeeds = [
  { label: '뉴스', feed: 'news' },
  { label: '리포트', feed: 'reports' },
  { label: '영상', feed: 'videos' },
  { label: '블로그·커뮤니티', feed: 'links' }
];
const activeNewsroomFeed = computed(() => {
  if (route.path !== '/newsroom') return '';
  const feed = route.query.feed;
  return Array.isArray(feed) ? feed[0] ?? '' : feed ?? '';
});

const loadShellSignals = async () => {
  shellReactionState.value = 'loading';
  try {
    const ranking = await fetchRealEstateReactionRankingWithFallback({ type: 'region', windowMinutes: 10080, limit: 6 });
    shellRankingItems.value = ranking.items;
    shellReactionState.value = ranking.items.length ? 'live' : 'empty';
  } catch {
    shellRankingItems.value = [];
    shellReactionState.value = 'error';
  }
};

type ShellTickerTone = 'news' | 'schedule' | 'up' | 'down' | 'state';

type ShellTickerItem = {
  id: string;
  label: string;
  text: string;
  tone: ShellTickerTone;
  score: number;
};

type ChatAttachment = {
  type: 'region' | 'complex';
  targetId: string;
  title: string;
  subtitle: string;
  metricLabel?: string;
  metricValue?: string;
  metricTone?: 'up' | 'down' | 'flat';
  landingPath: string;
};

type EdgeChatMessage = {
  id: string;
  author: string;
  badge: string;
  body: string;
  timeLabel: string;
  category: EdgeChatCategory;
  mine?: boolean;
  tone?: 'orange' | 'green' | 'blue' | 'red' | 'purple';
  verified?: boolean;
  attachment?: ChatAttachment | null;
};

type EdgeChatCategory = 'system' | 'chat' | 'news';

type ChatPresenceResponse = {
  activeSessionCount?: number;
  source?: string;
};

type ChatNicknameAvailabilityResponse = {
  available?: boolean;
};

type ChatMessageResponse = {
  id: string;
  author: string;
  badge?: string;
  body: string;
  timeLabel?: string;
  category?: EdgeChatCategory;
  mine?: boolean;
  tone?: EdgeChatMessage['tone'];
  verified?: boolean;
  createdAt?: string;
  attachment?: ChatAttachment | null;
};

const edgeChatSeedMessages: EdgeChatMessage[] = [
  {
    id: 'chat-welcome',
    author: '전체채팅',
    badge: '안내',
    body: '너나사 부동산 채팅에 오신 걸 환영합니다. 지역 분석과 실거래를 첨부해 함께 이야기할 수 있습니다.',
    timeLabel: '방금',
    category: 'system',
    tone: 'blue'
  },
  {
    id: 'chat-sample-1',
    author: '서울전세관찰',
    badge: '관망',
    body: '오늘 전세 매물 흐름 다시 봐야겠네요',
    timeLabel: '1분 전',
    category: 'chat',
    tone: 'orange',
    verified: true
  },
  {
    id: 'chat-sample-2',
    author: '세종살이',
    badge: '관련',
    body: '세종 실거래 지도랑 같이 보면 좋겠다',
    timeLabel: '방금',
    category: 'chat',
    tone: 'green',
    verified: true
  },
  {
    id: 'chat-sample-3',
    author: '마포체크',
    badge: '관망',
    body: '마포는 거래량이랑 전세를 같이 봐야 할 듯',
    timeLabel: '방금',
    category: 'chat',
    tone: 'purple',
    verified: true
  }
];

const EDGE_CHAT_VISIBLE_LIMIT = 100;
const edgeChatMessages = ref<EdgeChatMessage[]>([...edgeChatSeedMessages]);

const tickerContentPageSize = 12;
const tickerContentLimit = 4;
const tickerScheduleLimit = 2;
const tickerTotalLimit = 8;
const shellTickerRefreshTopics = new Set(['newsroom', 'market-data-schedules', 'map-layers']);
let shellTickerBatchUpdateSubscription: BatchUpdateSubscription | null = null;
let recentViewsUnsubscribe: (() => void) | null = null;

const loadShellTicker = async () => {
  shellTickerState.value = 'loading';
  const [newsroomResult, schedulesResult, mapLayerResult] = await Promise.allSettled([
    fetchRealEstateNewsroom({ feed: 'news', page: 1, pageSize: tickerContentPageSize }),
    fetchMarketDataSchedules({ month: currentMonth() }),
    fetchRealEstateMapLayer({ layerType: 'sido' })
  ]);

  const items: ShellTickerItem[] = [];

  if (newsroomResult.status === 'fulfilled') {
    items.push(...buildContentTickerItems(newsroomResult.value));
  }
  if (schedulesResult.status === 'fulfilled') {
    items.push(...buildScheduleTickerItems(schedulesResult.value.scheduleEvents));
  }
  if (mapLayerResult.status === 'fulfilled') {
    items.push(...buildMovementTickerItems(mapLayerResult.value.targets));
  }

  shellTickerItems.value = rankShellTickerItems(items).slice(0, tickerTotalLimit);
  shellTickerState.value = shellTickerItems.value.length ? 'live' : 'empty';

  if (newsroomResult.status === 'rejected' && schedulesResult.status === 'rejected' && mapLayerResult.status === 'rejected') {
    shellTickerState.value = 'error';
  }
};

const handleShellTickerBatchUpdate = (event: RealEstateBatchUpdateEvent) => {
  if (!shellTickerRefreshTopics.has(event.topic)) return;
  if (event.topic === 'market-data-schedules' && event.month && event.month !== currentMonth()) return;

  void loadShellTicker();
};

const loadAuthState = async () => {
  authState.value = 'checking';
  try {
    const user = await loadCurrentUser();
    authState.value = user ? 'authenticated' : 'guest';
    if (user) {
      try {
        await loadUserWatchTargets();
      } catch {
        // 관심 목록 장애가 로그인 상태 자체를 guest로 떨어뜨리면 화면 전체가 흔들린다.
      }
    } else {
      resetUserWatchTargets('unauthenticated');
    }
  } catch {
    currentAuthUser.value = null;
    authState.value = 'guest';
    resetUserWatchTargets('error');
  }
};

const loadEdgeChatPresence = async () => {
  edgeChatPresenceState.value = 'loading';
  try {
    const response = await fetch('/api/chat/presence', {
      credentials: 'include'
    });
    if (!response.ok) {
      throw new Error('chat presence request failed');
    }
    const payload = await response.json() as ChatPresenceResponse;
    edgeChatParticipantCount.value = Math.max(1, Number(payload.activeSessionCount ?? 0));
    edgeChatPresenceState.value = 'live';
  } catch {
    edgeChatParticipantCount.value = Math.max(1, edgeChatParticipantCount.value);
    edgeChatPresenceState.value = 'error';
  }
};

const CHAT_ATTACH_EVENT = 'ybf-chat-attach';

const stringValue = (value: unknown): string | undefined => {
  if (typeof value !== 'string') return undefined;
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
};

const normalizeChatAttachment = (value: unknown): ChatAttachment | null => {
  if (!value || typeof value !== 'object') return null;
  const source = value as Record<string, unknown>;
  const type = source.type === 'region' || source.type === 'complex' ? source.type : null;
  const targetId = stringValue(source.targetId);
  const title = stringValue(source.title);
  const subtitle = stringValue(source.subtitle);
  const landingPath = stringValue(source.landingPath);
  if (!type || !targetId || !title || !subtitle || !landingPath || !landingPath.startsWith('/realestate/')) {
    return null;
  }

  const rawMetricTone = source.metricTone;
  const metricTone = rawMetricTone === 'up' || rawMetricTone === 'down' || rawMetricTone === 'flat'
    ? rawMetricTone
    : undefined;

  return {
    type,
    targetId,
    title,
    subtitle,
    metricLabel: stringValue(source.metricLabel),
    metricValue: stringValue(source.metricValue),
    metricTone,
    landingPath
  };
};

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const chatAttachmentKindLabel = (attachment: ChatAttachment) => attachment.type === 'complex' ? '실거래' : '지역 분석';
const normalizeAttachmentDisplayText = (value?: string) => (value ?? '').replace(/\s+/g, ' ').trim();
const chatAttachmentCompactDetail = (attachment: ChatAttachment) => {
  const kind = chatAttachmentKindLabel(attachment);
  const compactKind = kind.replace(/\s+/g, '');
  const prefixPattern = new RegExp(`^(${escapeRegExp(kind)}|${escapeRegExp(compactKind)})\\s*(첨부)?\\s*[·:|-]?\\s*`);
  const detail = attachment.subtitle.replace(prefixPattern, '').trim();

  return detail || attachment.subtitle;
};
const shouldShowChatAttachmentDetail = (attachment: ChatAttachment) => {
  const detail = normalizeAttachmentDisplayText(chatAttachmentCompactDetail(attachment));
  const metricLabel = normalizeAttachmentDisplayText(attachment.metricLabel);

  return Boolean(detail && (!attachment.metricValue || !metricLabel || detail !== metricLabel));
};
const chatAttachmentMetricDisplayLabel = (attachment: ChatAttachment) => {
  const metricLabel = normalizeAttachmentDisplayText(attachment.metricLabel);
  const readableLabels: Record<string, string> = {
    MoM: '최근 1개월',
    '6개월': '최근 6개월',
    YoY: '최근 1년'
  };

  return readableLabels[metricLabel] ?? metricLabel;
};
const chatAttachmentMetricLabelText = (attachment: ChatAttachment) =>
  chatAttachmentMetricDisplayLabel(attachment) ? `${chatAttachmentMetricDisplayLabel(attachment)} ` : '';

const mapChatMessageResponse = (message: ChatMessageResponse): EdgeChatMessage => ({
  id: message.id,
  author: message.author,
  badge: message.badge ?? '채팅',
  body: message.body,
  timeLabel: message.timeLabel ?? '방금',
  category: message.category === 'news' || message.category === 'system' ? message.category : 'chat',
  mine: Boolean(message.mine),
  tone: message.tone ?? 'blue',
  verified: Boolean(message.verified),
  attachment: normalizeChatAttachment(message.attachment)
});

const scrollEdgeChatToBottom = async () => {
  await nextTick();
  const feed = edgeChatFeedRef.value;
  if (!feed) return;
  feed.scrollTop = feed.scrollHeight;
};

const setEdgeChatMessages = (messages: EdgeChatMessage[]) => {
  edgeChatMessages.value = messages.slice(-EDGE_CHAT_VISIBLE_LIMIT);
  void scrollEdgeChatToBottom();
};

const upsertEdgeChatMessage = (message: ChatMessageResponse) => {
  const nextMessage = mapChatMessageResponse(message);
  const existing = edgeChatMessages.value.find((item) => item.id === nextMessage.id);
  setEdgeChatMessages([
    ...edgeChatMessages.value.filter((item) => item.id !== nextMessage.id),
    {
      ...nextMessage,
      mine: Boolean(existing?.mine || nextMessage.mine)
    }
  ]);
};

const loadEdgeChatMessages = async () => {
  try {
    const response = await fetch(`/api/chat/messages?limit=${EDGE_CHAT_VISIBLE_LIMIT}`, {
      credentials: 'include'
    });
    if (!response.ok) {
      throw new Error('chat messages request failed');
    }
    const payload = await response.json() as ChatMessageResponse[];
    setEdgeChatMessages([
      ...edgeChatSeedMessages,
      ...payload.map(mapChatMessageResponse)
    ]);
  } catch {
    if (!edgeChatMessages.value.length) {
      setEdgeChatMessages([...edgeChatSeedMessages]);
    }
  }
};

const startEdgeChatMessageStream = () => {
  if (edgeChatMessageStream || typeof EventSource === 'undefined') return;

  edgeChatMessageStream = new EventSource('/api/chat/messages/stream');
  edgeChatMessageStream.addEventListener('chat-message', (event) => {
    try {
      upsertEdgeChatMessage(JSON.parse(event.data) as ChatMessageResponse);
    } catch {
      void loadEdgeChatMessages();
    }
  });
  edgeChatMessageStream.onerror = () => {
    void loadEdgeChatMessages();
  };
};

const stopEdgeChatMessageStream = () => {
  if (!edgeChatMessageStream) return;
  edgeChatMessageStream.close();
  edgeChatMessageStream = null;
};

const refreshEdgeChatServerState = () => {
  void loadEdgeChatPresence();
  void loadEdgeChatMessages();
};

const startEdgeChatPresence = () => {
  refreshEdgeChatServerState();
  startEdgeChatMessageStream();
  if (edgeChatPresenceTimer !== null) return;
  edgeChatPresenceTimer = window.setInterval(refreshEdgeChatServerState, 5000);
};

const stopEdgeChatPresence = () => {
  stopEdgeChatMessageStream();
  if (edgeChatPresenceTimer === null) return;
  window.clearInterval(edgeChatPresenceTimer);
  edgeChatPresenceTimer = null;
};

onMounted(() => {
  recentViews.value = loadRecentRealEstateViews();
  recentViewsUnsubscribe = subscribeRecentRealEstateViews((items) => {
    recentViews.value = items;
  });
  void loadShellSignals();
  void loadShellTicker();
  void loadAuthState();
  if (railExpanded.value && activeRailItem.value === 'chat') {
    startEdgeChatPresence();
  }
  shellTickerBatchUpdateSubscription = subscribeRealEstateBatchUpdates(handleShellTickerBatchUpdate);
  window.addEventListener(CHAT_ATTACH_EVENT, handleChatAttachmentEvent);
});

onBeforeUnmount(() => {
  stopEdgeChatPresence();
  window.removeEventListener(CHAT_ATTACH_EVENT, handleChatAttachmentEvent);
  shellTickerBatchUpdateSubscription?.close();
  shellTickerBatchUpdateSubscription = null;
  recentViewsUnsubscribe?.();
  recentViewsUnsubscribe = null;
});

const shellStatusLabel = computed(() => {
  if (shellReactionState.value === 'live') return '시장 흐름 반영';
  if (shellReactionState.value === 'loading') return '시장 흐름 확인 중';
  if (shellReactionState.value === 'empty') return '시장 데이터 확인 전';
  return '시장 흐름 확인 필요';
});

const activePanelBadgeLabel = computed(() => {
  if (activeRailItem.value === 'recent') {
    return recentViews.value.length ? `최근 ${recentViews.value.length}개` : '비어 있음';
  }
  if (activeRailItem.value === 'watch') {
    if (authState.value === 'checking') return '로그인 확인 중';
    if (!authUser.value) return '로그인 필요';
    if (userWatchTargetLoadState.value === 'loading') return '관심 확인 중';
    return currentUserWatchTargets.value.length ? `관심 ${currentUserWatchTargets.value.length}개` : '비어 있음';
  }
  if (activeRailItem.value !== 'chat') return shellStatusLabel.value;
  if (authState.value === 'checking') return '로그인 확인 중';
  return edgeChatGuestDisplayName.value || authUser.value?.displayName || '채팅 참여';
});

const isEdgeChatParticipant = computed(() => Boolean(authUser.value || edgeChatGuestDisplayName.value));
const showGuestChatGate = computed(() => !authUser.value && !edgeChatGuestDisplayName.value);
const canPostChat = computed(() => Boolean(isEdgeChatParticipant.value && edgeChatDraft.value.trim()));
const edgeChatParticipantLabel = computed(() =>
  edgeChatPresenceState.value === 'loading'
    ? '확인중'
    : edgeChatParticipantCount.value.toLocaleString('ko-KR')
);
const edgeChatDisplayName = computed(() => {
  const user = authUser.value;
  if (!user) return edgeChatGuestDisplayName.value || '손님';

  const override = edgeChatNicknameOverride.value;
  if (override?.userId === user.id) return override.displayName;

  return user.displayName;
});
const canSaveEdgeChatNickname = computed(() =>
  Boolean(isEdgeChatParticipant.value && edgeChatNicknameDraft.value.trim() && !edgeChatGuestNameChecking.value)
);
const canSaveGuestChatName = computed(() => Boolean(edgeChatGuestNameDraft.value.trim() && !edgeChatGuestNameChecking.value));
const edgeChatRoomStyle = computed(() => ({
  '--edge-chat-font-scale': (1 + ((edgeChatFontLevel.value - 5) * 0.06)).toFixed(2)
}));
const filteredEdgeChatMessages = computed(() => edgeChatMessages.value.filter((message) => message.category !== 'news'));
const EDGE_CHAT_AUTHOR_TONE_COUNT = 12;
const edgeChatAuthorToneClass = (author?: string) => {
  const normalizedAuthor = author?.trim() || 'guest';
  let hash = 0;
  for (const char of normalizedAuthor) {
    hash = ((hash * 31) + (char.codePointAt(0) ?? 0)) >>> 0;
  }

  return `edge-chat-author-tone-${hash % EDGE_CHAT_AUTHOR_TONE_COUNT}`;
};
const edgeChatDisplayToneClass = computed(() => edgeChatAuthorToneClass(edgeChatDisplayName.value));
const hasEdgeChatDisplayAnimation = computed(() => Boolean(isEdgeChatParticipant.value && edgeChatDisplayName.value.trim()));
const isEdgeChatVerifiedMessage = (message: EdgeChatMessage) =>
  Boolean(message.verified || (message.mine && authUser.value));
const hasEdgeChatAuthorAnimation = (message: EdgeChatMessage) =>
  message.category === 'chat' && Boolean(message.author.trim());

const liveTopics = computed(() => {
  if (!shellTickerItems.value.length) {
    return [
      {
        id: 'ticker-state',
        label: shellTickerState.value === 'loading' ? '확인' : '상태',
        tone: 'state' as ShellTickerTone,
        text: shellTickerState.value === 'error'
          ? '오늘 뉴스 확인 필요'
          : '오늘 뉴스 확인 중'
      }
    ];
  }

  return shellTickerItems.value;
});

const watchTargets = computed(() => currentUserWatchTargets.value);
const watchTargetTestId = (target: UserWatchTarget) =>
  `edge-watch-${target.targetType}-${safeWatchTargetTestId(target.targetId)}`;
const watchTargetRemoveTestId = (target: UserWatchTarget) =>
  `edge-watch-remove-${target.targetType}-${safeWatchTargetTestId(target.targetId)}`;
const watchTargetInitial = (target: UserWatchTarget) => target.targetType === 'complex' ? '실' : '지';
const watchTargetTypeLabel = (target: UserWatchTarget) => target.targetType === 'complex' ? '실거래' : '지역 분석';
const recentViewTestId = (view: RecentRealEstateView) => `recent-view-${view.kind}-${view.id}`;
const recentViewInitial = (view: RecentRealEstateView) => view.kind === 'transaction' ? '실' : '지';

function buildContentTickerItems(contentItems: RealEstateContentItem[]): ShellTickerItem[] {
  const todayKey = kstDateKey(new Date());
  const displayItems = buildNewsroomFeedItems(contentItems);
  const sourceById = new Map(contentItems.map((item) => [item.contentId, item]));

  const tickerItems: Array<ShellTickerItem | null> = displayItems.map((item) => {
    const source = sourceById.get(item.id);
    const publishedAt = source?.publishedAt ?? null;

    if (item.category !== 'news') return null;
    if (!isSameKstDate(publishedAt, todayKey)) return null;
    if (isLowValueTickerNews(item, source)) return null;

    return {
      id: `content-${item.id}`,
      label: '뉴스',
      text: item.title,
      tone: 'news',
      score: timestampValue(publishedAt)
    } satisfies ShellTickerItem;
  });

  return tickerItems
    .filter((item): item is ShellTickerItem => Boolean(item))
    .sort((left, right) => right.score - left.score)
    .slice(0, tickerContentLimit);
}

function buildScheduleTickerItems(events: MarketDataScheduleEvent[]): ShellTickerItem[] {
  const todayKey = kstDateKey(new Date());

  return events
    .filter((event) => {
      const eventDateKey = kstDateKey(event.date);
      return Boolean(eventDateKey && todayKey && eventDateKey >= todayKey && !event.stale);
    })
    .map((event) => ({
      id: `schedule-${event.id}`,
      label: '일정',
      text: `${formatScheduleDate(event.date)} ${event.title}`,
      tone: 'schedule',
      score: 3_000_000_000_000 - timestampValue(event.date)
    } satisfies ShellTickerItem))
    .sort((left, right) => right.score - left.score)
    .slice(0, tickerScheduleLimit);
}

function buildMovementTickerItems(targets: RealEstateMapLayerTarget[]): ShellTickerItem[] {
  const movements = targets
    .map((target) => {
      const period = latestUsablePeriod(target);
      return period ? { target, changePct: period.changePct, asOf: timestampValue(period.asOf) } : null;
    })
    .filter((item): item is { target: RealEstateMapLayerTarget; changePct: number; asOf: number } => Boolean(item));
  const highestGain = movements.filter((item) => item.changePct > 0).sort((left, right) => right.changePct - left.changePct)[0];
  const largestDrop = movements.filter((item) => item.changePct < 0).sort((left, right) => left.changePct - right.changePct)[0];

  const tickerItems: Array<ShellTickerItem | null> = [
    highestGain
      ? {
          id: `movement-up-${highestGain.target.targetId}`,
          label: '상승',
          text: `${highestGain.target.displayName} ${formatPct(highestGain.changePct)}`,
          tone: 'up',
          score: highestGain.asOf + Math.abs(highestGain.changePct) * 100
        } satisfies ShellTickerItem
      : null,
    largestDrop
      ? {
          id: `movement-down-${largestDrop.target.targetId}`,
          label: '하락',
          text: `${largestDrop.target.displayName} ${formatPct(largestDrop.changePct)}`,
          tone: 'down',
          score: largestDrop.asOf + Math.abs(largestDrop.changePct) * 100
        } satisfies ShellTickerItem
      : null
  ];

  return tickerItems.filter((item): item is ShellTickerItem => Boolean(item));
}

function rankShellTickerItems(items: ShellTickerItem[]): ShellTickerItem[] {
  const seen = new Set<string>();

  return items
    .sort((left, right) => right.score - left.score)
    .filter((item) => {
      const key = `${item.label}:${item.text}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

function isLowValueTickerNews(item: NewsroomFeedItem, source?: RealEstateContentItem): boolean {
  const searchable = `${item.title} ${source?.snippet ?? ''} ${source?.metricLabel ?? ''}`.toLowerCase();
  return /이벤트|할인|제휴|프로모션|광고|브랜드|수상|채용|앱 출시|해외사업|온도차|실적/.test(searchable);
}

function latestUsablePeriod(target: RealEstateMapLayerTarget) {
  const periodOrder: PeriodKey[] = ['week', 'month', 'quarter', 'halfYear', 'year'];
  return periodOrder
    .map((period) => target.periods[period])
    .find((period) => period && period.dataStatus !== 'mock' && !period.stale) ?? null;
}

function timestampValue(value?: string | null): number {
  if (!value) return 0;
  const parsed = new Date(value).getTime();
  return Number.isFinite(parsed) ? parsed : 0;
}

function isSameKstDate(value: string | null, expectedDateKey: string | null): boolean {
  return Boolean(value && expectedDateKey && kstDateKey(value) === expectedDateKey);
}

function kstDateKey(value: Date | string | null | undefined): string | null {
  if (!value) return null;
  const parsed = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;

  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).formatToParts(parsed);
  const year = parts.find((part) => part.type === 'year')?.value;
  const month = parts.find((part) => part.type === 'month')?.value;
  const day = parts.find((part) => part.type === 'day')?.value;

  return year && month && day ? `${year}-${month}-${day}` : null;
}

function formatScheduleDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat('ko-KR', { month: '2-digit', day: '2-digit' }).format(parsed);
}

function formatPct(value: number): string {
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
}

const openRail = (id: string) => {
  activeRailItem.value = id;
  railExpanded.value = true;
  if (id === 'chat') {
    startEdgeChatPresence();
    void scrollEdgeChatToBottom();
    return;
  }
  stopEdgeChatPresence();
  if (id === 'watch' && authUser.value) {
    void loadUserWatchTargets();
  }
};

const toggleRail = () => {
  railExpanded.value = !railExpanded.value;
  if (railExpanded.value && activeRailItem.value === 'chat') {
    startEdgeChatPresence();
    void scrollEdgeChatToBottom();
  } else {
    stopEdgeChatPresence();
  }
};

const clearEdgeChatDraftAttachment = () => {
  edgeChatDraftAttachment.value = null;
};

const decreaseEdgeChatFont = () => {
  edgeChatFontLevel.value = Math.max(1, edgeChatFontLevel.value - 1);
};

const increaseEdgeChatFont = () => {
  edgeChatFontLevel.value = Math.min(9, edgeChatFontLevel.value + 1);
};

const handleChatAttachmentEvent = async (event: Event) => {
  const attachment = normalizeChatAttachment((event as CustomEvent).detail);
  if (!attachment) return;

  edgeChatDraftAttachment.value = attachment;
  openRail('chat');
  await nextTick();
  chatInputRef.value?.focus();
};

const openChatNicknameSettings = async () => {
  if (!isEdgeChatParticipant.value) {
    await openGuestChatNameForm();
    return;
  }

  edgeChatGuestNameError.value = '';
  edgeChatNicknameDraft.value = edgeChatDisplayName.value;
  edgeChatNicknamePopoverOpen.value = true;
  await nextTick();
  edgeChatNicknameInputRef.value?.focus();
  edgeChatNicknameInputRef.value?.select();
};

const closeChatNicknameSettings = () => {
  edgeChatGuestNameError.value = '';
  edgeChatNicknamePopoverOpen.value = false;
};

const checkGuestChatDisplayNameAvailability = async (displayName: string) => {
  if (edgeChatGuestNameChecking.value) return false;

  edgeChatGuestNameError.value = '';
  edgeChatGuestNameChecking.value = true;
  try {
    const response = await fetch(`/api/chat/nickname-availability?displayName=${encodeURIComponent(displayName)}`, {
      credentials: 'include'
    });
    if (response.status === 409) {
      edgeChatGuestNameError.value = '이미 가입자가 사용 중인 닉네임이에요.';
      return false;
    }
    if (!response.ok) {
      throw new Error('guest chat nickname availability request failed');
    }
    const payload = await response.json() as ChatNicknameAvailabilityResponse;
    if (!payload.available) {
      edgeChatGuestNameError.value = '이미 가입자가 사용 중인 닉네임이에요.';
      return false;
    }
    return true;
  } catch {
    edgeChatGuestNameError.value = '닉네임을 확인하지 못했어요. 잠시 후 다시 시도해주세요.';
    return false;
  } finally {
    edgeChatGuestNameChecking.value = false;
  }
};

const saveChatNicknameSettings = async () => {
  if (!isEdgeChatParticipant.value) return;

  const displayName = edgeChatNicknameDraft.value.trim();
  if (!displayName) return;

  if (authUser.value) {
    edgeChatNicknameOverride.value = {
      userId: authUser.value.id,
      displayName
    };
  } else {
    const available = await checkGuestChatDisplayNameAvailability(displayName);
    if (!available) return;
    edgeChatGuestDisplayName.value = displayName;
  }
  edgeChatNicknamePopoverOpen.value = false;
};

const openGuestChatNameForm = async () => {
  edgeChatGuestJoinMode.value = 'nickname';
  edgeChatGuestNameDraft.value = edgeChatGuestDisplayName.value;
  edgeChatGuestNameError.value = '';
  await nextTick();
  edgeChatGuestNameInputRef.value?.focus();
  edgeChatGuestNameInputRef.value?.select();
};

const cancelGuestChatNameForm = () => {
  edgeChatGuestNameError.value = '';
  edgeChatGuestJoinMode.value = 'choice';
};

const saveGuestChatName = async () => {
  const displayName = edgeChatGuestNameDraft.value.trim();
  if (!displayName) return;

  const available = await checkGuestChatDisplayNameAvailability(displayName);
  if (!available) return;

  edgeChatGuestDisplayName.value = displayName;
  edgeChatGuestJoinMode.value = 'choice';
  await nextTick();
  chatInputRef.value?.focus();
};

const submitEdgeChatMessage = async () => {
  if (!isEdgeChatParticipant.value) {
    await openGuestChatNameForm();
    return;
  }

  const body = edgeChatDraft.value.trim();
  if (!body) return;
  const attachment = edgeChatDraftAttachment.value;

  edgeChatDraft.value = '';
  edgeChatDraftAttachment.value = null;

  try {
    const response = await fetch('/api/chat/messages', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        body,
        displayName: edgeChatDisplayName.value,
        ...(attachment ? { attachment } : {})
      })
    });
    if (!response.ok) {
      throw new Error('chat message post failed');
    }
    const message = await response.json() as ChatMessageResponse;
    upsertEdgeChatMessage(message);
  } catch {
    edgeChatDraft.value = body;
    edgeChatDraftAttachment.value = attachment;
  }
};

const removeWatchTarget = async (target: UserWatchTarget) => {
  try {
    await removeUserWatchTarget(target.targetType, target.targetId);
  } catch {
    if (!authUser.value) {
      await router.push('/auth/login');
    }
  }
};

const dismissNewsroomMenu = () => {
  newsroomMenuDismissed.value = true;
  window.setTimeout(() => {
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
  }, 0);
};

const handleLogout = async () => {
  await logout();
  authState.value = 'guest';
  resetUserWatchTargets('unauthenticated');
};
</script>

<template>
  <div :class="['app-shell', { 'edge-panel-open': railExpanded }]">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand-lockup">
          <RouterLink class="brand-home" data-testid="app-title" to="/dashboard">
            <h1>너나사 <span>YouBuyFirst</span></h1>
          </RouterLink>
        </div>

        <nav class="main-nav" aria-label="주요 화면">
          <RouterLink data-testid="nav-dashboard" to="/dashboard">대시보드</RouterLink>
          <span
            :class="['nav-menu-parent', { 'menu-dismissed': newsroomMenuDismissed }]"
            @pointerenter="newsroomMenuDismissed = false"
            @pointerleave="newsroomMenuDismissed = false"
            @focusin="newsroomMenuDismissed = false"
          >
            <RouterLink data-testid="nav-newsroom" to="/newsroom" @click="dismissNewsroomMenu">뉴스룸</RouterLink>
            <span class="nav-submenu" aria-label="뉴스룸 하위 피드">
              <RouterLink
                v-for="feed in newsroomFeeds"
                :key="feed.feed"
                :class="{ active: activeNewsroomFeed === feed.feed }"
                :to="{ path: '/newsroom', query: { feed: feed.feed } }"
                @click="dismissNewsroomMenu"
              >
                {{ feed.label }}
              </RouterLink>
            </span>
          </span>
          <RouterLink data-testid="nav-map" to="/realestate/map">지역 분석</RouterLink>
          <RouterLink data-testid="nav-transactions" to="/realestate/transactions">실거래</RouterLink>
          <RouterLink data-testid="nav-indicators" to="/indicators">주요 일정</RouterLink>
        </nav>

        <div class="topbar-status topbar-actions" aria-label="서비스 상태와 계정">
          <span>KST</span>
          <span v-if="authUser" class="auth-greeting" data-testid="auth-greeting">
            {{ authUser.displayName }}님 안녕하세요
          </span>
          <button
            v-if="authUser"
            class="login-button"
            data-testid="logout-button"
            type="button"
            @click="handleLogout"
          >
            로그아웃
          </button>
          <RouterLink
            v-else
            class="login-button"
            data-testid="auth-entry"
            to="/auth/login"
          >
            로그인
          </RouterLink>
        </div>
      </div>

      <div class="topbar-live-strip">
        <section class="live-strip" aria-label="상단 실시간 속보">
          <div class="live-strip-track">
            <div
              v-for="cycle in 4"
              :key="`ticker-cycle-${cycle}`"
              class="live-strip-sequence"
              :aria-hidden="cycle > 1"
            >
              <span
                v-for="topic in liveTopics"
                :key="`${cycle}-${topic.id}`"
                :class="['live-topic', `tone-${topic.tone}`]"
              >
                <strong>{{ topic.label }}</strong>
                {{ topic.text }}
              </span>
            </div>
          </div>
        </section>
      </div>
    </header>

    <main class="page-frame">
      <RouterView />
    </main>

    <footer class="site-footer" aria-labelledby="site-footer-title">
      <div class="site-footer-inner">
        <div class="site-footer-grid">
          <section class="site-footer-brand">
            <h2 id="site-footer-title">너나사<span>YouBuyFirst</span></h2>
            <p>
              실거래·전세 흐름, 지도 기반 지역 변화, 주요 일정, 뉴스·리포트 이슈를 함께 보는 부동산 인사이트 서비스입니다.
              실제 매수·매도·청약 판단을 대신하지 않습니다.
            </p>
            <a href="mailto:yh99cho1@gmail.com">문의 yh99cho1@gmail.com</a>
          </section>

          <section class="footer-column" aria-labelledby="footer-features-title">
            <h3 id="footer-features-title">서비스 특징</h3>
            <span>Daily briefing</span>
            <span>실거래·전세 흐름 확인</span>
            <span>전국·지역 지도 탐색</span>
            <span>주요 일정·뉴스·리포트 정리</span>
          </section>

          <section class="footer-column footer-legal" aria-labelledby="footer-notice-title">
            <h3 id="footer-notice-title">유의사항</h3>
            <p>
              가격, 거래, 일정 정보는 공개 지연이나 신고 보정으로 달라질 수 있습니다.
              본 사이트는 시장 정보를 정리해 보여주는 관찰용 서비스입니다.
            </p>
            <p>
              매수·매도·청약·대출 행동을 권유하지 않으며, 지도 색상과 요약은 확정 전망이 아닙니다.
            </p>
          </section>

          <section class="footer-column" aria-labelledby="footer-source-title">
            <h3 id="footer-source-title">데이터 출처</h3>
            <span>국토교통부 공공데이터</span>
            <span>한국부동산원 통계</span>
            <span>국토교통부 실거래가 공개시스템</span>
            <span>한국은행·청약Home 등 공식 출처</span>
          </section>
        </div>

        <div class="site-footer-bottom">
          <span>© 2026 YouBuyFirst · 모든 부동산 지표는 참고용이며 실시간이 아닐 수 있습니다.</span>
          <span>관찰형 부동산 인사이트 · 2026.06</span>
        </div>
      </div>
    </footer>

    <aside :class="['edge-panel', { open: railExpanded, 'chat-open': activeRailItem === 'chat' }]" aria-label="오른쪽 확장 패널">
      <section class="edge-panel-screen">
        <section
          v-if="activeRailItem === 'chat'"
          class="edge-chat-room"
          :style="edgeChatRoomStyle"
          data-testid="edge-chat-room"
          aria-label="채팅방"
        >
          <header class="edge-chat-toolbar">
            <div
              class="edge-chat-participants"
              data-testid="edge-chat-participants"
              aria-label="현재 채팅 참여자"
            >
              <span aria-hidden="true"></span>
              <strong>{{ edgeChatParticipantLabel }}</strong>
            </div>
            <div class="edge-chat-toolbar-actions" data-testid="edge-chat-toolbar-actions">
              <button
                type="button"
                data-testid="edge-chat-font-down"
                aria-label="글자 작게"
                :disabled="edgeChatFontLevel <= 1"
                @click="decreaseEdgeChatFont"
              >A-</button>
              <strong class="edge-chat-font-level" data-testid="edge-chat-font-level" aria-label="글자 크기">{{ edgeChatFontLevel }}</strong>
              <button
                type="button"
                data-testid="edge-chat-font-up"
                aria-label="글자 크게"
                :disabled="edgeChatFontLevel >= 9"
                @click="increaseEdgeChatFont"
              >A+</button>
              <button
                :class="[
                  'edge-chat-nickname-trigger',
                  edgeChatDisplayToneClass,
                  { 'edge-chat-author-gradient': hasEdgeChatDisplayAnimation }
                ]"
                type="button"
                data-testid="edge-chat-nickname-trigger"
                :data-author="edgeChatDisplayName"
                aria-label="닉네임 수정"
                @click="openChatNicknameSettings"
              >{{ edgeChatDisplayName }}</button>
            </div>
            <form
              v-if="edgeChatNicknamePopoverOpen"
              class="edge-chat-nickname-popover"
              data-testid="edge-chat-nickname-popover"
              @submit.prevent="saveChatNicknameSettings"
              @keydown.esc.prevent="closeChatNicknameSettings"
            >
              <div class="edge-chat-nickname-popover-header">
                <strong
                  class="edge-chat-nickname-popover-title"
                  data-testid="edge-chat-nickname-popover-title"
                >닉네임 변경</strong>
                <span>{{ edgeChatDisplayName }}</span>
              </div>
              <label
                class="edge-chat-nickname-field-label"
                data-testid="edge-chat-nickname-field-label"
                for="edge-chat-nickname-input"
              >채팅 닉네임</label>
              <input
                id="edge-chat-nickname-input"
                ref="edgeChatNicknameInputRef"
                v-model="edgeChatNicknameDraft"
                data-testid="edge-chat-nickname-input"
                type="text"
                maxlength="16"
                autocomplete="off"
                aria-label="닉네임"
              />
              <p
                v-if="edgeChatGuestNameError"
                class="edge-chat-guest-error"
                data-testid="edge-chat-nickname-error"
              >{{ edgeChatGuestNameError }}</p>
              <div class="edge-chat-nickname-actions">
                <button
                  type="button"
                  data-testid="edge-chat-nickname-cancel"
                  @click="closeChatNicknameSettings"
                >취소</button>
                <button
                  type="submit"
                  data-testid="edge-chat-nickname-save"
                  :disabled="!canSaveEdgeChatNickname"
                  @click.prevent="saveChatNicknameSettings"
                >저장</button>
              </div>
            </form>
          </header>

          <div class="edge-chat-feed-frame" data-testid="edge-chat-feed-frame">
            <div
              ref="edgeChatFeedRef"
              class="edge-chat-feed"
              :class="{ 'guest-locked': showGuestChatGate }"
              data-testid="edge-chat-feed"
              aria-label="채팅 메시지 목록"
            >
            <article
              v-for="message in filteredEdgeChatMessages"
              :key="message.id"
              :class="['edge-chat-message', `tone-${message.tone ?? 'blue'}`, { mine: message.mine }]"
            >
              <div class="edge-chat-message-meta">
                <strong
                  :class="[
                    'edge-chat-author-name',
                    edgeChatAuthorToneClass(message.author),
                    { 'edge-chat-author-gradient': hasEdgeChatAuthorAnimation(message) }
                  ]"
                  :data-author="message.author"
                >{{ message.author }}</strong>
                <span
                  v-if="isEdgeChatVerifiedMessage(message)"
                  class="edge-chat-author-verified"
                  data-testid="edge-chat-author-verified"
                  aria-label="가입 인증"
                  title="가입 인증"
                >
                  <svg viewBox="0 0 12 12" aria-hidden="true" focusable="false">
                    <path d="M3.1 6.1 5 8l4-4.3" />
                  </svg>
                </span>
                <em>{{ message.timeLabel }}</em>
              </div>
              <div class="edge-chat-message-bubble">
                <p v-if="message.body">{{ message.body }}</p>
                <RouterLink
                  v-if="message.attachment"
                  class="edge-chat-attachment"
                  :class="[`metric-${message.attachment.metricTone ?? 'flat'}`]"
                  :to="message.attachment.landingPath"
                  :data-testid="`edge-chat-attachment-${message.attachment.type}-${message.attachment.targetId}`"
                >
                  <span class="edge-chat-attachment-head">
                    <i>{{ chatAttachmentKindLabel(message.attachment) }}</i>
                    <strong>{{ message.attachment.title }}</strong>
                  </span>
                  <em
                    v-if="shouldShowChatAttachmentDetail(message.attachment)"
                    class="edge-chat-attachment-detail"
                  >{{ chatAttachmentCompactDetail(message.attachment) }}</em>
                  <span v-if="message.attachment.metricValue" class="edge-chat-attachment-metric">
                    <span v-if="message.attachment.metricLabel">{{ chatAttachmentMetricLabelText(message.attachment) }}</span>
                    <b>{{ message.attachment.metricValue }}</b>
                  </span>
                </RouterLink>
              </div>
            </article>
            </div>

            <div
              v-if="showGuestChatGate"
              class="edge-chat-guest-gate"
              data-testid="edge-chat-guest-gate"
              aria-label="채팅 참여 선택"
            >
              <div v-if="edgeChatGuestJoinMode === 'choice'" class="edge-chat-guest-panel">
                <strong>채팅 참여</strong>
                <p>로그인하거나 닉네임만 정해서 바로 대화에 참여할 수 있어요.</p>
                <div class="edge-chat-guest-actions">
                  <RouterLink
                    class="edge-chat-guest-login"
                    data-testid="edge-chat-guest-login"
                    to="/auth/login"
                  >로그인 하기</RouterLink>
                  <button
                    type="button"
                    class="edge-chat-guest-join"
                    data-testid="edge-chat-guest-join"
                    @click="openGuestChatNameForm"
                  >비로그인으로 참여하기</button>
                </div>
              </div>
              <form
                v-else
                class="edge-chat-guest-panel edge-chat-guest-form"
                data-testid="edge-chat-guest-form"
                @submit.prevent="saveGuestChatName"
              >
                <strong>닉네임 입력</strong>
                <p>채팅에 표시될 이름을 정해주세요. 게스트 닉네임에는 인증마크가 붙지 않아요.</p>
                <input
                  ref="edgeChatGuestNameInputRef"
                  v-model="edgeChatGuestNameDraft"
                  data-testid="edge-chat-guest-name-input"
                  type="text"
                  maxlength="16"
                  autocomplete="off"
                  aria-label="게스트 닉네임"
                  placeholder="예: 송파관찰러"
                />
                <p
                  v-if="edgeChatGuestNameError"
                  class="edge-chat-guest-error"
                  data-testid="edge-chat-guest-name-error"
                >{{ edgeChatGuestNameError }}</p>
                <div class="edge-chat-guest-form-actions">
                  <button
                    type="button"
                    data-testid="edge-chat-guest-name-cancel"
                    @click="cancelGuestChatNameForm"
                  >돌아가기</button>
                  <button
                    type="submit"
                    data-testid="edge-chat-guest-name-save"
                    :disabled="!canSaveGuestChatName"
                    @click.prevent="saveGuestChatName"
                  >참여 시작</button>
                </div>
              </form>
            </div>
          </div>

          <div class="edge-chat-composer">
            <div
              v-if="edgeChatDraftAttachment"
              class="edge-chat-pending-attachment"
              data-testid="edge-chat-pending-attachment"
            >
              <div>
                <span class="edge-chat-pending-attachment-head">
                  <i>{{ chatAttachmentKindLabel(edgeChatDraftAttachment) }}</i>
                  <strong>{{ edgeChatDraftAttachment.title }}</strong>
                </span>
                <em v-if="shouldShowChatAttachmentDetail(edgeChatDraftAttachment)">
                  {{ chatAttachmentCompactDetail(edgeChatDraftAttachment) }}
                </em>
              </div>
              <span
                v-if="edgeChatDraftAttachment.metricValue"
                class="edge-chat-pending-attachment-metric"
                :class="`metric-${edgeChatDraftAttachment.metricTone ?? 'flat'}`"
              >
                <span v-if="edgeChatDraftAttachment.metricLabel">{{ chatAttachmentMetricLabelText(edgeChatDraftAttachment) }}</span>
                <b>{{ edgeChatDraftAttachment.metricValue }}</b>
              </span>
              <button
                type="button"
                data-testid="edge-chat-attachment-clear"
                aria-label="채팅 첨부 제거"
                @click="clearEdgeChatDraftAttachment"
              >×</button>
            </div>
            <form class="edge-chat-form" data-testid="edge-chat-form" @submit.prevent="submitEdgeChatMessage">
              <textarea
                ref="chatInputRef"
                v-model="edgeChatDraft"
                data-testid="edge-chat-input"
                :placeholder="isEdgeChatParticipant ? '메시지 입력...' : '비로그인 참여 후 메시지 입력...'"
                rows="1"
                :disabled="!isEdgeChatParticipant"
                @keydown.enter.exact.prevent="submitEdgeChatMessage"
              />
              <button class="edge-chat-submit" type="submit" :disabled="!canPostChat">전송</button>
            </form>
          </div>
        </section>

        <template v-else>
          <div class="edge-panel-header">
            <div>
              <p class="label">quick panel</p>
              <h2>{{ activeRailLabel }}</h2>
            </div>
            <span class="panel-mini-badge">{{ activePanelBadgeLabel }}</span>
          </div>

          <div v-if="activeRailItem === 'watch'" class="edge-watch-list">
            <div v-if="!authUser" class="edge-empty-state">
              <strong>로그인 필요</strong>
              <p>지역 분석과 실거래에서 저장한 관심 대상은 로그인 사용자별로 보관됩니다.</p>
              <RouterLink class="edge-panel-login-link" to="/auth/login">로그인하기</RouterLink>
            </div>
            <div v-else-if="userWatchTargetLoadState === 'loading'" class="edge-empty-state">
              <strong>관심 목록 확인 중</strong>
              <p>로그인 세션 기준 저장 목록을 불러오고 있습니다.</p>
            </div>
            <div v-else-if="!watchTargets.length" class="edge-empty-state">
              <strong>저장된 관심 없음</strong>
              <p>지역 리포트나 실거래 상세의 하트 버튼을 누르면 이곳에 바로가기가 쌓입니다.</p>
            </div>
            <template v-else>
              <article
                v-for="target in watchTargets"
                :key="`${target.targetType}-${target.targetId}`"
                class="edge-watch-item"
              >
                <RouterLink
                  class="edge-watch-row"
                  :data-testid="watchTargetTestId(target)"
                  :to="target.landingPath"
                >
                  <span class="edge-initial">{{ watchTargetInitial(target) }}</span>
                  <div>
                    <strong>{{ target.displayName }}</strong>
                    <p>{{ watchTargetTypeLabel(target) }}</p>
                  </div>
                  <span class="edge-watch-arrow" aria-hidden="true">›</span>
                </RouterLink>
                <button
                  class="edge-watch-remove"
                  type="button"
                  :data-testid="watchTargetRemoveTestId(target)"
                  :aria-label="`${target.displayName} 관심 해제`"
                  @click="removeWatchTarget(target)"
                >♥</button>
              </article>
            </template>
          </div>

          <div v-else-if="activeRailItem === 'recent'" class="edge-recent-list">
            <div v-if="!recentViews.length" class="edge-empty-state">
              <strong>최근 본 항목 없음</strong>
              <p>지역 분석에서 지역을 열거나 실거래에서 부동산을 선택하면 최신순으로 최대 15개까지 표시됩니다.</p>
            </div>
            <RouterLink
              v-for="view in recentViews"
              :key="`${view.kind}-${view.id}`"
              class="edge-recent-row"
              :to="view.href"
              :data-testid="recentViewTestId(view)"
            >
              <span class="edge-initial">{{ recentViewInitial(view) }}</span>
              <div>
                <strong>{{ view.label }}</strong>
                <p>{{ view.meta }}</p>
              </div>
              <span class="edge-recent-arrow" aria-hidden="true">›</span>
            </RouterLink>
          </div>

          <div v-else class="edge-empty-state">
            <strong>{{ activeRailLabel }} 패널</strong>
            <p>{{ shellStatusLabel }} · 해당 패널의 실제 API가 열리면 항목을 표시합니다.</p>
          </div>
        </template>
      </section>
    </aside>

    <aside class="edge-rail" aria-label="오른쪽 고정 탭">
      <button
        class="rail-expand"
        type="button"
        :aria-expanded="railExpanded"
        aria-label="오른쪽 패널 열고 닫기"
        @click="toggleRail"
      >
        <span>{{ railExpanded ? '»' : '«' }}</span>
        <em>{{ railExpanded ? '닫기' : '열기' }}</em>
      </button>
      <button
        v-for="item in railItems"
        :key="item.id"
        type="button"
        :data-testid="`edge-rail-${item.id}`"
        :class="{ active: railExpanded && activeRailItem === item.id }"
        :aria-pressed="railExpanded && activeRailItem === item.id"
        @click="openRail(item.id)"
      >
        <span>
          <svg
            v-if="item.icon === 'chat'"
            viewBox="0 0 28 24"
            aria-hidden="true"
            focusable="false"
          >
            <path
              d="M5 6.4A3.9 3.9 0 0 1 8.9 2.5h10.2A3.9 3.9 0 0 1 23 6.4v5.2a3.9 3.9 0 0 1-3.9 3.9h-5.4L7 20.5v-5.2a3.9 3.9 0 0 1-2-3.4z"
            />
          </svg>
          <template v-else>{{ item.shortcut }}</template>
        </span>
        <em>{{ item.label }}</em>
      </button>
      <button class="theme-toggle" type="button" aria-label="라이트 다크 모드 전환">
        <span>◐</span>
        <em>다크모드</em>
      </button>
    </aside>
  </div>
</template>
