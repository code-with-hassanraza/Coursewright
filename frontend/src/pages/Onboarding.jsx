import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import { updateUser } from '../services/userService'
import { getFields } from '../services/specializationService'
import { getErrorMessage } from '../utils/errors'
import Spinner from '../components/common/Spinner'

// Sourced from quest.edu.pk / QUEST's Wikipedia page — real QUEST programs,
// not invented. "Other" covers anything not confirmed here (QUEST doesn't
// appear to run a Business Administration program of its own, despite that
// being one of our 8 seeded Coursewright fields, so this list intentionally
// doesn't claim one).
const DEGREE_OPTIONS = [
  'Computer Science',
  'Information Technology',
  'Software Engineering',
  'Electrical Engineering',
  'Electronic Engineering',
  'Civil Engineering',
  'Environmental Engineering',
  'Mechanical Engineering',
  'Chemical Engineering',
  'Telecommunication Engineering',
  'Cyber Security',
  'Biomedical Engineering',
  'Other',
]

// QUEST's bachelor's programs are confirmed 4-year / 8-semester.
const YEAR_OPTIONS = [
  { value: 1, label: '1st Year' },
  { value: 2, label: '2nd Year' },
  { value: 3, label: '3rd Year' },
  { value: 4, label: '4th Year' },
]

// Same picks as FieldExplorer — the API only gives icon_key strings.
const FIELD_ICONS = {
  it: 'lan',
  cs: 'terminal',
  se: 'deployed_code',
  ds: 'query_stats',
  ee: 'bolt',
  ce: 'foundation',
  ba: 'monitoring',
  enve: 'eco',
}

function Stepper({ step }) {
  return (
    <div className="mb-xl flex items-center justify-center gap-xs">
      {[1, 2].map((n) => (
        <div
          key={n}
          className={`h-1.5 w-16 rounded-full transition-colors ${n <= step ? 'bg-primary' : 'bg-secondary-bg'}`}
        />
      ))}
    </div>
  )
}

