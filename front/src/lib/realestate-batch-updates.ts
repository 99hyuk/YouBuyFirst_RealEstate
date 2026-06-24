export type RealEstateBatchUpdateTopic = 'newsroom' | 'market-data-schedules' | 'map-layers';

export type RealEstateBatchUpdateEvent = {
  topic: RealEstateBatchUpdateTopic | string;
  month?: string | null;
  acceptedItems?: number | null;
  refreshedAt?: string | null;
};

export type BatchUpdateSubscription = {
  supported: boolean;
  close: () => void;
};

type EventSourceLike = {
  addEventListener: (type: string, listener: (event: MessageEvent) => void) => void;
  close: () => void;
};

type EventSourceFactory = new (url: string) => EventSourceLike;

const BATCH_UPDATE_STREAM_URL = '/api/realestate/batch-updates/stream';
const BATCH_UPDATE_EVENT_NAME = 'realestate-batch-update';

export function subscribeRealEstateBatchUpdates(
  onUpdate: (event: RealEstateBatchUpdateEvent) => void,
  eventSourceFactory?: EventSourceFactory
): BatchUpdateSubscription {
  const Factory = eventSourceFactory ?? globalThis.EventSource;
  if (!Factory) {
    return {
      supported: false,
      close: () => {}
    };
  }

  const source = new Factory(BATCH_UPDATE_STREAM_URL);
  source.addEventListener(BATCH_UPDATE_EVENT_NAME, (message) => {
    const event = parseBatchUpdateEvent(message.data);
    if (event) {
      onUpdate(event);
    }
  });

  return {
    supported: true,
    close: () => source.close()
  };
}

function parseBatchUpdateEvent(rawData: string): RealEstateBatchUpdateEvent | null {
  try {
    const parsed = JSON.parse(rawData) as Partial<RealEstateBatchUpdateEvent>;
    if (typeof parsed.topic !== 'string' || !parsed.topic) {
      return null;
    }
    return {
      topic: parsed.topic,
      month: typeof parsed.month === 'string' ? parsed.month : null,
      acceptedItems: typeof parsed.acceptedItems === 'number' ? parsed.acceptedItems : null,
      refreshedAt: typeof parsed.refreshedAt === 'string' ? parsed.refreshedAt : null
    };
  } catch {
    return null;
  }
}
