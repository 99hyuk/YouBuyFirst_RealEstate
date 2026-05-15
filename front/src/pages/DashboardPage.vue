<script setup lang="ts">
import dashboardSummary from '../fixtures/dashboard-summary.json';
import quoteSnapshots from '../fixtures/quote-snapshots.json';
import reactionRanking from '../fixtures/reaction-ranking.json';
</script>

<template>
  <section class="page-grid">
    <div class="page-heading">
      <p class="eyebrow">Dashboard</p>
      <h2>{{ dashboardSummary.title }}</h2>
      <p>{{ dashboardSummary.description }}</p>
    </div>

    <section class="panel span-2" aria-labelledby="ranking-title">
      <div class="panel-header">
        <div>
          <p class="label">mock data</p>
          <h3 id="ranking-title">커뮤니티 반응 랭킹</h3>
        </div>
        <span class="status-pill">{{ reactionRanking.windowLabel }}</span>
      </div>
      <div class="ranking-list">
        <article v-for="item in reactionRanking.items" :key="item.symbol" class="ranking-row">
          <div>
            <strong>{{ item.name }}</strong>
            <span>{{ item.symbol }} · {{ item.market }}</span>
          </div>
          <div class="metric">
            <strong>{{ item.heatScore }}</strong>
            <span>열기 후보</span>
          </div>
          <div class="metric">
            <strong>{{ item.mentionCount }}</strong>
            <span>언급</span>
          </div>
          <div class="tags">
            <span v-for="keyword in item.topKeywords" :key="keyword">{{ keyword }}</span>
          </div>
        </article>
      </div>
    </section>

    <section class="panel" aria-labelledby="quote-title">
      <div class="panel-header">
        <div>
          <p class="label">market placeholder</p>
          <h3 id="quote-title">가격 상태</h3>
        </div>
      </div>
      <article v-for="quote in quoteSnapshots.items" :key="quote.symbol" class="quote-row">
        <strong>{{ quote.name }}</strong>
        <span>{{ quote.price.toLocaleString() }}원</span>
        <span :class="['status-pill', quote.stale ? 'warning' : '']">
          {{ quote.stale ? 'stale quote' : 'mock quote' }}
        </span>
      </article>
    </section>

    <section class="panel" aria-labelledby="confirm-title">
      <div class="panel-header">
        <div>
          <p class="label">planning boundary</p>
          <h3 id="confirm-title">기획자 확인 필요</h3>
        </div>
      </div>
      <ul class="check-list">
        <li v-for="item in dashboardSummary.confirmationNeeded" :key="item">{{ item }}</li>
      </ul>
    </section>
  </section>
</template>
