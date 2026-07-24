const SIZES = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-[3px]',
    lg: 'h-12 w-12 border-4',
  }
  
  export default function Spinner({ size = 'md', className = '', label = 'Loading' }) {
    return (
      <div role="status" className={`inline-flex items-center justify-center ${className}`}>
        <span className={`${SIZES[size]} animate-spin rounded-full border-hairline border-t-primary`} />
        <span className="sr-only">{label}</span>
      </div>
    )
  }