<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  fetchLatestRealEstateDailyBriefing,
  type RealEstateDailyBriefing
} from '../lib/realestate-daily-briefing';

const briefing = ref<RealEstateDailyBriefing | null>(null);
const loadState = ref<'loading' | 'live' | 'empty' | 'error'>('loading');

const sortedSections = computed(() =>
  [...(briefing.value?.sections ?? [])].sort((left, right) => left.displayOrder - right.displayOrder)
);
const sortedFocusRegions = computed(() =>
  [...(briefing.value?.focusRegions ?? [])].sort((left, right) => Number(left.displayOrder ?? 100) - Number(right.displayOrder ?? 100))
);
const sortedSourceItems = computed(() =>
  [...(briefing.value?.sourceItems ?? [])].sort((left, right) => {
    const leftHasUrl = Boolean(left.url);
    const rightHasUrl = Boolean(right.url);
    if (leftHasUrl !== rightHasUrl) return leftHasUrl ? -1 : 1;
    return left.displayOrder - right.displayOrder;
  })
);
const sectionsById = computed(() => new Map(sortedSections.value.map((section) => [section.sectionId, section])));
const primarySection = computed(() => sectionsById.value.get('flow') ?? sortedSections.value[0] ?? null);
const regionSection = computed(() => sectionsById.value.get('regions') ?? null);
const variableSection = computed(() => sectionsById.value.get('variables') ?? null);
const sourceSection = computed(() => sectionsById.value.get('sources') ?? null);
const headlineRoles = ['핵심 신호', '지역 흐름', '시장 변수'];
const relatedEvidenceLinks = [
  {
    id: 'newsroom-news',
    label: '뉴스룸',
    title: '최근 뉴스 확인',
    description: '브리핑에 언급된 이슈 후보 원문',
    to: { path: '/newsroom', query: { feed: 'news' } }
  },
  {
    id: 'newsroom-reports',
    label: '정책·통계 리포트',
    title: '리포트 근거 확인',
    description: '공공·연구기관 리포트 모음',
    to: { path: '/newsroom', query: { feed: 'reports' } }
  },
  {
    id: 'indicators',
    label: '주요 일정',
    title: '공식 발표 일정',
    description: '통계·청약·정책 일정 확인',
    to: { path: '/indicators' }
  },
  {
    id: 'map',
    label: '전국 지역 지도',
    title: '지역 흐름 비교',
    description: '시도별 가격·거래 흐름 확인',
    to: { path: '/realestate/map' }
  }
];
const splitBriefingPoints = (body?: string | null) => {
  const normalized = String(body ?? '').replace(/\s+/g, ' ').trim();
  if (!normalized) return [];
  return normalized
    .split(/(?<=\.)\s+|•\s*|\n+/)
    .map((point) => point.trim())
    .filter(Boolean)
    .slice(0, 3);
};
const splitBriefingParagraphs = (body?: string | null) => {
  const raw = String(body ?? '').trim();
  if (!raw) return [];
  const explicitParagraphs = raw
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.replace(/\s+/g, ' ').trim())
    .filter(Boolean);
  if (explicitParagraphs.length > 1) return explicitParagraphs;
  return raw
    .replace(/\s+/g, ' ')
    .split(/(?<=\.)\s+/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
};
const primaryParagraphs = computed(() => splitBriefingParagraphs(primarySection.value?.body));
const primaryLead = computed(() => primaryParagraphs.value[0] ?? primarySection.value?.body ?? '');
const primaryBodyParagraphs = computed(() => primaryParagraphs.value.slice(1));
const regionPoints = computed(() => splitBriefingPoints(regionSection.value?.body));
const variablePoints = computed(() => splitBriefingPoints(variableSection.value?.body));
const generatedLabel = computed(() => {
  if (!briefing.value?.generatedAt) return '';
  const generatedAt = new Date(briefing.value.generatedAt);
  if (Number.isNaN(generatedAt.getTime())) return '';
  return generatedAt.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
});
const briefingDateLabel = computed(() => {
  if (!briefing.value?.briefingDate) return '';
  const briefingDate = new Date(`${briefing.value.briefingDate}T00:00:00`);
  if (Number.isNaN(briefingDate.getTime())) return briefing.value.briefingDate;
  return briefingDate.toLocaleDateString('ko-KR', {
    month: '2-digit',
    day: '2-digit'
  });
});

const loadBriefing = async () => {
  loadState.value = 'loading';
  try {
    const latest = await fetchLatestRealEstateDailyBriefing();
    briefing.value = latest;
    loadState.value = latest ? 'live' : 'empty';
  } catch {
    briefing.value = null;
    loadState.value = 'error';
  }
};

onMounted(() => {
  void loadBriefing();
});
</script>

