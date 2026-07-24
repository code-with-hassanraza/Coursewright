import axios from 'axios'

// Falls back to localhost:8000 for local dev; override via .env → VITE_API_URL
// for staging/prod builds without touching this file.
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// /auth/login and /auth/register can legitimately return 401/400 for
// "wrong password" or "email taken" — those are ordinary form errors the
// calling page catches and displays inline. They must NOT trigger the
// global forced-logout-and-redirect below, or the Login page would bounce
// itself back to /login the moment someone typos their password.
const AUTH_ENDPOINTS = ['/auth/login', '/auth/register']

function isAuthEndpoint(url = '') {
  return AUTH_ENDPOINTS.some((endpoint) => url.includes(endpoint))
}

// Attach the bearer token to every outgoing request.
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Global session handling: a 401 on any *protected* endpoint means the
// token expired or was rejected — clear it and send the user back to
// /login. Guarded so it can't loop (skips if already on /login) and
// skips the auth endpoints themselves (see note above).
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const requestUrl = error.config?.url

    if (status === 401 && !isAuthEndpoint(requestUrl)) {
      localStorage.removeItem('access_token')
      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }

    return Promise.reject(error)
  },
)

export default api