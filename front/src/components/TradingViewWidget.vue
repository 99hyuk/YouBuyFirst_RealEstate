<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

const props = withDefaults(
  defineProps<{
    symbol: string;
    title: string;
    marketLabel: string;
    note: string;
  }>(),
  {}
);

const widgetContainer = ref<HTMLDivElement | null>(null);
const isTestMode = typeof window !== 'undefined' && window.navigator.userAgent.includes('jsdom');

const widgetConfig = computed(() => ({
  autosize: true,
  symbol: props.symbol,
  interval: 'D',
  timezone: 'Asia/Seoul',
  theme: 'light',
  style: '1',
  locale: 'kr',
  withdateranges: true,
  hide_side_toolbar: false,
  allow_symbol_change: true,
  save_image: false,
  calendar: false,
  support_host: 'https://www.tradingview.com'
}));

const renderWidget = async () => {
  await nextTick();

  if (!widgetContainer.value || isTestMode) {
    return;
  }

  widgetContainer.value.innerHTML = '';

  const widgetSlot = document.createElement('div');
  widgetSlot.className = 'tradingview-widget-container__widget';
  widgetContainer.value.appendChild(widgetSlot);

  const script = document.createElement('script');
  script.type = 'text/javascript';
  script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
  script.async = true;
  script.textContent = JSON.stringify(widgetConfig.value);
  widgetContainer.value.appendChild(script);
};

onMounted(renderWidget);
watch(() => props.symbol, renderWidget);

onBeforeUnmount(() => {
  if (widgetContainer.value) {
    widgetContainer.value.innerHTML = '';
  }
});
</script>

<template>
  <article class="tradingview-test-card">
    <div class="tradingview-test-card__header">
      <div>
        <span>{{ marketLabel }}</span>
        <strong>{{ title }}</strong>
      </div>
      <em>{{ symbol }}</em>
    </div>

    <div ref="widgetContainer" class="tradingview-widget-container stock-tradingview-widget">
      <div class="tv-widget-fallback">
        <strong>{{ symbol }}</strong>
        <span>TradingView widget loading</span>
      </div>
    </div>

    <div class="tradingview-widget-copyright">
      <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">
        Track all markets on TradingView
      </a>
    </div>

    <p>{{ note }}</p>
  </article>
</template>
