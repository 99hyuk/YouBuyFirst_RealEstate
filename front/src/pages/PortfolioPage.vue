<script setup lang="ts">
import portfolioState from '../fixtures/portfolio-disabled.json';
</script>

<template>
  <section class="page-grid">
    <div class="page-heading span-2">
      <p class="eyebrow">Portfolio shell</p>
      <h2>{{ portfolioState.title }}</h2>
      <p>{{ portfolioState.description }}</p>
    </div>

    <section class="panel span-2 disabled-panel">
      <p class="label">disabled shell</p>
      <h3>{{ portfolioState.message }}</h3>
      <ul class="check-list">
        <li v-for="item in portfolioState.futureWidgets" :key="item">{{ item }}</li>
      </ul>
    </section>
  </section>
</template>