<template>
  <main class="daily-briefing-detail-page">
    <section class="daily-briefing-hero-panel">
      <div class="daily-briefing-hero-copy">
        <p class="label">Daily briefing</p>
        <h1>{{ briefing?.title ?? '오늘의 부동산 시장 브리핑' }}</h1>
        <p>시장 흐름 · 지역 · 변수 · 근거 요약</p>
      </div>
      <div class="daily-briefing-meta-board" aria-label="브리핑 기준 정보">
        <span>
          기준일
          <strong>{{ briefingDateLabel || '-' }}</strong>
        </span>
        <span>
          생성
          <strong>{{ generatedLabel || '-' }}</strong>
        </span>
        <span>
          헤드라인
          <strong>{{ briefing?.summaryHeadlines.length ?? 0 }}개</strong>
        </span>
      </div>
    </section>

    <p v-if="loadState === 'loading'" class="daily-briefing-detail-state">브리핑을 불러오는 중입니다.</p>
    <p v-else-if="loadState === 'error'" class="daily-briefing-detail-state">브리핑 갱신 상태를 확인해야 합니다.</p>
    <p v-else-if="loadState === 'empty'" class="daily-briefing-detail-state">브리핑 생성 대기</p>

    <template v-if="briefing">
      <section class="daily-briefing-headline-grid" aria-label="대시보드 핵심 헤드라인">
        <article
          v-for="(headline, index) in briefing.summaryHeadlines"
          :key="headline"
          class="daily-briefing-headline-card"
        >
          <span class="daily-briefing-headline-index">{{ String(index + 1).padStart(2, '0') }}</span>
          <div>
            <small>{{ headlineRoles[index] ?? '핵심' }}</small>
            <strong>{{ headline }}</strong>
          </div>
        </article>
      </section>

      <section class="daily-briefing-report-layout" aria-label="일일 브리핑 본문">
        <article class="daily-briefing-primary-panel" aria-labelledby="daily-briefing-primary-title">
          <div class="daily-briefing-panel-heading">
            <span aria-hidden="true"></span>
            <p>마켓 컬럼</p>
          </div>
          <h2 id="daily-briefing-primary-title">{{ primarySection?.title ?? '오늘의 핵심 흐름' }}</h2>
          <p class="daily-briefing-column-lead">{{ primaryLead }}</p>
          <div v-if="primaryBodyParagraphs.length" class="daily-briefing-column-body">
            <p v-for="paragraph in primaryBodyParagraphs" :key="paragraph">{{ paragraph }}</p>
          </div>
          <div class="daily-briefing-signal-strip" aria-label="핵심 헤드라인 재정리">
            <span v-for="headline in briefing.summaryHeadlines" :key="`signal-${headline}`">{{ headline }}</span>
          </div>
        </article>

        <aside class="daily-briefing-side-stack">
          <section class="daily-briefing-compact-panel" aria-labelledby="daily-briefing-regions-title">
            <div class="daily-briefing-compact-heading">
              <p id="daily-briefing-regions-title">{{ regionSection?.title ?? '주목할 지역과 이유' }}</p>
              <strong>{{ sortedFocusRegions.length || regionPoints.length }}</strong>
            </div>
            <ol v-if="sortedFocusRegions.length" class="daily-briefing-region-ledger">
              <li
                v-for="(region, index) in sortedFocusRegions.slice(0, 5)"
                :key="region.targetId ?? region.label"
              >
                <span>{{ String(index + 1).padStart(2, '0') }}</span>
                <div>
                  <strong>{{ region.label }}</strong>
                  <em>{{ region.reason || '브리핑 본문 언급' }}</em>
                </div>
              </li>
            </ol>
            <ul v-else class="daily-briefing-region-ledger">
              <li v-for="(point, index) in regionPoints" :key="point">
                <span>{{ String(index + 1).padStart(2, '0') }}</span>
                <div>
                  <strong>{{ point }}</strong>
                </div>
              </li>
            </ul>
          </section>

          <section class="daily-briefing-compact-panel" aria-labelledby="daily-briefing-variables-title">
            <div class="daily-briefing-compact-heading">
              <p id="daily-briefing-variables-title">{{ variableSection?.title ?? '시장 변수' }}</p>
              <strong>{{ variablePoints.length || 1 }}</strong>
            </div>
            <ul class="daily-briefing-variable-list">
              <li
                v-for="point in (variablePoints.length ? variablePoints : [variableSection?.body ?? '확인할 시장 변수가 정리되는 중입니다.'])"
                :key="point"
              >
                <span aria-hidden="true"></span>
                <strong>{{ point }}</strong>
              </li>
            </ul>
          </section>
        </aside>
      </section>

      <section
        class="daily-briefing-source-panel"
        aria-label="관련 뉴스와 리포트"
      >
        <div class="daily-briefing-source-heading">
          <div>
            <p>{{ sortedSourceItems.length ? (sourceSection?.title ?? '관련 뉴스·리포트') : '관련 확인 화면' }}</p>
            <strong>{{ sortedSourceItems.length ? `${sortedSourceItems.length}개 원문 근거` : '내부 자료로 이어보기' }}</strong>
          </div>
        </div>
        <p v-if="sourceSection?.body" class="daily-briefing-source-summary">{{ sourceSection.body }}</p>
        <div v-if="sortedSourceItems.length" class="daily-briefing-source-ledger">
          <a
            v-for="item in sortedSourceItems"
            :key="item.sourceItemId"
            class="daily-briefing-source-row"
            :href="item.url ?? undefined"
            target="_blank"
            rel="noreferrer"
          >
            <span>{{ item.label || item.sourceType }}</span>
            <strong>{{ item.title }}</strong>
          </a>
        </div>
        <div class="daily-briefing-related-links" aria-label="사이트 안 관련 정보">
          <RouterLink
            v-for="link in relatedEvidenceLinks"
            :key="link.id"
            class="daily-briefing-related-link"
            :to="link.to"
          >
            <span>{{ link.label }}</span>
            <strong>{{ link.title }}</strong>
            <em>{{ link.description }}</em>
          </RouterLink>
        </div>
      </section>
    </template>
  </main>
</template>
