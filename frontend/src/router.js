import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import DeviationDetail from '../views/DeviationDetail.vue'

const routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/deviation/:id', name: 'detail', component: DeviationDetail }
]

export default createRouter({
  history: createWebHistory(),
  routes
})