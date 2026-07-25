import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import PageWrapper from '../components/layout/PageWrapper'
import Spinner from '../components/common/Spinner'
import ErrorMessage from '../components/common/ErrorMessage'
import { getFields, getFieldSpecializations, searchSpecializations } from '../services/specializationService'

// icon_key -> Material Symbol name. The API only gives us the key string;
// nothing specifies the actual glyph, so these are my picks — easy to swap.
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

function FieldCard({ field, onClick }) {
  return (
    <button onClick={onClick} className="pin-card custom-shadow-hover flex flex-col items-start gap-sm p-lg text-left">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-container/10">
        <span className="material-symbols-outlined text-primary">{FIELD_ICONS[field.icon_key] || 'school'}</span>
      </span>
      <p className="font-heading-md text-heading-md text-ink">{field.name}</p>
      <p className="font-body-sm text-body-sm text-mute">{field.category}</p>
    </button>
  )
}

function SpecializationCard({ spec, onClick }) {
  return (
    <button
      onClick={onClick}
      className="pin-card custom-shadow-hover masonry-item flex w-full flex-col items-start gap-xs p-lg text-left"
    >
      <p className="font-heading-md text-heading-md text-ink">{spec.name}</p>
      {spec.description && <p className="line-clamp-3 font-body-sm text-body-sm text-mute">{spec.description}</p>}
      {spec.salary_range && (
        <p className="mt-xs font-body-sm-strong text-body-sm-strong text-primary">{spec.salary_range}</p>
      )}
    </button>
  )
}

function SearchResultsPanel({ isSearching, error, results, query, onClear, onSelect }) {
  if (isSearching) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }
  if (error) return <ErrorMessage message={error} />

  if (!results || results.length === 0) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-md py-section text-center">
        <span className="flex h-24 w-24 items-center justify-center rounded-full bg-surface-container-highest">
          <span className="material-symbols-outlined text-4xl text-on-surface-variant">search_off</span>
        </span>
        <p className="font-heading-lg text-heading-lg text-ink">No results found</p>
        <p className="max-w-sm font-body-md text-body-md text-mute">
          We couldn't find any fields or roles matching "{query}". Try adjusting your search or filters.
        </p>
        <button onClick={onClear} className="btn-primary">
          Clear all filters
        </button>
      </div>
    )
  }

  return (
    <div className="masonry-grid mt-xl">
      {results.map((spec) => (
        <SpecializationCard key={spec.id} spec={spec} onClick={() => onSelect(spec)} />
      ))}
    </div>
  )
}

