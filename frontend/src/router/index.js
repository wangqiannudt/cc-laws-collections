import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Search from '../views/Search.vue'
import Detail from '../views/Detail.vue'
import Timeline from '../views/Timeline.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/search',
    name: 'Search',
    component: Search,
  },
  {
    path: '/law/:id',
    name: 'Detail',
    component: Detail,
  },
  {
    path: '/timeline',
    name: 'Timeline',
    component: Timeline,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
