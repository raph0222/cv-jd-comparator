import axios from 'axios'

const apiBaseURL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000').replace(
  /\/+$/,
  ''
)

const instance = axios.create({
  baseURL: apiBaseURL
})

instance.interceptors.request.use(
  (config) => {
    const path = String(config.url || '')
    if (!path.startsWith('/api')) {
      config.baseURL = typeof window !== 'undefined' ? window.location.origin : apiBaseURL
    }
    return config
  },
  (error) => Promise.reject(error)
)

export default instance
