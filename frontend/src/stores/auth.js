import { defineStore } from 'pinia'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('tma_token') || null,
    user: JSON.parse(localStorage.getItem('tma_user') || 'null'),
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token && !!state.user,
    userRole: (state) => state.user?.role || null,
    isAdmin: (state) => state.user?.role === 'admin',
    isStaff: (state) => state.user?.role === 'staff',
    isTrekker: (state) => state.user?.role === 'user',
    staffApproved: (state) => state.user?.role === 'staff' && state.user?.is_approved
  },

  actions: {
    async login(email, password) {
      this.loading = true
      this.error = null
      try {
        const response = await api.post('/auth/login', { email, password })
        const { access_token, user } = response.data

        this.token = access_token
        this.user = user
        localStorage.setItem('tma_token', access_token)
        localStorage.setItem('tma_user', JSON.stringify(user))

        return user
      } catch (err) {
        this.error = err.response?.data?.error || 'Login failed. Please check credentials.'
        throw this.error
      } finally {
        this.loading = false
      }
    },

    async register(payload) {
      this.loading = true
      this.error = null
      try {
        const response = await api.post('/auth/register', payload)
        const { access_token, user } = response.data

        if (user.role === 'user') {
          this.token = access_token
          this.user = user
          localStorage.setItem('tma_token', access_token)
          localStorage.setItem('tma_user', JSON.stringify(user))
        }

        return user
      } catch (err) {
        this.error = err.response?.data?.error || 'Registration failed.'
        throw this.error
      } finally {
        this.loading = false
      }
    },

    async fetchCurrentUser() {
      if (!this.token) return
      try {
        const response = await api.get('/auth/me')
        this.user = response.data.user
        localStorage.setItem('tma_user', JSON.stringify(this.user))
      } catch (err) {
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('tma_token')
      localStorage.removeItem('tma_user')
    }
  }
})