export default function Onboarding() {
  const { user, updateUser: updateCachedUser } = useAuth()
  const navigate = useNavigate()

  const [step, setStep] = useState(1)

  // Pre-fill if the user already has a saved degree/year (e.g. they refreshed
  // mid-onboarding, or are revisiting) rather than making them re-enter it.
  const [degree, setDegree] = useState(() => {
    if (!user?.degree) return ''
    return DEGREE_OPTIONS.includes(user.degree) ? user.degree : 'Other'
  })
  const [customDegree, setCustomDegree] = useState(() =>
    user?.degree && !DEGREE_OPTIONS.includes(user.degree) ? user.degree : '',
  )
  const [yearOfStudy, setYearOfStudy] = useState(() => (user?.year_of_study ? String(user.year_of_study) : ''))
  const [fieldErrors, setFieldErrors] = useState({})
  const [submitError, setSubmitError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [fields, setFields] = useState([])
  const [isLoadingFields, setIsLoadingFields] = useState(true)
  const [highlighted, setHighlighted] = useState(new Set())

  useEffect(() => {
    if (step !== 2) return
    let cancelled = false
    async function loadFields() {
      setIsLoadingFields(true)
      try {
        const data = await getFields()
        if (!cancelled) setFields(data.items)
      } catch {
        // Non-critical for onboarding — this step is just a preview, so a
        // failed fetch shouldn't block finishing. It'll just render empty.
      } finally {
        if (!cancelled) setIsLoadingFields(false)
      }
    }
    loadFields()
    return () => {
      cancelled = true
    }
  }, [step])

  function toggleHighlight(fieldId) {
    setHighlighted((prev) => {
      const next = new Set(prev)
      if (next.has(fieldId)) next.delete(fieldId)
      else next.add(fieldId)
      return next
    })
  }

  async function handleStepOneSubmit(e) {
    e.preventDefault()
    const errors = {}
    if (!degree) errors.degree = 'Please select your degree program.'
    if (degree === 'Other' && !customDegree.trim()) errors.customDegree = 'Please tell us your degree program.'
    if (!yearOfStudy) errors.yearOfStudy = 'Please select your year of study.'
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return

    setSubmitError(null)
    setIsSubmitting(true)
    try {
      const finalDegree = degree === 'Other' ? customDegree.trim() : degree
      const updated = await updateUser(user.id, {
        degree: finalDegree,
        year_of_study: Number(yearOfStudy),
      })
      updateCachedUser(updated)
      setStep(2)
    } catch (err) {
      setSubmitError(getErrorMessage(err, 'Unable to save your details. Please try again.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleFinish() {
    navigate('/fields', { replace: true })
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface-soft px-margin py-section">
      <div className="w-full max-w-2xl">
        <Stepper step={step} />

        {step === 1 && (
          <div className="modal-card">
            <div className="mb-lg text-center">
              <h1 className="font-heading-xl text-heading-xl text-ink">Tell us about yourself</h1>
              <p className="mt-xs font-body-md text-body-md text-mute">
                This helps us tailor your roadmap recommendations.
              </p>
            </div>

            <form onSubmit={handleStepOneSubmit} noValidate className="flex flex-col gap-lg">
              <div>
                <label htmlFor="degree" className="label">
                  Degree Program
                </label>
                <div className="relative">
                  <select
                    id="degree"
                    className="input"
                    value={degree}
                    onChange={(e) => setDegree(e.target.value)}
                    disabled={isSubmitting}
                  >
                    <option value="" disabled>
                      Select your program
                    </option>
                    {DEGREE_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                  <span className="material-symbols-outlined pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-mute">
                    expand_more
                  </span>
                </div>
                {fieldErrors.degree && (
                  <p className="mt-xs font-body-sm text-body-sm text-error">{fieldErrors.degree}</p>
                )}
              </div>

              {degree === 'Other' && (
                <div>
                  <label htmlFor="customDegree" className="label">
                    Please specify
                  </label>
                  <input
                    id="customDegree"
                    type="text"
                    className="input"
                    value={customDegree}
                    onChange={(e) => setCustomDegree(e.target.value)}
                    disabled={isSubmitting}
                  />
                  {fieldErrors.customDegree && (
                    <p className="mt-xs font-body-sm text-body-sm text-error">{fieldErrors.customDegree}</p>
                  )}
                </div>
              )}

              <div>
                <label htmlFor="yearOfStudy" className="label">
                  Year of Study
                </label>
                <div className="relative">
                  <select
                    id="yearOfStudy"
                    className="input"
                    value={yearOfStudy}
                    onChange={(e) => setYearOfStudy(e.target.value)}
                    disabled={isSubmitting}
                  >
                    <option value="" disabled>
                      Select your year
                    </option>
                    {YEAR_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <span className="material-symbols-outlined pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-mute">
                    expand_more
                  </span>
                </div>
                {fieldErrors.yearOfStudy && (
                  <p className="mt-xs font-body-sm text-body-sm text-error">{fieldErrors.yearOfStudy}</p>
                )}
              </div>

              {submitError && (
                <p className="rounded-md border border-error-container bg-error-container px-md py-sm font-body-sm text-body-sm text-on-error-container">
                  {submitError}
                </p>
              )}

              <button type="submit" className="btn-primary w-full justify-center" disabled={isSubmitting}>
                {isSubmitting ? 'Saving…' : 'Continue'}
              </button>
            </form>
          </div>
        )}

        {step === 2 && (
          <div className="modal-card">
            <div className="mb-lg text-center">
              <h1 className="font-heading-xl text-heading-xl text-ink">What are you curious about?</h1>
              <p className="mt-xs font-body-md text-body-md text-mute">
                Tap anything that catches your eye — you'll be able to explore all of them either way.
              </p>
            </div>

            {isLoadingFields ? (
              <div className="flex min-h-[200px] items-center justify-center">
                <Spinner size="lg" />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-md sm:grid-cols-4">
                {fields.map((field) => {
                  const isHighlighted = highlighted.has(field.id)
                  return (
                    <button
                      key={field.id}
                      type="button"
                      onClick={() => toggleHighlight(field.id)}
                      className={`flex flex-col items-center gap-xs rounded-md border p-md text-center transition-colors ${
                        isHighlighted
                          ? 'border-primary bg-primary-container/10'
                          : 'border-hairline-soft bg-surface-card hover:border-hairline'
                      }`}
                    >
                      <span className="material-symbols-outlined text-primary">
                        {FIELD_ICONS[field.icon_key] || 'school'}
                      </span>
                      <span className="font-body-sm-strong text-body-sm-strong text-ink">{field.name}</span>
                    </button>
                  )
                })}
              </div>
            )}

            <button onClick={handleFinish} className="btn-primary mt-xl w-full justify-center">
              Start Exploring
            </button>
          </div>
        )}
      </div>
    </div>
  )
}