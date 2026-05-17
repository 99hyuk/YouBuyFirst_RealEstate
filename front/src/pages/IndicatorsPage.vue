<script setup lang="ts">
import dashboardSummary from '../fixtures/dashboard-summary.json';

const formatPct = (value: number) => `${value > 0 ? '+' : ''}${value}%`;
const trendClass = (trend: string) => (trend === 'down' ? 'down' : 'up');
</script>

<template>
  <section class="page-grid indicator-page">
    <div class="page-heading span-2">
      <p class="eyebrow">market indicators</p>
      <h2>주요 지표</h2>
      <p>지수, 환율, 금리, 원자재, 심리 지표를 mock 데이터로 모아 보는 화면입니다.</p>
    </div>

    <section class="panel span-2">
      <div class="panel-header">
        <div>
          <p class="label">market pulse</p>
          <h3>실시간 주요 지표</h3>
        </div>
        <span class="status-pill warning">mock · 지연 가능</span>
      </div>
      <div class="indicator-grid">
        <article
          v-for="indicator in dashboardSummary.marketIndicators"
          :key="indicator.label"
          :class="['indicator-card', trendClass(indicator.trend)]"
        >
          <div class="indicator-copy">
            <span>{{ indicator.label }}</span>
            <strong>{{ indicator.value }}</strong>
            <em>{{ formatPct(indicator.changePct) }}</em>
          </div>
          <svg viewBox="0 0 128 48" aria-hidden="true">
            <polyline :points="indicator.pointString" />
          </svg>
          <small>{{ indicator.updatedLabel }}</small>
        </article>
      </div>
    </section>

    <section class="panel span-2">
      <div class="panel-header">
        <div>
          <p class="label">macro dashboard</p>
          <h3>매크로 지표 자세히 보기</h3>
        </div>
        <span class="status-pill">카테고리 mock</span>
      </div>
      <div class="macro-tabs" aria-label="매크로 카테고리">
        <span>달러·금리</span>
        <span>환율</span>
        <span>원자재</span>
        <span>글로벌 지수</span>
        <span>심리</span>
      </div>
      <div class="macro-matrix">
        <article
          v-for="metric in dashboardSummary.macroMetrics"
          :key="`${metric.category}-${metric.name}`"
          :class="['macro-metric-card', trendClass(metric.trend)]"
        >
          <span>{{ metric.category }}</span>
          <strong>{{ metric.name }}</strong>
          <em>{{ metric.value }}</em>
          <small>{{ metric.changeLabel }}</small>
          <svg viewBox="0 0 112 40" aria-hidden="true">
            <polyline :points="metric.pointString" />
          </svg>
        </article>
      </div>
    </section>
  </section>
</template>
