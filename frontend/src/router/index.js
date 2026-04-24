import { createRouter, createWebHistory } from 'vue-router'
import { decodeTokenPayload, isTokenExpired } from '@/api/auth.js'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('@/components/layout/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/users',
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('@/views/Models.vue'),
      },
      {
        path: 'groups',
        name: 'Groups',
        component: () => import('@/views/Groups.vue'),
      },
      {
        path: 'qa-records',
        name: 'QaRecords',
        component: () => import('@/views/QaRecords.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Expose router globally for auth interceptor
window.__router__ = router

// Auth guard
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')

  // Protected route without token → redirect to login
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // Expired token → redirect to login
  if (token && isTokenExpired()) {
    localStorage.removeItem('token')
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // Already logged in, trying to access login page → redirect to home
  if (to.meta.guest && token) {
    next('/users')
    return
  }

  next()
})

export default router
