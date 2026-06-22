<script setup lang="ts">
import { computed } from 'vue';

type ScheduleTone = 'market' | 'deal' | 'supply' | 'finance' | 'policy' | 'subscription';

type ScheduleEvent = {
  id: string;
  date: string;
  title: string;
  category: string;
  source: string;
  summary: string;
  link: string;
  tone: ScheduleTone;
};

type SourceLink = {
  title: string;
  label: string;
  link: string;
};

const calendarYear = 2026;
const calendarMonthIndex = 5;
const calendarMonthLabel = '2026.06';
const todayIso = '2026-06-22';
const weekdayLabels = ['월', '화', '수', '목', '금', '토', '일'];

const scheduleEvents: ScheduleEvent[] = [
  {
    id: 'r-one-weekly',
    date: '2026-06-03',
    title: '주간 아파트 가격동향 확인',
    category: '가격지수',
    source: '한국부동산원 R-ONE',
    summary: '매매·전세 가격 흐름과 상승/하락 지역을 먼저 확인합니다.',
    link: 'https://www.reb.or.kr/r-one/portal/main/indexPage.do',
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
    link: 'https://stat.molit.go.kr/',
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
    link: 'https://applyhome.co.kr/',
    tone: 'subscription'
  },
  {
    id: 'molit-policy',
    date: '2026-06-20',
    title: '정책·보도자료 확인',
    category: '정책',
    source: '국토교통부',
    summary: '공급, 대출, 정비사업, 교통 발표가 있는지 확인합니다.',
    link: 'https://www.molit.go.kr/',
    tone: 'policy'
  },
  {
    id: 'hug-market',
    date: '2026-06-25',
    title: '보증·주택시장 자료 확인',
    category: '보증',
    source: 'HUG 주택도시보증공사',
    summary: '분양보증, 전세보증, 주택시장 참고 자료를 확인합니다.',
    link: 'https://www.khug.or.kr/',
    tone: 'supply'
  },
  {
    id: 'month-close',
    date: '2026-06-30',
    title: '월말 시장 데이터 마감 점검',
    category: '월마감',
    source: '공식 통계 묶음',
    summary: '가격지수, 실거래, 공급, 금리 이슈를 월간 리포트 후보로 묶습니다.',
    link: 'https://www.reb.or.kr/r-one/portal/stat/easyStatPage.do',
    tone: 'market'
  }
];

const sourceLinks: SourceLink[] = [
  {
    title: '한국부동산원 R-ONE',
    label: '가격지수·공표일정',
    link: 'https://www.reb.or.kr/r-one/portal/main/indexPage.do'
  },
  {
    title: '국토교통부 실거래가 공개시스템',
    label: '매매·전월세 거래',
    link: 'https://rt.molit.go.kr/'
  },
  {
    title: '국토교통 통계누리',
    label: '미분양·공급',
    link: 'https://stat.molit.go.kr/'
  },
  {
    title: '한국은행 일정',
    label: '금리·통화정책',
    link: 'https://www.bok.or.kr/portal/singl/crncyPolicyDrcMtg/listYear.do?menuNo=200755&mtgSe=A'
  },
  {
    title: '청약Home',
    label: '청약·분양',
    link: 'https://applyhome.co.kr/'
  },
  {
    title: '국토교통부',
    label: '정책·보도자료',
    link: 'https://www.molit.go.kr/'
  }
];

const scheduleByDate = computed(() => scheduleEvents.reduce<Record<string, ScheduleEvent[]>>((acc, event) => {
  acc[event.date] = [...(acc[event.date] ?? []), event];
  return acc;
}, {}));

const calendarCells = computed(() => {
  const firstDay = new Date(calendarYear, calendarMonthIndex, 1);
  const lastDay = new Date(calendarYear, calendarMonthIndex + 1, 0);
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

    const iso = `${calendarYear}-06-${String(day).padStart(2, '0')}`;
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

</script>

<template>
  <section class="surface-page indicators-page indicator-calendar-page">
    <section class="indicator-calendar-hero" aria-labelledby="indicators-title">
      <div>
        <p class="label">공식 일정 보드</p>
        <h2 id="indicators-title">주요 일정</h2>
        <span>가격지수, 실거래, 공급, 금리, 청약 일정을 캘린더로 확인합니다.</span>
      </div>
      <a
        class="calendar-primary-link"
        href="https://www.reb.or.kr/r-one/portal/main/indexPage.do"
        target="_blank"
        rel="noreferrer"
      >
        공식 통계 확인
      </a>
    </section>

    <section class="indicator-calendar-layout" aria-label="부동산 주요 일정 캘린더">
      <article class="calendar-month-card">
        <div class="calendar-month-header">
          <div>
            <p class="label">월간 일정 캘린더</p>
            <h3>{{ calendarMonthLabel }}</h3>
          </div>
          <span>주요 공개·점검 일정</span>
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
              <a
                v-for="event in cell.events"
                :key="event.id"
                :href="event.link"
                class="calendar-event-pill"
                :class="event.tone"
                target="_blank"
                rel="noreferrer"
              >
                {{ event.category }}
              </a>
            </div>
          </div>
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
