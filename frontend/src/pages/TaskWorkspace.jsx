import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import PageWrapper from '../components/layout/PageWrapper'
import useAuth from '../hooks/useAuth'
import { getTask, completeTask } from '../services/taskService'
import { getSpecialization } from '../services/specializationService'
import { getUserProgress } from '../services/userService'
import { getErrorMessage } from '../utils/errors'

const DIFFICULTY_STYLES = {
  beginner: 'bg-primary-container/10 text-primary',
  intermediate: 'bg-tertiary-container/10 text-tertiary',
  advanced: 'border border-ink text-ink',
}

export default function TaskWorkspace() {
  const { task_id } = useParams()
  const { user } = useAuth()

  const [task, setTask] = useState(null)
  const [spec, setSpec] = useState(null)
  const [isComplete, setIsComplete] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  const [isCompleting, setIsCompleting] = useState(false)
  const [completeError, setCompleteError] = useState(null)
  const [needsExploreFirst, setNeedsExploreFirst] = useState(false)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const taskData = await getTask(task_id)
      setTask(taskData)

      const specData = await getSpecialization(taskData.specialization_id).catch(() => null)
      setSpec(specData)

      if (user?.id) {
        const progressData = await getUserProgress(user.id)
        const match = progressData.items.find((p) => p.specialization_id === taskData.specialization_id)
        const completedSet = new Set(match?.completed_nodes || [])
        setIsComplete(completedSet.has(taskData.id))
      }
    } catch (err) {
      setError(getErrorMessage(err, "We couldn't load this task."))
    } finally {
      setIsLoading(false)
    }
  }, [task_id, user?.id])

  useEffect(() => {
    load()
  }, [load])

  async function handleComplete() {
    setIsCompleting(true)
    setCompleteError(null)
    setNeedsExploreFirst(false)
    try {
      await completeTask(task.id)
      setIsComplete(true)
    } catch (err) {
      if (err.response?.status === 400) {
        setNeedsExploreFirst(true)
      } else {
        setCompleteError(getErrorMessage(err, 'Unable to mark this complete. Please try again.'))
      }
    } finally {
      setIsCompleting(false)
    }
  }

  return (
    <PageWrapper isLoading={isLoading} error={error} onRetry={load} maxWidth="max-w-3xl">
      {task && (
        <div>
          {spec && (
            <Link
              to={`/roadmap/${task.specialization_id}`}
              className="flex items-center gap-xs font-body-sm-strong text-body-sm-strong text-primary"
            >
              <span className="material-symbols-outlined">arrow_back</span>
              Back to {spec.name}
            </Link>
          )}

          <div className="mt-md flex flex-wrap items-center gap-xs">
            <span className={`badge ${DIFFICULTY_STYLES[task.difficulty] || 'bg-secondary-bg text-on-secondary'}`}>
              {task.difficulty}
            </span>
            {isComplete && (
              <span className="badge flex items-center gap-xs bg-primary text-on-primary">
                <span className="material-symbols-outlined text-sm">check</span>
                Complete
              </span>
            )}
          </div>

          <h1 className="mt-xs font-heading-xl text-heading-xl text-ink">{task.title}</h1>
          {task.description && <p className="mt-xs font-body-md text-body-md text-mute">{task.description}</p>}

          {task.suggested_tools && task.suggested_tools.length > 0 && (
            <div className="mt-md flex flex-wrap gap-xs">
              {task.suggested_tools.map((tool) => (
                <span
                  key={tool}
                  className="badge bg-secondary-container text-body-sm-strong text-on-secondary-container"
                >
                  {tool}
                </span>
              ))}
            </div>
          )}

          {task.instructions && (
            <div className="mt-xl rounded-md border border-hairline-soft bg-surface-card p-xl">
              <h2 className="font-heading-md text-heading-md text-ink">Instructions</h2>
              <p className="mt-sm whitespace-pre-line font-body-md text-body-md text-ink">{task.instructions}</p>
            </div>
          )}

          {needsExploreFirst && spec && (
            <p className="mt-lg rounded-md border border-error-container bg-error-container px-md py-sm font-body-sm text-body-sm text-on-error-container">
              You need to start exploring {spec.name} before completing tasks.{' '}
              <Link to={`/specializations/${task.specialization_id}`} className="font-body-sm-strong underline">
                Go start exploring →
              </Link>
            </p>
          )}
          {completeError && (
            <p className="mt-lg rounded-md border border-error-container bg-error-container px-md py-sm font-body-sm text-body-sm text-on-error-container">
              {completeError}
            </p>
          )}

          <button
            onClick={handleComplete}
            disabled={isComplete || isCompleting}
            className="btn-primary mt-xl w-full justify-center gap-xs sm:w-auto"
          >
            <span className="material-symbols-outlined">check_circle</span>
            {isComplete ? 'Completed' : isCompleting ? 'Marking complete…' : 'Mark Complete'}
          </button>
        </div>
      )}
    </PageWrapper>
  )
}