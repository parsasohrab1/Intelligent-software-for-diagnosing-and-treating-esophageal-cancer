import axios from 'axios'

// Use Vite proxy (always use relative path to go through proxy)
// @ts-ignore - Vite env types
// Force use of proxy by ignoring VITE_API_BASE_URL if it's an absolute URL
const envUrl = import.meta.env.VITE_API_BASE_URL
const apiBaseURL = (envUrl && !envUrl.startsWith('http')) ? envUrl : '/api/v1'

const api = axios.create({
  baseURL: apiBaseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds timeout
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    // Log errors for debugging
    if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.code === 'ERR_NETWORK') {
      console.error('API Connection Error:', error.message)
      console.error('API Base URL:', apiBaseURL)
      console.error('Make sure backend is running on http://localhost:8001')
      console.error('Full error:', error)
    }
    return Promise.reject(error)
  }
)

export default api

