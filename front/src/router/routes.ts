import type { RouteRecordRaw } from 'vue-router';

import CommunitiesPage from '../pages/CommunitiesPage.vue';
import DashboardPage from '../pages/DashboardPage.vue';
import IndicatorsPage from '../pages/IndicatorsPage.vue';
import NewsroomPage from '../pages/NewsroomPage.vue';
import PortfolioPage from '../pages/PortfolioPage.vue';
import StockDetailPage from '../pages/StockDetailPage.vue';
import StockListPage from '../pages/StockListPage.vue';

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardPage
  },
  {
    path: '/newsroom',
    name: 'newsroom',
    component: NewsroomPage
  },
  {
    path: '/stocks',
    name: 'stocks',
    component: StockListPage
  },
  {
    path: '/stocks/:symbol',
    name: 'stock-detail',
    component: StockDetailPage
  },
  {
    path: '/communities',
    name: 'communities',
    component: CommunitiesPage
  },
  {
    path: '/indicators',
    name: 'indicators',
    component: IndicatorsPage
  },
  {
    path: '/indicators/:category',
    name: 'indicator-detail',
    component: IndicatorsPage
  },
  {
    path: '/agents',
    name: 'agents',
    redirect: {
      path: '/communities',
      query: { view: 'agents' }
    }
  },
  {
    path: '/portfolio',
    name: 'portfolio',
    component: PortfolioPage
  }
];
