<script setup lang="ts">
import stockDetail from '../fixtures/stock-detail-samsung.json';
</script>

<template>
  <section class="page-grid">
    <div class="page-heading span-2">
      <p class="eyebrow">Stock detail shell</p>
      <h2>{{ stockDetail.name }} · {{ stockDetail.symbol }}</h2>
      <p>특정 종목의 커뮤니티 반응과 mock 가격 상태를 함께 확인하는 자리입니다.</p>
    </div>

    <section class="panel">
      <p class="label">quote placeholder</p>
      <h3>{{ stockDetail.quote.price.toLocaleString() }}원</h3>
      <p>등락률 {{ stockDetail.quote.changePct }}%</p>
      <span :class="['status-pill', stockDetail.quote.stale ? 'warning' : '']">
        {{ stockDetail.quote.stale ? 'stale quote' : 'mock quote' }}
      </span>
    </section>

    <section class="panel">
      <p class="label">reaction direction</p>
      <h3>{{ stockDetail.reactionSummary.directionLabel }}</h3>
      <p>언급 {{ stockDetail.reactionSummary.mentionCount }}건 · 열기 후보 {{ stockDetail.reactionSummary.heatScore }}</p>
    </section>

    <section class="panel span-2">
      <p class="label">source breakdown</p>
      <h3>소스별 반응 분포</h3>
      <div class="ranking-list">
        <article v-for="source in stockDetail.sourceBreakdown" :key="source.source" class="ranking-row">
          <strong>{{ source.sourceLabel }}</strong>
          <span>{{ source.mentionCount }}건</span>
          <span>{{ source.dominantDirectionLabel }}</span>
        </article>
      </div>
    </section>
  </section>
</template>
