import request from '@/api/request.js'

const BASE = '/auth'

export const authApi = {
  login(username, password) {
    return request.post(`${BASE}/login`, { username, password }).then(res => {
      // Save token + user to localStorage
      localStorage.setItem('token', res.access_token)
      localStorage.setItem('user', JSON.stringify(res.user))
      return res
    })
  },
  logout() {
    return request.post(`${BASE}/logout`).finally(() => {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }).catch(() => {
      // Even if logout API fails, clear local state
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    })
  },
}

// JWT helpers — decode payload without server verification
export function decodeTokenPayload() {
  const token = localStorage.getItem('token')
  if (!token) return null
  try {
    const payload = token.split('.')[1]
    const decoded = atob(payload)
    return JSON.parse(decoded)
  } catch {
    return null
  }
}

// Check if token has expired (30s safety buffer)
export function isTokenExpired() {
  const payload = decodeTokenPayload()
  if (!payload || !payload.exp) return true
  return Date.now() >= payload.exp * 1000 - 30000
}
