export function getErrorMessage(err, fallback = 'Something went wrong. Please try again.') {
    const detail = err?.response?.data?.detail
  
    if (!detail) return fallback
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      const messages = detail.map((d) => d?.msg).filter(Boolean)
      return messages.length > 0 ? messages.join(' ') : fallback
    }
    return fallback
  }