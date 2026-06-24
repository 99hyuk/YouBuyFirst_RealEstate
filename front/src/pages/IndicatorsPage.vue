<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';

import {
  subscribeRealEstateBatchUpdates,
  type BatchUpdateSubscription
} from '../lib/realestate-batch-updates';
import {
  currentMonth,
  fetchMarketDataSchedules,
  type MarketDataScheduleEvent,
  type MarketDataSourceLink
} from '../lib/realestate-schedules';

type ScheduleEvent = MarketDataScheduleEvent;
type SourceLink = MarketDataSourceLink;

const calendarMonth = ref(currentMonth());
const calendarYear = computed(() => Number(calendarMonth.value.slice(0, 4)));
const calendarMonthIndex = computed(() => Number(calendarMonth.value.slice(5, 7)) - 1);
const calendarMonthLabel = computed(() => calendarMonth.value.replace('-', '.'));
const todayIso = new Date().toISOString().slice(0, 10);
const weekdayLabels = ['월', '화', '수', '목', '금', '토', '일'];
const scheduleToneLegend = [
  { tone: 'market', label: '가격지수' },
  { tone: 'deal', label: '실거래' },
  { tone: 'supply', label: '공급' },
  { tone: 'finance', label: '금융' },
  { tone: 'policy', label: '정책' },
  { tone: 'subscription', label: '청약' }
];

const fallbackScheduleEvents: ScheduleEvent[] = [
  {
    id: 'r-one-weekly',
    date: '2026-06-03',
    title: '주간 아파트 가격동향 확인',
    category: '가격지수',
    source: '한국부동산원 R-ONE',
    summary: '매매·전세 가격 흐름과 상승/하락 지역을 먼저 확인합니다.',
    link: 'https://www.reb.or.kr/r-one/portal/bbs/pres/searchBulletinPage.do?listSubCd=PRES01',
    tone: 'market'
  },
  {
    id: 'rt-molit',
    date: '2026-06-05',
    title: '실거래가 공개 데이터 점검',
    category: '실거래',
    source: '국토교통부 실거래가 공개시스템',
    summary: '최근 신고된 매매·전월세 거래가 들어왔는지 확인합니다.',
    link: 'https://rt.molit.go.kr/',
    tone: 'deal'
  },
  {
    id: 'molit-unsold',
    date: '2026-06-10',
    title: '미분양·공급 통계 확인',
    category: '공급',
    source: '국토교통 통계누리',
    summary: '미분양, 준공 후 미분양, 인허가 흐름을 함께 봅니다.',
    link: 'https://stat.molit.go.kr/portal/notice/scheduleList.do',
    tone: 'supply'
  },
  {
    id: 'bok-rate',
    date: '2026-06-12',
    title: '금리·통화정책 일정 확인',
    category: '금융',
    source: '한국은행',
    summary: '기준금리, 통화정책방향, 의사록 일정을 대출 민감도와 함께 확인합니다.',
    link: 'https://www.bok.or.kr/portal/singl/crncyPolicyDrcMtg/listYear.do?menuNo=200755&mtgSe=A',
    tone: 'finance'
  },
  {
    id: 'applyhome',
    date: '2026-06-16',
    title: '청약·분양 일정 확인',
    category: '청약',
    source: '청약Home',
    summary: '청약 접수, 당첨자 발표, 경쟁률 공개 일정을 확인합니다.',
    link: 'https://www.applyhome.co.kr/ai/aib/selectSubscrptCalenderView.do',
    tone: 'subscription'
  },
  {
    id: 'molit-policy',
    date: '2026-06-20',
    title: '정책·보도자료 확인',
    category: '정책',
    source: '국토교통부',
    summary: '공급, 대출, 정비사업, 교통 발표가 있는지 확인합니다.',
    link: 'https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp',
    tone: 'policy'
  },
  {
    id: 'hug-market',
    date: '2026-06-25',
    title: '보증·주택시장 자료 확인',
    category: '보증',
    source: 'HUG 주택도시보증공사',
    summary: '분양보증, 전세보증, 주택시장 참고 자료를 확인합니다.',
    link: 'https://www.khug.or.kr/houstar/web/p01/03/p010301.jsp',
    tone: 'supply'
  },
  {
    id: 'month-close',
    date: '2026-06-30',
    title: '월말 시장 데이터 마감 점검',
    category: '월마감',
    source: '공식 통계 묶음',
    summary: '가격지수, 실거래, 공급, 금리 이슈를 월간 리포트 후보로 묶습니다.',
    link: 'https://www.reb.or.kr/r-one/portal/compose/scheduleStatsPage.do',
    tone: 'market'
  }
];

