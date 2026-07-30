import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import Navbar from '../components/layout/Navbar'
import Spinner from '../components/common/Spinner'
import { getFields } from '../services/specializationService'
import { FIELD_ICONS } from '../utils/constants'

export default function Home() {
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [fields, setFields] = useState([])
  const [isLoadingFields, setIsLoadingFields] = useState(true)

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate('/fields', { replace: true })
    }
  }, [isAuthenticated, authLoading, navigate])

  useEffect(() => {
    async function load() {
      try {
        const data = await getFields()
        setFields(data.items)
      } catch {
        // Non-critical — hero still works fine.
      } finally {
        setIsLoadingFields(false)
      }
    }
    load()
  }, [])

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className="pt-16">
        {/* Hero */}
        <section className="mx-auto max-w-4xl px-margin py-section text-center">
          <h1 className="font-display-lg text-display-lg text-ink">
            Find your path,<br />build your future.
          </h1>
          <p className="mx-auto mt-lg max-w-xl font-body-md text-body-md text-mute">
            Discover personalised academic roadmaps curated by AI and verified by human experts.
            Navigate your education with clarity.
          </p>
          <div className="mt-xl flex flex-col items-center justify-center gap-md sm:flex-row">
            <Link to="/signup" className="btn-primary px-xxl">
              Get Started →
            </Link>
            <Link to="/fields" className="search-bar max-w-xs text-left text-ash">
              <span className="flex items-center gap-xs">
                <span className="material-symbols-outlined text-ash">search</span>
                What do you want to learn?
              </span>
            </Link>
          </div>
        </section>

        {/* Fields grid */}
        <section className="border-t border-hairline-soft bg-surface-soft px-margin py-xl">
          <div className="mx-auto max-w-6xl">
            <h2 className="font-heading-lg text-heading-lg text-ink">Browse by field</h2>
            {isLoadingFields ? (
              <div className="flex min-h-[200px] items-center justify-center">
                <Spinner />
              </div>
            ) : (
              <div className="mt-lg grid grid-cols-2 gap-lg sm:grid-cols-4">
                {fields.map((field) => (
                  <Link
                    key={field.id}
                    to="/fields"
                    className="pin-card custom-shadow-hover flex flex-col items-start gap-sm p-lg"
                  >
                    <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-container/10">
                      <span className="material-symbols-outlined text-primary">
                        {FIELD_ICONS[field.icon_key] || 'school'}
                      </span>
                    </span>
                    <p className="font-heading-md text-heading-md text-ink">{field.name}</p>
                    <p className="font-body-sm text-body-sm text-mute">{field.category}</p>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-hairline-soft px-margin py-xl">
          <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-md sm:flex-row">
            <p className="font-heading-md text-heading-md text-primary">Coursewright</p>
            <div className="flex gap-lg">
              <span className="font-body-sm text-body-sm text-mute">About Us</span>
              <span className="font-body-sm text-body-sm text-mute">Contact Support</span>
              <span className="font-body-sm text-body-sm text-mute">Privacy Policy</span>
              <span className="font-body-sm text-body-sm text-mute">University Partners</span>
            </div>
            <p className="font-body-sm text-body-sm text-mute">
              © {new Date().getFullYear()} Coursewright Pakistan. Academic Discovery Platform.
            </p>
          </div>
        </footer>
      </main>
    </div>
  )
}