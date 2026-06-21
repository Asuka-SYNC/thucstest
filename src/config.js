// Centralized runtime configuration for frontend
// Uses Vite env variables (prefixed with VITE_) with sensible fallbacks

const _wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || `${_wsProtocol}//${window.location.host}`

export const REQUEST_TIMEOUT = 10000

export const STEAM_AUTH_URL = `${API_BASE_URL}/auth/steam`

