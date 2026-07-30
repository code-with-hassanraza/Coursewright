import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import { getErrorMessage } from '../utils/errors'

const initialForm = {
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreeToTerms: false,
}

function validate(form) {
  const errors = {}
  if (!form.fullName.trim()) errors.fullName = 'Full name is required.'
  if (!form.email.trim()) errors.email = 'Email is required.'
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errors.email = 'Enter a valid email address.'
  if (!form.password) errors.password = 'Password is required.'
  else if (form.password.length < 8) errors.password = 'Password must be at least 8 characters.'
  if (form.confirmPassword !== form.password) errors.confirmPassword = 'Passwords do not match.'
  if (!form.agreeToTerms) errors.agreeToTerms = 'Please agree to the Terms of Service to continue.'
  return errors
}

export default function Signup() {
  const { register, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [fieldErrors, setFieldErrors] = useState({})
  const [submitError, setSubmitError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true })
  }, [isAuthenticated, navigate])

  function handleChange(field) {
    return (e) => {
      const value = field === 'agreeToTerms' ? e.target.checked : e.target.value
      setForm((prev) => ({ ...prev, [field]: value }))
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const errors = validate(form)
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return

    setSubmitError(null)
    setIsSubmitting(true)
    try {
      await register({
        email: form.email.trim(),
        full_name: form.fullName.trim(),
        password: form.password,
      })
      navigate('/onboarding', { replace: true })
    } catch (err) {
      setSubmitError(getErrorMessage(err, 'Unable to create your account. Please try again.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface-soft px-margin py-section">
      <div className="w-full max-w-md">
        <div className="mb-xl text-center">
          <h1 className="font-heading-xl text-heading-xl text-ink">Coursewright</h1>
          <p className="mt-xs font-body-md text-body-md text-mute">Join the academic discovery platform.</p>
        </div>

        <div className="modal-card">
          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-lg">
            <div>
              <label htmlFor="fullName" className="label">Full Name</label>
              <input
                id="fullName"
                type="text"
                autoComplete="name"
                placeholder="Alex Doe"
                className="input"
                value={form.fullName}
                onChange={handleChange('fullName')}
                disabled={isSubmitting}
              />
              {fieldErrors.fullName && (
                <p className="mt-xs font-body-sm text-body-sm text-error">{fieldErrors.fullName}</p>
              )}
            </div>

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

            <div className="grid grid-cols-2 gap-lg">
              <div>
                <label htmlFor="password" className="label">Password</label>
                <input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  className="input"
                  value={form.password}
                  onChange={handleChange('password')}
                  disabled={isSubmitting}
                />
                {fieldErrors.password && (
                  <p className="mt-xs font-body-sm text-body-sm text-error">{fieldErrors.password}</p>
                )}
              </div>
              <div>
                <label htmlFor="confirmPassword" className="label">Confirm Password</label>
                <input
                  id="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  className="input"
                  value={form.confirmPassword}
                  onChange={handleChange('confirmPassword')}
                  disabled={isSubmitting}
                />
                {fieldErrors.confirmPassword && (
                  <p className="mt-xs font-body-sm text-body-sm text-error">{fieldErrors.confirmPassword}</p>
                )}
              </div>
            </div>

            <div>
              <label className="flex items-start gap-xs">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 rounded border-hairline accent-primary"
                  checked={form.agreeToTerms}
                  onChange={handleChange('agreeToTerms')}
                  disabled={isSubmitting}
                />
                <span className="font-body-sm text-body-sm text-ink">
                  I agree to the{' '}
                  <span className="font-body-sm-strong text-body-sm-strong underline">Terms of Service</span> and{' '}
                  <span className="font-body-sm-strong text-body-sm-strong underline">Privacy Policy</span>.
                </span>
              </label>
              {fieldErrors.agreeToTerms && (
                <p className="mt-xs font-body-sm text-body-sm text-error">{fieldErrors.agreeToTerms}</p>
              )}
            </div>

            {submitError && (
              <p className="rounded-md border border-error-container bg-error-container px-md py-sm font-body-sm text-body-sm text-on-error-container">
                {submitError}
              </p>
            )}

            <button type="submit" className="btn-primary w-full justify-center" disabled={isSubmitting}>
              {isSubmitting ? 'Creating account…' : 'Create Account'}
            </button>

            <p className="text-center font-body-sm text-body-sm text-ink">
              Already have an account?{' '}
              <Link to="/login" className="font-body-sm-strong text-body-sm-strong text-primary">
                Sign in
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