import axios from 'axios'
import { ElMessage } from 'element-plus'
const request = axios.create({
  baseURL: '/admin/api',
  timeout: 30000,
})

// Attach auth token to every request
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// Handle 401 — single-device login: force re-login
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      ElMessage.error('Session expired. Please log in again.')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      const router = window.__router__
      if (router) {
        const route = router.currentRoute.value
        if (route.name !== 'Login') {
          router.replace({
            name: 'Login',
            query: { redirect: route.fullPath },
          })
        }
      }
    } else {
      let msg = error.response?.data?.detail || error.message || 'Request failed'
      if (Array.isArray(msg)) {
        msg = msg.map(e => e.msg || e).join('; ')
      }
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default request
