import api from './api'

/**
 * POST /auth/login — CRITICAL: the backend expects form-urlencoded data with
 * a field literally named "username", not JSON and not "email". This is the
 * one place that translation happens; everywhere else in the app just calls
 * login(email, password) and never thinks about it again.
 *
 * @param {{ email: string, password: string }} credentials
 * @returns {Promise<{ access_token: string, token_type: string }>}
 */
export async function login({ email, password }) {
  const body = new URLSearchParams()
  body.append('username', email)
  body.append('password', password)

  const { data } = await api.post('/auth/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

/**
 * POST /auth/register — plain JSON, unlike login. Passed straight through so
 * the field list (email, full_name, password, degree?, year_of_study?) only
 * has to be maintained on the calling page (Signup.jsx), not duplicated here.
 *
 * @param {{ email: string, full_name: string, password: string, degree?: string, year_of_study?: number|string }} payload
 * @returns {Promise<{ access_token: string, token_type: string }>}
 */
export async function register(payload) {
  const { data } = await api.post('/auth/register', payload)
  return data
}

/**
 * GET /auth/me — protected. Used both on app-load bootstrap and right after
 * login/register, since neither of those returns the user object itself.
 *
 * @returns {Promise<import('../types').UserResponse>}
 */
export async function getCurrentUser() {
  const { data } = await api.get('/auth/me')
  return data
}