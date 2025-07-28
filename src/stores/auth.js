import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '../api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('steam_token'))
  const user = ref(null)
  const loading = ref(false)
  const needsFirstTimeSetup = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isSuperAdmin = computed(() => user.value?.permission?.is_super_admin || false)
  const canParticipateMatch = computed(() =>
    user.value?.permission?.can_participate_match &&
    !user.value?.permission?.is_banned
  )

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('steam_token', newToken)
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
  }

  function clearToken() {
    token.value = null
    user.value = null
    needsFirstTimeSetup.value = false
    localStorage.removeItem('steam_token')
    delete apiClient.defaults.headers.common['Authorization']
  }

  function loadToken() {
    if (token.value) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      fetchProfile()
    }
  }

  async function fetchProfile() {
    if (!token.value) return

    loading.value = true
    try {
      const response = await apiClient.get('/auth/profile')
      user.value = response.data
      needsFirstTimeSetup.value = response.data.is_first_time_setup
    } catch (error) {
      console.error('Failed to fetch profile:', error)
      clearToken()
    } finally {
      loading.value = false
    }
  }

  async function completeFirstTimeSetup(setupData) {
    try {
      const response = await apiClient.post('/auth/first-time-setup', setupData)
      user.value = response.data.user
      needsFirstTimeSetup.value = false
      return { success: true }
    } catch (error) {
      console.error('First time setup failed:', error)
      return {
        success: false,
        error: error.response?.data?.detail || '设置失败，请重试'
      }
    }
  }

  function logout() {
    clearToken()
  }

  return {
    token,
    user,
    loading,
    needsFirstTimeSetup,
    isAuthenticated,
    isSuperAdmin,
    canParticipateMatch,
    setToken,
    clearToken,
    loadToken,
    fetchProfile,
    completeFirstTimeSetup,
    logout
  }
})
