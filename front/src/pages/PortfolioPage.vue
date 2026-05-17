<script setup lang="ts">
import portfolioState from '../fixtures/portfolio-disabled.json';

const formatPct = (value: number) => `${value > 0 ? '+' : ''}${value}%`;
</script>

<template>
  <section class="page-grid">
    <div class="page-heading span-2">
      <p class="eyebrow">mock portfolio</p>
      <h2>{{ portfolioState.title }}</h2>
      <p>{{ portfolioState.description }}</p>
    </div>

    <section class="panel portfolio-summary">
      <p class="label">overview</p>
      <h3>{{ portfolioState.message }}</h3>
      <div class="portfolio-kpis">
        <div>
          <span>{{ portfolioState.cashLabel }}</span>
          <strong>{{ portfolioState.cashValue }}</strong>
        </div>
        <div>
          <span>모의 수익률</span>
          <strong>{{ formatPct(portfolioState.totalReturnPct) }}</strong>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <p class="label">holdings</p>
          <h3>보유 종목</h3>
        </div>
        <span class="status-pill warning">mock</span>
      </div>
      <div class="compact-list">
        <div v-for="holding in portfolioState.holdings" :key="holding.symbol" class="compact-row">
          <strong>{{ holding.name }}</strong>
          <span>{{ holding.weightPct }}%</span>
          <span :class="['status-pill', holding.mockReturnPct < 0 ? 'warning' : '']">
            {{ formatPct(holding.mockReturnPct) }}
          </span>
        </div>
      </div>
    </section>
  </section>
</template>
