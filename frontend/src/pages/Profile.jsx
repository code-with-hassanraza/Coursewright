import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import PageWrapper from '../components/layout/PageWrapper'
import useAuth from '../hooks/useAuth'
import { updateUser, getUserProgress } from '../services/userService'
import { getSpecialization } from '../services/specializationService'
import { getTasksBySpecialization } from '../services/taskService'
import { getMyCertificates } from '../services/certificateService'
import { getErrorMessage } from '../utils/errors'
import { DEGREE_OPTIONS, YEAR_OPTIONS } from '../utils/constants'

function formatMonthYear(isoDate) {
  return new Date(isoDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

function getPathStats(progress, tasks) {
  if (!tasks || tasks.length === 0) return { percent: 0, totalTasks: 0, nextTaskTitle: null }
  const completedSet = new Set(progress.completed_nodes || [])
  const totalTasks = tasks.length
  const completedCount = tasks.filter((t) => completedSet.has(t.id)).length
  const percent = Math.round((completedCount / totalTasks) * 100)
  const nextTask = tasks.find((t) => !completedSet.has(t.id))
  return { percent, totalTasks, completedCount, nextTaskTitle: nextTask?.title ?? null }
}

export default function Profile() {
  const { user, updateUser: updateCachedUser } = useAuth()

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [inProgressPaths, setInProgressPaths] = useState([])
  const [certificates, setCertificates] = useState([])
  const [stats, setStats] = useState({ exploring: 0, learning: 0, completed: 0 })

  const [fullName, setFullName] = useState(user?.full_name || '')
  const [degree, setDegree] = useState(() =>
    user?.degree ? (DEGREE_OPTIONS.includes(user.degree) ? user.degree : 'Other') : '',
  )
  const [customDegree, setCustomDegree] = useState(() =>
    user?.degree && !DEGREE_OPTIONS.includes(user.degree) ? user.degree : '',
  )
  const [yearOfStudy, setYearOfStudy] = useState(() => (user?.year_of_study ? String(user.year_of_study) : ''))
  const [profileError, setProfileError] = useState(null)
  const [profileSuccess, setProfileSuccess] = useState(false)
  const [isSavingProfile, setIsSavingProfile] = useState(false)

  const load = useCallback(async () => {
    if (!user?.id) return
    setIsLoading(true)
    setError(null)
    try {
      const [progressData, certs] = await Promise.all([getUserProgress(user.id), getMyCertificates()])
      const progressItems = progressData.items
      const inProgress = progressItems.filter((p) => p.status !== 'completed')

      const specIds = new Set([
        ...inProgress.map((p) => p.specialization_id),
        ...certs.map((c) => c.specialization_id),
      ])
      const specEntries = await Promise.all(
        Array.from(specIds).map(async (specId) => {
          try {
            return [specId, await getSpecialization(specId)]
          } catch {
            return [specId, null]
          }
        }),
      )
      const specById = new Map(specEntries)

      const inProgressWithTasks = await Promise.all(
        inProgress.map(async (p) => {
          let tasksData = []
          try {
            const tasksResponse = await getTasksBySpecialization(p.specialization_id)
            tasksData = tasksResponse.items
          } catch {
            tasksData = []
          }
          return { progress: p, spec: specById.get(p.specialization_id), tasks: tasksData }
        }),
      )

      setInProgressPaths(inProgressWithTasks)
      setCertificates(certs.map((c) => ({ certificate: c, spec: specById.get(c.specialization_id) })))
      setStats({
        exploring: progressItems.filter((p) => p.status === 'exploring').length,
        learning: progressItems.filter((p) => p.status === 'learning').length,
        completed: progressItems.filter((p) => p.status === 'completed').length,
      })
    } catch (err) {
      setError(getErrorMessage(err, "We couldn't load your profile."))
    } finally {
      setIsLoading(false)
    }
  }, [user?.id])

  useEffect(() => {
    load()
  }, [load])

  async function handleProfileSubmit(e) {
    e.preventDefault()
    setProfileError(null)
    setProfileSuccess(false)

    if (degree === 'Other' && !customDegree.trim()) {
      setProfileError('Please tell us your degree program.')
      return
    }

    setIsSavingProfile(true)
    try {
      const payload = { full_name: fullName.trim() }
      if (degree) payload.degree = degree === 'Other' ? customDegree.trim() : degree
      if (yearOfStudy) payload.year_of_study = Number(yearOfStudy)

      const updated = await updateUser(user.id, payload)
      updateCachedUser(updated)
      setProfileSuccess(true)
    } catch (err) {
      setProfileError(getErrorMessage(err, 'Unable to save your changes. Please try again.'))
    } finally {
      setIsSavingProfile(false)
    }
  }

  const hasNothingYet = inProgressPaths.length === 0 && certificates.length === 0

  return (
    <PageWrapper isLoading={isLoading} error={error} onRetry={load}>
      <h1 className="font-heading-xl text-heading-xl text-ink">Welcome back, {user?.full_name?.split(' ')[0]}.</h1>
      <p className="mt-xs font-body-md text-body-md text-mute">Here's where things stand.</p>

      <div className="mt-lg flex gap-md">
        <span className="badge bg-secondary-container text-body-sm-strong text-on-secondary-container">
          {stats.exploring} exploring
        </span>
        <span className="badge bg-secondary-container text-body-sm-strong text-on-secondary-container">
          {stats.learning} learning
        </span>
        <span className="badge bg-primary-container/10 text-body-sm-strong text-primary">
          {stats.completed} completed
        </span>
      </div>

      {hasNothingYet && (
        <div className="mt-xl rounded-md border border-hairline-soft bg-surface-card p-xl text-center">
          <p className="font-heading-md text-heading-md text-ink">You haven't started a path yet.</p>
          <p className="mt-xs font-body-sm text-body-sm text-mute">
            Browse the fields to find a specialization that fits where you want to go.
          </p>
          <Link to="/fields" className="btn-primary mt-lg inline-flex">
            Explore Fields
          </Link>
        </div>
      )}

      {inProgressPaths.length > 0 && (
        <section className="mt-xl">
          <h2 className="font-heading-lg text-heading-lg text-ink">Currently Learning</h2>
          <div className="mt-md grid gap-lg sm:grid-cols-2">
            {inProgressPaths.map(({ progress, spec, tasks }) => {
              const { percent, nextTaskTitle } = getPathStats(progress, tasks)
              return (
                <div key={progress.id} className="bento-card">
                  <p className="font-heading-md text-heading-md text-ink">{spec?.name || 'Specialization'}</p>
                  {spec?.description && (
                    <p className="mt-xs line-clamp-2 font-body-sm text-body-sm text-mute">{spec.description}</p>
                  )}
                  <div className="mt-md flex items-center justify-between font-body-sm-strong text-body-sm-strong text-ink">
                    <span>{percent}% Complete</span>
                    {nextTaskTitle && <span className="text-mute">Next: {nextTaskTitle}</span>}
                  </div>
                  <div className="mt-xs h-2 w-full overflow-hidden rounded-full bg-secondary-bg">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${percent}%` }} />
                  </div>
                  <Link
                    to={`/roadmap/${progress.specialization_id}`}
                    className="btn-secondary mt-md w-full justify-center gap-xs"
                  >
                    <span className="material-symbols-outlined">play_arrow</span>
                    Resume Learning
                  </Link>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {certificates.length > 0 && (
        <section className="mt-xl">
          <h2 className="font-heading-lg text-heading-lg text-ink">Completed Paths &amp; Certificates</h2>
          <div className="mt-md grid gap-lg sm:grid-cols-2">
            {certificates.map(({ certificate, spec }) => (
              <div key={certificate.id} className="bento-card flex items-start gap-md">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary-container/10">
                  <span className="material-symbols-outlined text-primary">workspace_premium</span>
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-heading-md text-heading-md text-ink">{spec?.name || 'Specialization'}</p>
                  <p className="mt-xs font-body-sm text-body-sm text-mute">
                    Completed {formatMonthYear(certificate.issued_at)}
                  </p>
                  <Link
                    to={`/certificates/verify/${certificate.certificate_code}`}
                    className="btn-outline mt-md gap-xs"
                  >
                    <span className="material-symbols-outlined">verified</span>
                    View Certificate
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="mt-xl">
        <h2 className="font-heading-lg text-heading-lg text-ink">Your Details</h2>
        <div className="modal-card mt-md max-w-xl p-xl">
          <div className="mb-lg flex items-center justify-between">
            <div>
              <p className="font-body-strong text-body-strong text-ink">{user?.email}</p>
              <p className="font-body-sm text-body-sm text-mute">Email can't be changed here.</p>
            </div>
            <span className="badge bg-secondary-container text-body-sm-strong text-on-secondary-container">
              {user?.role}
            </span>
          </div>

          <form onSubmit={handleProfileSubmit} className="flex flex-col gap-lg">
            <div>
              <label htmlFor="fullName" className="label">Full Name</label>
              <input
                id="fullName"
                type="text"
                className="input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={isSavingProfile}
              />
            </div>

            <div>
              <label htmlFor="degree" className="label">Degree Program</label>
              <div className="relative">
                <select
                  id="degree"
                  className="input"
                  value={degree}
                  onChange={(e) => setDegree(e.target.value)}
                  disabled={isSavingProfile}
                >
                  <option value="">Not set</option>
                  {DEGREE_OPTIONS.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
                <span className="material-symbols-outlined pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-mute">
                  expand_more
                </span>
              </div>
            </div>

            {degree === 'Other' && (
              <div>
                <label htmlFor="customDegree" className="label">Please specify</label>
                <input
                  id="customDegree"
                  type="text"
                  className="input"
                  value={customDegree}
                  onChange={(e) => setCustomDegree(e.target.value)}
                  disabled={isSavingProfile}
                />
              </div>
            )}

            <div>
              <label htmlFor="yearOfStudy" className="label">Year of Study</label>
              <div className="relative">
                <select
                  id="yearOfStudy"
                  className="input"
                  value={yearOfStudy}
                  onChange={(e) => setYearOfStudy(e.target.value)}
                  disabled={isSavingProfile}
                >
                  <option value="">Not set</option>
                  {YEAR_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
                <span className="material-symbols-outlined pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-mute">
                  expand_more
                </span>
              </div>
            </div>

            {profileError && (
              <p className="rounded-md border border-error-container bg-error-container px-md py-sm font-body-sm text-body-sm text-on-error-container">
                {profileError}
              </p>
            )}
            {profileSuccess && (
              <p className="rounded-md border border-hairline-soft bg-surface-card px-md py-sm font-body-sm text-body-sm text-ink">
                Saved.
              </p>
            )}

            <button type="submit" className="btn-primary justify-center" disabled={isSavingProfile}>
              {isSavingProfile ? 'Saving…' : 'Save Changes'}
            </button>
          </form>
        </div>
      </section>
    </PageWrapper>
  )
}