const fallbackSourceLinks: SourceLink[] = [
  {
    id: 'reb-r-one',
    title: '한국부동산원 R-ONE',
    label: '가격지수·공표일정',
    link: 'https://www.reb.or.kr/r-one/portal/main/indexPage.do'
  },
  {
    id: 'rt-molit',
    title: '국토교통부 실거래가 공개시스템',
    label: '매매·전월세 거래',
    link: 'https://rt.molit.go.kr/'
  },
  {
    id: 'molit-stat',
    title: '국토교통 통계누리',
    label: '미분양·공급',
    link: 'https://stat.molit.go.kr/'
  },
  {
    id: 'bok-rate',
    title: '한국은행 일정',
    label: '금리·통화정책',
    link: 'https://www.bok.or.kr/portal/singl/crncyPolicyDrcMtg/listYear.do?menuNo=200755&mtgSe=A'
  },
  {
    id: 'applyhome',
    title: '청약Home',
    label: '청약·분양',
    link: 'https://applyhome.co.kr/'
  },
  {
    id: 'molit-policy',
    title: '국토교통부',
    label: '정책·보도자료',
    link: 'https://www.molit.go.kr/'
  }
];

const scheduleEvents = ref<ScheduleEvent[]>(fallbackScheduleEvents);
const sourceLinks = ref<SourceLink[]>(fallbackSourceLinks);
const requestedScheduleId = ref<string | null>(null);
const scheduleCardElements = ref<Record<string, HTMLElement>>({});
let batchUpdateSubscription: BatchUpdateSubscription | null = null;

const shiftedMonth = (month: string, offset: number) => {
  const year = Number(month.slice(0, 4));
  const monthIndex = Number(month.slice(5, 7)) - 1;
  const targetDate = new Date(year, monthIndex + offset, 1);
  return `${targetDate.getFullYear()}-${String(targetDate.getMonth() + 1).padStart(2, '0')}`;
};

const refreshSchedules = async (month = calendarMonth.value) => {
  try {
    const response = await fetchMarketDataSchedules({ month });
    calendarMonth.value = response.month;
    scheduleEvents.value = response.scheduleEvents;
    sourceLinks.value = response.sourceLinks.length ? response.sourceLinks : fallbackSourceLinks;
  } catch {
    scheduleEvents.value = fallbackScheduleEvents;
    sourceLinks.value = fallbackSourceLinks;
  }
};

const moveCalendarMonth = (offset: number) => {
  const targetMonth = shiftedMonth(calendarMonth.value, offset);
  calendarMonth.value = targetMonth;
  requestedScheduleId.value = null;
  void refreshSchedules(targetMonth);
};

const scheduleByDate = computed(() => scheduleEvents.value.reduce<Record<string, ScheduleEvent[]>>((acc, event) => {
  acc[event.date] = [...(acc[event.date] ?? []), event];
  return acc;
}, {}));

const visibleScheduleEvents = computed(() => [...scheduleEvents.value]
  .filter((event) => event.date.startsWith(`${calendarMonth.value}-`))
  .sort((left, right) => {
    const dateOrder = left.date.localeCompare(right.date);
    if (dateOrder !== 0) return dateOrder;
    return left.title.localeCompare(right.title, 'ko-KR');
  }));

const genericScheduleLinks = new Set([
  'https://applyhome.co.kr',
  'https://www.applyhome.co.kr',
  'https://www.molit.go.kr',
  'https://rt.molit.go.kr',
  'https://stat.molit.go.kr',
  'https://www.khug.or.kr',
  'https://www.reb.or.kr/r-one/portal/main/indexPage.do'
]);

const isPublishedSchedule = (event: ScheduleEvent) => event.dataStatus === 'published' && Boolean(event.link);

const normalizedScheduleLink = (link: string) => link.replace(/\/+$/, '');

const scheduleLinkFor = (event: ScheduleEvent) => {
  const link = event.link?.trim();
  if (!link) return undefined;
  return genericScheduleLinks.has(normalizedScheduleLink(link)) ? undefined : link;
};

const scheduleSummaryLine = (event: ScheduleEvent) => {
  if (!event.summary) return event.title;
  return `${event.title} · ${event.summary}`;
};

const eventStatusLabel = (event: ScheduleEvent) => {
  if (event.status) return event.status;
  return isPublishedSchedule(event) ? '공표 확인' : '확인 예정';
};

const eventDateLabel = (date: string) => date.slice(5).replace('-', '.');

const setScheduleCardElement = (eventId: string) => (element: Element | null) => {
  if (element instanceof HTMLElement) {
    scheduleCardElements.value[eventId] = element;
    return;
  }
  delete scheduleCardElements.value[eventId];
};

const requestScheduleDetail = async (event: ScheduleEvent) => {
  requestedScheduleId.value = null;
  await nextTick();
  requestedScheduleId.value = event.id;
  await nextTick();
  scheduleCardElements.value[event.id]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
};

const calendarCells = computed(() => {
  const firstDay = new Date(calendarYear.value, calendarMonthIndex.value, 1);
  const lastDay = new Date(calendarYear.value, calendarMonthIndex.value + 1, 0);
  const leadingEmpty = (firstDay.getDay() + 6) % 7;
  const dayCount = lastDay.getDate();
  const totalCells = Math.ceil((leadingEmpty + dayCount) / 7) * 7;

  return Array.from({ length: totalCells }, (_, index) => {
    const day = index - leadingEmpty + 1;
    if (day < 1 || day > dayCount) {
      return {
        key: `empty-${index}`,
        day: '',
        iso: '',
        events: [] as ScheduleEvent[],
        muted: true,
        today: false
      };
    }

    const month = String(calendarMonthIndex.value + 1).padStart(2, '0');
    const iso = `${calendarYear.value}-${month}-${String(day).padStart(2, '0')}`;
    return {
      key: iso,
      day: String(day),
      iso,
      events: scheduleByDate.value[iso] ?? [],
      muted: false,
      today: iso === todayIso
    };
  });
});

