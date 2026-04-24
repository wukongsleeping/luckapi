import { defineStore } from 'pinia'
import { decodeTokenPayload, isTokenExpired } from '@/api/auth.js'
import request from '@/api/request.js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
  }),

  getters: {
    isAuthenticated: () => {
      const token = localStorage.getItem('token')
      if (!token) return false
      return !isTokenExpired()
    },
    currentUserId: (state) => state.user?.id || null,
  },

  actions: {
    setUser(user) {
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },

    clearUser() {
      this.user = null
      localStorage.removeItem('user')
    },

    async refreshUserData() {
      try {
        const user = await request.get('/auth/me')
        this.user = user
        localStorage.setItem('user', JSON.stringify(user))
        return user
      } catch {
        this.clearUser()
        return null
      }
    },

    async autoLogin() {
      const token = localStorage.getItem('token')
      if (!token || isTokenExpired()) {
        this.clearUser()
        return false
      }
      await this.refreshUserData()
      return this.isAuthenticated
    },
  },
})
