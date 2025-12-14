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
  timeout: 300000, // 5 minutes timeout for long operations like data generation
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
      // Handle unauthorized - redirect to dashboard (no auth required for dev)
      // But don't redirect if we're already on a page that doesn't require auth
      const currentPath = window.location.pathname
      const publicPaths = ['/dashboard', '/cds', '/patients', '/patient-data', '/ml-models', '/mri', '/monitoring', '/settings']
      
      if (!publicPaths.includes(currentPath)) {
        localStorage.removeItem('auth_token')
        // Use navigate if available, otherwise redirect
        if (currentPath !== '/dashboard') {
          window.location.href = '/dashboard'
        }
      }
      // For public paths, just log the error but don't redirect
      console.warn('API 401 error on public path:', currentPath, error)
    }
    // Log errors for debugging
    if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.code === 'ERR_NETWORK') {
      console.error('API Connection Error:', error.message)
      console.error('API Base URL:', apiBaseURL)
      console.error('Make sure backend is running on http://localhost:8001')
      console.error('Full error:', error)
    }
    // Handle timeout errors
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      console.error('API Timeout Error:', error.message)
      console.error('Request took too long. The backend might be processing a large operation.')
    }
    return Promise.reject(error)
  }
)

export default api

