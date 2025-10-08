import axios from 'axios'
import { API_BASE_URL, REQUEST_TIMEOUT } from '../config'

// Helper to get current token (single source of truth: localStorage for now)
function getStoredToken() {
  return localStorage.getItem('steam_token')
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT
})

// Attach auth header if token exists
apiClient.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for global auth handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('steam_token')
      // Soft reload to reset state
      if (window.location.pathname !== '/') {
        window.location.href = '/'
      } else {
        window.location.reload()
      }
    }
    return Promise.reject(error)
  }
)