function FieldDrilldown({ field, specs, isLoading, error, onBack, onSelect }) {
  return (
    <div className="mt-xl">
      <button
        onClick={onBack}
        className="mb-lg flex items-center gap-xs font-body-sm-strong text-body-sm-strong text-primary"
      >
        <span className="material-symbols-outlined">arrow_back</span>
        All fields
      </button>
      <h2 className="font-heading-xl text-heading-xl text-ink">{field.name}</h2>
      {field.description && <p className="mt-xs font-body-md text-body-md text-mute">{field.description}</p>}

      {isLoading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : error ? (
        <ErrorMessage message={error} />
      ) : specs.length === 0 ? (
        <p className="mt-xl font-body-md text-body-md text-mute">
          No specializations have been published for this field yet.
        </p>
      ) : (
        <div className="masonry-grid mt-lg">
          {specs.map((spec) => (
            <SpecializationCard key={spec.id} spec={spec} onClick={() => onSelect(spec)} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function FieldExplorer() {
  const navigate = useNavigate()

  const [fields, setFields] = useState([])
  const [isLoadingFields, setIsLoadingFields] = useState(true)
  const [fieldsError, setFieldsError] = useState(null)

  const [selectedCategory, setSelectedCategory] = useState('All Fields')
  const [selectedField, setSelectedField] = useState(null)
  const [fieldSpecs, setFieldSpecs] = useState([])
  const [isLoadingFieldSpecs, setIsLoadingFieldSpecs] = useState(false)
  const [fieldSpecsError, setFieldSpecsError] = useState(null)

  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null) // null = no active search
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState(null)

  const loadFields = useCallback(async () => {
    setIsLoadingFields(true)
    setFieldsError(null)
    try {
      const data = await getFields()
      setFields(data.items)
    } catch {
      setFieldsError("We couldn't load the fields right now.")
    } finally {
      setIsLoadingFields(false)
    }
  }, [])

  useEffect(() => {
    loadFields()
  }, [loadFields])

  // Debounce raw typing into a settled query.
  useEffect(() => {
    const handle = setTimeout(() => setSearchQuery(searchInput.trim()), 400)
    return () => clearTimeout(handle)
  }, [searchInput])

  // Run the search whenever the debounced query actually changes.
  useEffect(() => {
    if (!searchQuery) {
      setSearchResults(null)
      setSearchError(null)
      return
    }
    setSelectedField(null)
    let cancelled = false
    async function runSearch() {
      setIsSearching(true)
      setSearchError(null)
      try {
        const data = await searchSpecializations({ search: searchQuery })
        if (!cancelled) setSearchResults(data.items)
      } catch {
        if (!cancelled) setSearchError('Search failed. Please try again.')
      } finally {
        if (!cancelled) setIsSearching(false)
      }
    }
    runSearch()
    return () => {
      cancelled = true
    }
  }, [searchQuery])

  async function handleFieldClick(field) {
    setSelectedField(field)
    setIsLoadingFieldSpecs(true)
    setFieldSpecsError(null)
    try {
      const data = await getFieldSpecializations(field.id)
      setFieldSpecs(data.items)
    } catch {
      setFieldSpecsError(`We couldn't load specializations for ${field.name}.`)
    } finally {
      setIsLoadingFieldSpecs(false)
    }
  }

  function clearAllFilters() {
    setSearchInput('')
    setSearchQuery('')
    setSelectedCategory('All Fields')
    setSelectedField(null)
  }

  const categories = ['All Fields', ...Array.from(new Set(fields.map((f) => f.category)))]
  const visibleFields =
    selectedCategory === 'All Fields' ? fields : fields.filter((f) => f.category === selectedCategory)

  const fieldCategoryById = Object.fromEntries(fields.map((f) => [f.id, f.category]))
  const visibleSearchResults =
    searchResults && selectedCategory !== 'All Fields'
      ? searchResults.filter((s) => fieldCategoryById[s.field_id] === selectedCategory)
      : searchResults

  const isSearchMode = searchQuery.length > 0

  return (
    <PageWrapper isLoading={isLoadingFields} error={fieldsError} onRetry={loadFields} maxWidth="max-w-7xl">
      <div className="sticky top-16 z-10 -mx-margin bg-canvas px-margin py-lg">
        <div className="relative">
          <span className="material-symbols-outlined pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-ash">
            search
          </span>
          <input
            type="text"
            className="search-bar pl-12"
            placeholder="What do you want to learn?"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
        <div className="mt-md flex flex-wrap gap-xs">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`rounded-full px-md py-xs font-body-sm-strong text-body-sm-strong transition-colors ${
                selectedCategory === category
                  ? 'bg-primary text-on-primary'
                  : 'bg-secondary-bg text-on-secondary hover:bg-secondary-pressed'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {isSearchMode ? (
        <SearchResultsPanel
          isSearching={isSearching}
          error={searchError}
          results={visibleSearchResults}
          query={searchQuery}
          onClear={clearAllFilters}
          onSelect={(spec) => navigate(`/specializations/${spec.id}`)}
        />
      ) : selectedField ? (
        <FieldDrilldown
          field={selectedField}
          specs={fieldSpecs}
          isLoading={isLoadingFieldSpecs}
          error={fieldSpecsError}
          onBack={() => setSelectedField(null)}
          onSelect={(spec) => navigate(`/specializations/${spec.id}`)}
        />
      ) : (
        <div className="mt-xl grid grid-cols-2 gap-lg md:grid-cols-4">
          {visibleFields.map((field) => (
            <FieldCard key={field.id} field={field} onClick={() => handleFieldClick(field)} />
          ))}
        </div>
      )}
    </PageWrapper>
  )
}