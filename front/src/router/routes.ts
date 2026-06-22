import type { RouteRecordRaw } from 'vue-router';

import DashboardPage from '../pages/DashboardPage.vue';
import IndicatorsPage from '../pages/IndicatorsPage.vue';
import NewsroomPage from '../pages/NewsroomPage.vue';
import RegionDetailPage from '../pages/RegionDetailPage.vue';
import RegionReactionPage from '../pages/RegionReactionPage.vue';
import WatchlistPage from '../pages/WatchlistPage.vue';

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
    path: '/realestate/map/:regionId',
    name: 'realestate-map-region',
    component: () => import('../pages/RealEstateMapPage.vue')
  },
  {
    path: '/realestate/complexes',
    name: 'realestate-complexes',
    component: () => import('../pages/ComplexBrowsePage.vue')
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
    path: '/realestate/targets/:targetId',
    name: 'region-detail',
    component: RegionDetailPage
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
    path: '/realestate/watchlist',
    name: 'realestate-watchlist',
    component: WatchlistPage
  }
];
