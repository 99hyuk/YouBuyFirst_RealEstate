import type { RouteRecordRaw } from 'vue-router';

import DashboardPage from '../pages/DashboardPage.vue';
import IndicatorsPage from '../pages/IndicatorsPage.vue';
import NewsroomPage from '../pages/NewsroomPage.vue';
import PortfolioPage from '../pages/PortfolioPage.vue';
import RegionDetailPage from '../pages/RegionDetailPage.vue';
import RegionReactionPage from '../pages/RegionReactionPage.vue';

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
    path: '/realestate/map',
    name: 'realestate-map',
    component: () => import('../pages/RealEstateMapPage.vue')
  },
  {
    path: '/newsroom',
    name: 'newsroom',
    component: NewsroomPage
  },
  {
    path: '/realestate/reactions',
    name: 'region-reactions',
    component: RegionReactionPage
  },
  {
    path: '/realestate/targets/:symbol',
    name: 'region-detail',
    component: RegionDetailPage
  },
  {
    path: '/stocks',
    name: 'legacy-region-reactions',
    redirect: '/realestate/reactions'
  },
  {
    path: '/stocks/:symbol',
    name: 'legacy-region-detail',
    redirect: (to) => ({
      path: `/realestate/targets/${String(to.params.symbol ?? '')}`,
      query: to.query
    })
  },
  {
    path: '/communities',
    name: 'legacy-community-reactions',
    redirect: (to) => ({
      path: '/realestate/reactions',
      query: to.query
    })
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
      path: '/realestate/reactions',
      query: { view: 'agents' }
    }
  },
  {
    path: '/portfolio',
    name: 'portfolio',
    component: PortfolioPage
  }
];
