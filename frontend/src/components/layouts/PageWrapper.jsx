import Navbar from './Navbar'
import Spinner from '../common/Spinner'
import ErrorMessage from '../common/ErrorMessage'

/**
 * Standard shell for every "normal" app page (not Login/Signup, which use
 * their own centered card layout with no navbar). Renders Navbar, clears
 * its fixed 64px height, constrains content width, and gives every page a
 * single consistent way to satisfy Rule 2 (loading / error / empty states)
 * just by passing props instead of re-implementing the same conditional
 * rendering on every page.
 */
export default function PageWrapper({
  children,
  isLoading = false,
  error = null,
  onRetry,
  isEmpty = false,
  emptyState = null,
  maxWidth = 'max-w-6xl',
  className = '',
}) {
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className={`pt-16 ${className}`}>
        <div className={`mx-auto ${maxWidth} px-margin py-xl`}>
          {isLoading ? (
            <div className="flex min-h-[50vh] items-center justify-center">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="flex min-h-[50vh] items-center justify-center">
              <ErrorMessage message={error} onRetry={onRetry} />
            </div>
          ) : isEmpty ? (
            emptyState
          ) : (
            children
          )}
        </div>
      </main>
    </div>
  )
}