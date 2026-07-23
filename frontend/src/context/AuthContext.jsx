import { createContext, useState, useEffect, useCallback, useMemo } from 'react'
import * as authService from '../services/authService'

export const AuthContext = createContext(undefined)

const TOKEN_KEY = 'access_token'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)

  // Strictly "am I still checking for an existing session on app load" —
  // NOT a general-purpose loading flag. Login/Signup/Profile forms track
  // their own submitting state locally; this only gates the initial
  // bootstrap so ProtectedRoute doesn't bounce a still-valid session to
  // /login before the /auth/me check has had a chance to resolve.
  const [isLoading, setIsLoading] = useState(true)

  // On first mount, if a token survived a page refresh, fetch the user it
  // belongs to so the app doesn't flash a logged-out state. If the token
  // is actually expired/invalid, the api.js response interceptor will
  // already clear it and hard-redirect on the 401 — this catch block just
  // makes sure `isLoading` still resolves to false either way.
  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      const token = localStorage.getItem(TOKEN_KEY)
      if (!token) {
        setIsLoading(false)
        return
      }
      try {
        const currentUser = await authService.getCurrentUser()
        if (!cancelled) setUser(currentUser)
      } catch {
        if (!cancelled) setUser(null)
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    bootstrap()
    return () => {
      cancelled = true
    }
  }, [])

  // Both login and register return only { access_token, token_type } per
  // the API — neither includes the user object — so both flows need this
  // same follow-up /auth/me call to populate `user`.
  const login = useCallback(async (email, password) => {
    const { access_token } = await authService.login({ email, password })
    localStorage.setItem(TOKEN_KEY, access_token)
    const currentUser = await authService.getCurrentUser()
    setUser(currentUser)
    return currentUser
  }, [])

  const register = useCallback(async (payload) => {
    const { access_token } = await authService.register(payload)
    localStorage.setItem(TOKEN_KEY, access_token)
    const currentUser = await authService.getCurrentUser()
    setUser(currentUser)
    return currentUser
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
  }, [])

  // Lets Profile/Onboarding patch the cached user after a successful
  // PUT /users/{id} without a full refetch.
  const updateUser = useCallback((updatedFields) => {
    setUser((prev) => (prev ? { ...prev, ...updatedFields } : prev))
  }, [])

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      login,
      register,
      logout,
      updateUser,
    }),
    [user, isLoading, login, register, logout, updateUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}