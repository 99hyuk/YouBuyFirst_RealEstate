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
  { tone: 'market', label: '가격·공시' },
  { tone: 'deal', label: '거래현황' },
  { tone: 'supply', label: '공급' },
  { tone: 'finance', label: '금융' },
  { tone: 'policy', label: '정책' },
  { tone: 'subscription', label: '청약' }
];

const fallbackScheduleEvents: ScheduleEvent[] = [];

const fallbackSourceLinks: SourceLink[] = [
  {
    id: 'reb-r-one',
    title: '한국부동산원 R-ONE',
    label: '가격지수·거래현황 공표일정',
    link: 'https://www.reb.or.kr/r-one/portal/compose/scheduleStatsPage.do'
  },
  {
    id: 'rt-molit',
    title: '국토교통부 실거래가 공개시스템',
    label: '상시 공개·freshness 확인',
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
  },
  {
    id: 'hug-market',
    title: 'HUG 주택도시보증공사',
    label: '분양가격·분양시장',
    link: 'https://khug.or.kr/houstar/web/p01/03/p010301.jsp?currentPage=1'
  },
  {
    id: 'lh-apply',
    title: 'LH청약플러스',
    label: '공공분양·공공임대',
    link: 'https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1027'
  },
  {
    id: 'sh-housing',
    title: '서울주거포털 SH',
    label: '공공임대',
    link: 'https://housing.seoul.go.kr/site/main/sh/publicLease/07/list'
  },
  {
    id: 'gh-supply',
    title: '경기주택도시공사 GH',
    label: '분양·임대 공고',
    link: 'https://www.gh.or.kr/gh/announcement-of-salerental001.do'
  },
  {
    id: 'ih-supply',
    title: '인천도시공사 iH',
    label: '분양·임대 공고',
    link: 'https://www.ih.co.kr/main/sale_lease/notice.jsp'
  },
  {
    id: 'fsc-policy',
    title: '금융위원회',
    label: '부동산 금융정책',
    link: 'https://www.fsc.go.kr/no010101'
  },
  {
    id: 'realty-price',
    title: '부동산공시가격 알리미',
    label: '공시가격',
    link: 'https://www.realtyprice.kr/notice/board/boardListAll.board'
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
  return isPublishedSchedule(event) ? '공표 확인' : '공식 일정';
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
        <span>가격·거래현황, 공급, 금융, 청약, 정책·공시 일정을 캘린더로 확인합니다.</span>
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
          <article v-if="!visibleScheduleEvents.length" class="calendar-event-card empty">
            <time :datetime="`${calendarMonth}-01`">{{ calendarMonthLabel }}</time>
            <span class="calendar-event-card-body">
              <strong>공식 일정 수집 전</strong>
              <span>이 달에 공식 원천에서 날짜가 확인된 일정이 아직 없습니다.</span>
            </span>
            <em>공식 출처 · insufficient</em>
          </article>
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
