export default function ErrorMessage({ title = 'Something went wrong', message, onRetry }) {
    return (
      <div className="flex flex-col items-center justify-center gap-sm rounded-md border border-error-container bg-error-container px-xl py-xl text-center">
        <span className="material-symbols-outlined text-on-error-container">error</span>
        <p className="font-heading-md text-heading-md text-on-error-container">{title}</p>
        {message && <p className="font-body-sm text-body-sm text-on-error-container">{message}</p>}
        {onRetry && (
          <button onClick={onRetry} className="btn-secondary mt-xs">
            Try again
          </button>
        )}
      </div>
    )
  }