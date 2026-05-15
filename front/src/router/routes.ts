import type { RouteRecordRaw } from 'vue-router';

import AgentsPage from '../pages/AgentsPage.vue';
import CommunitiesPage from '../pages/CommunitiesPage.vue';
import DashboardPage from '../pages/DashboardPage.vue';
import PortfolioPage from '../pages/PortfolioPage.vue';
import StockDetailPage from '../pages/StockDetailPage.vue';

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
    path: '/agents',
    name: 'agents',
    component: AgentsPage
  },
  {
    path: '/portfolio',
    name: 'portfolio',
    component: PortfolioPage
  }
];
