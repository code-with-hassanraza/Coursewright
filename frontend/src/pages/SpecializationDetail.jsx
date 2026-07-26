import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom'
import PageWrapper from '../components/layout/PageWrapper'
import useAuth from '../hooks/useAuth'
import { getSpecialization, getField, exploreSpecialization } from '../services/specializationService'
import { getRoadmapBySpecialization } from '../services/roadmapService'
import { getUserProgress } from '../services/userService'
import { getErrorMessage } from '../utils/errors'

function InfoCard({ icon, label, value, caption }) {
  return (
    <div className="bento-card">
      <div className="flex items-center gap-xs text-mute">
        <span className="material-symbols-outlined">{icon}</span>
        <span className="font-body-sm-strong text-body-sm-strong">{label}</span>
      </div>
      <p className="mt-xs font-heading-lg text-heading-lg text-ink">{value}</p>
      {caption && <p className="mt-xs font-body-sm text-body-sm text-mute">{caption}</p>}
    </div>
  )
}

export default function SpecializationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { user, isAuthenticated } = useAuth()

  const [spec, setSpec] = useState(null)
  const [field, setField] = useState(null)
  const [roadmap, setRoadmap] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  const [existingProgress, setExistingProgress] = useState(null)
  const [isExploring, setIsExploring] = useState(false)
  const [exploreError, setExploreError] = useState(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const specData = await getSpecialization(id)
      setSpec(specData)

      const [fieldData, roadmapData] = await Promise.all([
        specData.field_id ? getField(specData.field_id) : Promise.resolve(null),
        getRoadmapBySpecialization(id),
      ])
      setField(fieldData)
      setRoadmap(roadmapData)

      if (isAuthenticated && user?.id) {
        try {
          const progressData = await getUserProgress(user.id)
          const match = progressData.items.find((p) => p.specialization_id === id)
          setExistingProgress(match || null)
        } catch {
          // Non-critical — worst case the button shows "Start Exploring" even
          // if they'd already started; the 400 fallback below still recovers.
        }
      }
    } catch (err) {
      setError(getErrorMessage(err, "We couldn't load this specialization."))
    } finally {
      setIsLoading(false)
    }
  }, [id, isAuthenticated, user?.id])

  useEffect(() => {
    load()
  }, [load])

  async function handleExplore() {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: location } })
      return
    }
    setIsExploring(true)
    setExploreError(null)
    try {
      const progress = await exploreSpecialization(spec.id, roadmap?.id)
      setExistingProgress(progress)
    } catch (err) {
      if (err.response?.status === 400) {
        setExistingProgress({ specialization_id: spec.id })
      } else {
        setExploreError(getErrorMessage(err, 'Unable to start exploring. Please try again.'))
      }
    } finally {
      setIsExploring(false)
    }
  }

  const topLevelNodes = roadmap
    ? [...roadmap.nodes].filter((n) => !n.parent_id).sort((a, b) => a.order - b.order)
    : []
  const totalHours = roadmap ? roadmap.nodes.reduce((sum, n) => sum + (n.estimated_hours || 0), 0) : null
  const previewNodes = topLevelNodes.slice(0, 3)
  const remainingCount = Math.max(topLevelNodes.length - previewNodes.length, 0)

  return (
    <PageWrapper isLoading={isLoading} error={error} onRetry={load} maxWidth="max-w-5xl">
      {spec && (
        <div>
          {field && (
            <span className="badge bg-secondary-container text-body-sm-strong text-on-secondary-container">
              {field.name}
            </span>
          )}

          <div className="mt-md flex flex-col gap-lg sm:flex-row sm:items-start sm:justify-between">
            <h1 className="font-heading-xl text-heading-xl text-ink">{spec.name}</h1>

            {existingProgress ? (
              <div className="flex items-center gap-lg">
                <span className="btn-secondary cursor-default gap-xs">
                  <span className="material-symbols-outlined">check_circle</span>
                  Path Added
                </span>
                <Link to={`/roadmap/${spec.id}`} className="font-body-sm-strong text-body-sm-strong text-primary">
                  Go to My Learning →
                </Link>
              </div>
            ) : (
              <button onClick={handleExplore} disabled={isExploring} className="btn-primary shrink-0">
                {isExploring ? 'Starting…' : 'Start Exploring'}
              </button>
            )}
          </div>

          {exploreError && (
            <p className="mt-md rounded-md border border-error-container bg-error-container px-md py-sm font-body-sm text-body-sm text-on-error-container">
              {exploreError}
            </p>
          )}

          {spec.real_world_example && (
            <div className="mt-xl rounded-md border border-hairline-soft bg-surface-card p-xl">
              <p className="font-body-sm-strong text-body-sm-strong text-primary">REAL WORLD IMPACT</p>
              <p className="mt-xs font-body-md text-body-md italic text-ink">"{spec.real_world_example}"</p>
            </div>
          )}

          <div className="mt-xl grid gap-lg sm:grid-cols-2">
            {spec.salary_range && <InfoCard icon="payments" label="Salary Range" value={spec.salary_range} />}
            {totalHours !== null && totalHours > 0 && (
              <InfoCard
                icon="schedule"
                label="Estimated Time"
                value={`${totalHours} hours`}
                caption="Total across the full roadmap"
              />
            )}
          </div>

          <div className="mt-xl grid gap-lg sm:grid-cols-2">
            {spec.description && (
              <div className="bento-card">
                <h2 className="font-heading-md text-heading-md text-ink">Path Overview</h2>
                <p className="mt-xs font-body-md text-body-md text-mute">{spec.description}</p>

                {spec.prerequisites && (
                  <>
                    <h3 className="mt-lg font-body-sm-strong text-body-sm-strong text-ink">Prerequisites</h3>
                    <p className="mt-xs whitespace-pre-line font-body-sm text-body-sm text-mute">
                      {spec.prerequisites}
                    </p>
                  </>
                )}
              </div>
            )}

            {spec.job_roles && spec.job_roles.length > 0 && (
              <div className="bento-card">
                <h2 className="font-heading-md text-heading-md text-ink">Target Roles</h2>
                <div className="mt-sm flex flex-wrap gap-xs">
                  {spec.job_roles.map((role) => (
                    <span key={role} className="badge bg-primary-container/10 text-body-sm-strong text-primary">
                      {role}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="mt-xl rounded-md border border-hairline-soft bg-surface-card p-xl">
            <div className="flex items-center justify-between">
              <h2 className="font-heading-md text-heading-md text-ink">Curriculum Preview</h2>
              {roadmap && (
                <Link to={`/roadmap/${spec.id}`} className="font-body-sm-strong text-body-sm-strong text-primary">
                  View Full Roadmap →
                </Link>
              )}
            </div>

            {!roadmap ? (
              <p className="mt-md font-body-sm text-body-sm text-mute">
                The roadmap for this specialization isn't published yet — check back soon.
              </p>
            ) : (
              <div className="mt-lg flex flex-col gap-sm">
                {previewNodes.map((node, index) => (
                  <div key={node.id} className="flex items-start gap-md rounded-md bg-canvas p-md">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary font-body-sm-strong text-body-sm-strong text-on-primary">
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-body-strong text-body-strong text-ink">{node.title}</p>
                      {node.description && (
                        <p className="mt-xs font-body-sm text-body-sm text-mute">{node.description}</p>
                      )}
                      {node.estimated_hours && (
                        <p className="mt-xs font-body-sm text-body-sm text-ash">{node.estimated_hours} hours</p>
                      )}
                    </div>
                  </div>
                ))}
                {remainingCount > 0 && (
                  <p className="mt-xs font-body-sm text-body-sm text-mute">
                    +{remainingCount} more topic{remainingCount === 1 ? '' : 's'} in the full roadmap.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </PageWrapper>
  )
}