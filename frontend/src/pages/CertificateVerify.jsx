import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { verifyCertificate } from '../services/certificateService'
import { getSpecialization } from '../services/specializationService'
import Spinner from '../components/common/Spinner'

function formatDate(isoDate) {
  return new Date(isoDate).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export default function CertificateVerify() {
  const { code } = useParams()
  const [cert, setCert] = useState(null)
  const [spec, setSpec] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setIsLoading(true)
      try {
        const certData = await verifyCertificate(code)
        if (!cancelled) {
          setCert(certData)
          const specData = await getSpecialization(certData.specialization_id).catch(() => null)
          if (!cancelled) setSpec(specData)
        }
      } catch {
        if (!cancelled) setNotFound(true)
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [code])

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-soft">
        <Spinner size="lg" />
      </div>
    )
  }

  if (notFound) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-lg bg-surface-soft px-margin text-center">
        <span className="material-symbols-outlined text-5xl text-error">error</span>
        <h1 className="font-heading-xl text-heading-xl text-ink">Certificate not found</h1>
        <p className="font-body-md text-body-md text-mute">
          The code <span className="font-mono font-body-sm-strong text-body-sm-strong text-ink">{code}</span> doesn't
          match any certificate in our system.
        </p>
        <Link to="/" className="btn-primary">Go to Coursewright</Link>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface-soft px-margin py-section">
      <div className="w-full max-w-lg">
        <div className="modal-card text-center">
          <span className="material-symbols-outlined text-5xl text-primary">verified</span>
          <h1 className="mt-md font-heading-xl text-heading-xl text-ink">Certificate Verified</h1>
          <p className="mt-xs font-body-md text-body-md text-mute">
            This is an authentic Coursewright certificate.
          </p>

          <div className="mt-xl divide-y divide-hairline-soft rounded-md border border-hairline-soft text-left">
            <div className="flex justify-between px-lg py-md">
              <span className="font-body-sm text-body-sm text-mute">Specialization</span>
              <span className="font-body-sm-strong text-body-sm-strong text-ink">
                {spec?.name || cert.specialization_id}
              </span>
            </div>
            <div className="flex justify-between px-lg py-md">
              <span className="font-body-sm text-body-sm text-mute">Issued on</span>
              <span className="font-body-sm-strong text-body-sm-strong text-ink">
                {formatDate(cert.issued_at)}
              </span>
            </div>
            <div className="flex justify-between px-lg py-md">
              <span className="font-body-sm text-body-sm text-mute">Certificate code</span>
              <span className="font-mono font-body-sm text-body-sm text-ink">{cert.certificate_code}</span>
            </div>
          </div>

          <Link to="/" className="btn-outline mt-xl w-full justify-center">
            Go to Coursewright
          </Link>
        </div>
        <p className="mt-lg text-center font-body-sm text-body-sm text-mute">
          © {new Date().getFullYear()} Coursewright Pakistan.
        </p>
      </div>
    </div>
  )
}