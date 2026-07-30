import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import { getErrorMessage } from '../utils/errors'

function validate(form) {
  const errors = {}
  if (!form.email.trim()) errors.email = 'Email is required.'
  if (!form.password) errors.password = 'Password is required.'
  return errors
}

export default function Login() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [fieldErrors, setFieldErrors] = useState({})
  const [submitError, setSubmitError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true })
  }, [isAuthenticated, navigate])

  function handleChange(field) {
    return (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const errors = validate(form)
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return

    setSubmitError(null)
    setIsSubmitting(true)
    try {
      await login(form.email.trim(), form.password)
      navigate(location.state?.from || '/', { replace: true })
    } catch (err) {
      if (err.response?.status === 403) {
        setSubmitError(`${getErrorMessage(err)} Please contact support if you believe this is a mistake.`)
      } else {
        setSubmitError(getErrorMessage(err, 'Unable to sign in. Please try again.'))
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface-soft px-margin py-section">
      <div className="w-full max-w-md">
        <div className="mb-xl text-center">
          <h1 className="font-heading-xl text-heading-xl text-ink">Coursewright</h1>
          <p className="mt-xs font-body-md text-body-md text-mute">Welcome back. Sign in to continue.</p>
        </div>

        <div className="modal-card">
          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-lg">
            <div>
              <label htmlFor="email" className="label">University Email</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="alex@university.edu"
                className="input"
                value={form.email}
                onChange={handleChange('email')}
                disabled={isSubmitting}
              />
              {fieldErrors.email && (
                <p className="mt-xs font-body-sm text-body-sm text-error">{fieldErrors.email}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="label">Password</label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                className="input"
                value={form.password}
                onChange={handleChange('password')}
                disabled={isSubmitting}
              />
              {fieldErrors.password && (
                <p className="mt-xs font-body-sm text-body-sm text-error">{fieldErrors.password}</p>
              )}
            </div>

            {submitError && (
              <p className="rounded-md border border-error-container bg-error-container px-md py-sm font-body-sm text-body-sm text-on-error-container">
                {submitError}
              </p>
            )}

            <button type="submit" className="btn-primary w-full justify-center" disabled={isSubmitting}>
              {isSubmitting ? 'Signing in…' : 'Sign In'}
            </button>

            <p className="text-center font-body-sm text-body-sm text-ink">
              Don't have an account?{' '}
              <Link to="/signup" className="font-body-sm-strong text-body-sm-strong text-primary">
                Sign up
              </Link>
            </p>
          </form>
        </div>

        <p className="mt-xl text-center font-body-sm text-body-sm text-mute">
          © {new Date().getFullYear()} Coursewright Pakistan.
        </p>
      </div>
    </div>
  )
}