onMounted(() => {
  void refreshSchedules();
  batchUpdateSubscription = subscribeRealEstateBatchUpdates((event) => {
    if (event.topic !== 'market-data-schedules') return;
    if (event.month && event.month !== calendarMonth.value) return;
    void refreshSchedules();
  });
});

onBeforeUnmount(() => {
  batchUpdateSubscription?.close();
  batchUpdateSubscription = null;
});
</script>

<template>
  <section class="surface-page indicators-page indicator-calendar-page">
    <section class="indicator-calendar-hero" aria-labelledby="indicators-title">
      <div>
        <p class="label">공식 일정 보드</p>
        <h2 id="indicators-title">주요 일정</h2>
        <span>가격지수, 실거래, 공급, 금리, 청약 일정을 캘린더로 확인합니다.</span>
      </div>
    </section>

    <section class="indicator-calendar-layout" aria-label="부동산 주요 일정 캘린더">
      <article class="calendar-month-card">
        <div class="calendar-month-header">
          <div class="calendar-month-copy">
            <p class="label">월간 일정 캘린더</p>
            <div class="calendar-month-title-row" aria-label="월 이동">
              <button
                type="button"
                class="calendar-month-nav"
                aria-label="이전 달 일정 보기"
                @click="moveCalendarMonth(-1)"
              >
                <span aria-hidden="true">‹</span>
              </button>
              <h3>{{ calendarMonthLabel }}</h3>
              <button
                type="button"
                class="calendar-month-nav"
                aria-label="다음 달 일정 보기"
                @click="moveCalendarMonth(1)"
              >
                <span aria-hidden="true">›</span>
              </button>
            </div>
          </div>
          <div class="calendar-tone-legend" aria-label="일정 유형 색상 범례">
            <span
              v-for="tone in scheduleToneLegend"
              :key="tone.tone"
              class="calendar-tone-key"
              :class="tone.tone"
            >
              {{ tone.label }}
            </span>
          </div>
        </div>

        <div class="calendar-weekdays" aria-hidden="true">
          <span v-for="weekday in weekdayLabels" :key="weekday">{{ weekday }}</span>
        </div>

        <div class="calendar-grid">
          <div
            v-for="cell in calendarCells"
            :key="cell.key"
            class="calendar-day"
            :class="{ muted: cell.muted, today: cell.today, 'has-events': cell.events.length }"
          >
            <span class="calendar-day-number">{{ cell.day }}</span>
            <div v-if="cell.events.length" class="calendar-day-events">
              <button
                v-for="event in cell.events"
                :key="event.id"
                type="button"
                class="calendar-event-strip"
                :class="[event.tone, event.dataStatus ?? 'scheduled']"
                :title="scheduleSummaryLine(event)"
                :aria-label="`${eventDateLabel(event.date)} ${scheduleSummaryLine(event)}`"
                @click="requestScheduleDetail(event)"
              >
                <span>{{ scheduleSummaryLine(event) }}</span>
              </button>
            </div>
          </div>
        </div>

        <div class="calendar-event-list" aria-label="월간 공식 일정 요약">
          <component
            :is="scheduleLinkFor(event) ? 'a' : 'article'"
            v-for="event in visibleScheduleEvents"
            :key="event.id"
            :href="scheduleLinkFor(event)"
            :target="scheduleLinkFor(event) ? '_blank' : undefined"
            :rel="scheduleLinkFor(event) ? 'noreferrer' : undefined"
            :ref="setScheduleCardElement(event.id)"
            :data-schedule-event-id="event.id"
            class="calendar-event-card"
            :class="[event.tone, event.dataStatus ?? 'scheduled', { requested: requestedScheduleId === event.id }]"
            :aria-current="requestedScheduleId === event.id ? 'true' : undefined"
          >
            <time :datetime="event.date">{{ eventDateLabel(event.date) }}</time>
            <span class="calendar-event-card-body">
              <strong>{{ event.title }}</strong>
              <span>{{ event.summary }}</span>
            </span>
            <em>{{ event.source }} · {{ eventStatusLabel(event) }}</em>
          </component>
        </div>
      </article>

    </section>

    <section class="schedule-source-section" aria-labelledby="schedule-source-title">
      <div class="section-title-row">
        <div>
          <h2 id="schedule-source-title">공식 출처</h2>
        </div>
      </div>

      <div class="schedule-source-grid">
        <a
          v-for="source in sourceLinks"
          :key="source.title"
          :href="source.link"
          class="schedule-source-card"
          target="_blank"
          rel="noreferrer"
        >
          <strong>{{ source.title }}</strong>
          <span>{{ source.label }}</span>
        </a>
      </div>
    </section>
  </section>
</template>
