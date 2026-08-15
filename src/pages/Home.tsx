import React, { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import './Home.css'
import { propertyService } from '../services/property'
import { Property } from '../types'
import PropertyCard from '../components/PropertyCard'
import Skeleton from '../components/Skeleton'
import { PUBLIC_FEATURED_PROPERTIES_FALLBACK, PUBLIC_HOME_INTELLIGENCE, PUBLIC_HOME_LOCATIONS, PUBLIC_HOME_STEPS, PUBLIC_PURPOSE_COPY, PropertyPurpose } from '../data/publicHomeContent'
import { PROPERTY_TYPES, BUDGETS, BEDROOMS } from '../data/propertySearchOptions'

// Real estate hero image from Unsplash
const HERO_IMAGE = 'https://source.unsplash.com/1200x800/?luxury-apartment,modern&sig=hero'

type SearchState = {
  location: string
  propertyType: string
  budget: string
  bedrooms: string
  purpose: PropertyPurpose
}

export default function Home() {
  const [search, setSearch] = useState<SearchState>({
    location: '',
    propertyType: '',
    budget: '',
    bedrooms: '',
    purpose: 'buy',
  })
  const [featured, setFeatured] = useState<Property[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [featuredSource, setFeaturedSource] = useState<'api' | 'fallback' | null>(null)
  const [portfolioTotal, setPortfolioTotal] = useState<number | null>(null)
  const [portfolioUnits, setPortfolioUnits] = useState<number | null>(null)
  const [savedIds, setSavedIds] = useState<number[]>([])
  const navigate = useNavigate()

  function buildPropertiesUrl(overrides?: Partial<SearchState> & { match?: boolean }) {
    const query = new URLSearchParams()
    const state = { ...search, ...overrides }
    
    // Determine base route based on purpose
    let basePath = '/properties'
    if (state.purpose === 'buy') basePath = '/buy'
    else if (state.purpose === 'rent') basePath = '/rent'
    else if (state.purpose === 'invest') basePath = '/invest'
    
    if (state.location) query.set('location', state.location)
    if (state.propertyType) query.set('property_type', state.propertyType)
    if (state.budget) query.set('budget', state.budget)
    if (state.bedrooms) query.set('bedrooms', state.bedrooms)
    if (overrides?.match) query.set('match', 'true')
    
    return `${basePath}${query.toString() ? `?${query.toString()}` : ''}`
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    navigate(buildPropertiesUrl())
  }

  useEffect(()=>{
    let mounted = true
    setLoading(true)
    setError(null)
    Promise.allSettled([
      propertyService.meta(),
      propertyService.list({ limit: 6, sort: 'newest' }),
    ]).then(([metaResult, listResult]) => {
      if (!mounted) return

      if (metaResult.status === 'fulfilled' && metaResult.value) {
        setPortfolioTotal(metaResult.value.total)
        setPortfolioUnits(metaResult.value.total_units)
      } else {
        setPortfolioTotal(null)
        setPortfolioUnits(null)
      }

      if (listResult.status === 'fulfilled' && listResult.value.length > 0) {
        setFeatured(listResult.value)
        setFeaturedSource('api')
      } else {
        if (listResult.status === 'rejected') {
          setError('Live inventory is unavailable right now. Showing a curated sample set.')
        } else {
          setError('No live featured properties are available yet. Showing a curated sample set.')
        }
        setFeatured(PUBLIC_FEATURED_PROPERTIES_FALLBACK)
        setFeaturedSource('fallback')
      }
    }).catch((err) => {
      if (!mounted) return
      setError(err instanceof Error ? err.message : 'Failed to load featured properties')
      setFeatured(PUBLIC_FEATURED_PROPERTIES_FALLBACK)
      setFeaturedSource('fallback')
    }).finally(() => {
      if (mounted) setLoading(false)
    })
    return () => { mounted = false }
  }, [])

  const purposeCopy = PUBLIC_PURPOSE_COPY[search.purpose]

  const liveListingsLabel = useMemo(() => {
    if (typeof portfolioTotal === 'number') return `${portfolioTotal} live listings`
    return 'Curated public inventory'
  }, [portfolioTotal])

  const featuredCards = featured && featured.length > 0 ? featured : PUBLIC_FEATURED_PROPERTIES_FALLBACK

  function toggleSaved(property: Property) {
    setSavedIds((current) => current.includes(property.id) ? current.filter((id) => id !== property.id) : [...current, property.id])
  }

  return (
    <div className="pn-home">
      <section className="pn-hero">
        <div className="pn-hero-copy">
          <span className="pn-kicker">Real estate discovery, management and intelligence in one place</span>
          <h1 className="pn-hero-title">Find Property That Fits Your Life.</h1>
          <p className="pn-hero-lead">Discover homes, investments and opportunities with smarter property search and real estate intelligence.</p>

          <div className="pn-purpose-switcher" role="tablist" aria-label="Property purpose">
            {(['buy', 'rent', 'invest'] as PropertyPurpose[]).map((purpose) => (
              <button
                key={purpose}
                type="button"
                role="tab"
                aria-selected={search.purpose === purpose}
                className={search.purpose === purpose ? 'is-active' : ''}
                onClick={() => setSearch((current) => ({ ...current, purpose }))}
              >
                {purpose.charAt(0).toUpperCase() + purpose.slice(1)}
              </button>
            ))}
          </div>

          <div className="pn-purpose-copy">
            <strong>{purposeCopy.title}</strong>
            <span>{purposeCopy.subtitle}</span>
          </div>

          <form className="pn-search-panel" onSubmit={handleSearch} role="search" aria-label="Homepage property search">
            <div className="pn-search-grid">
              <label className="pn-field">
                <span>Location</span>
                <input
                  type="text"
                  value={search.location}
                  onChange={(event) => setSearch((current) => ({ ...current, location: event.target.value }))}
                  placeholder="Nairobi, Mombasa, Kiambu"
                  aria-label="Location"
                />
              </label>

              <label className="pn-field">
                <span>Property type</span>
                <select
                  value={search.propertyType}
                  onChange={(event) => setSearch((current) => ({ ...current, propertyType: event.target.value }))}
                  aria-label="Property type"
                >
                  {PROPERTY_TYPES.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
                </select>
              </label>

              <label className="pn-field">
                <span>Budget</span>
                <select
                  value={search.budget}
                  onChange={(event) => setSearch((current) => ({ ...current, budget: event.target.value }))}
                  aria-label="Budget"
                >
                  {BUDGETS.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
                </select>
              </label>

              <label className="pn-field">
                <span>Bedrooms</span>
                <select
                  value={search.bedrooms}
                  onChange={(event) => setSearch((current) => ({ ...current, bedrooms: event.target.value }))}
                  aria-label="Bedrooms"
                >
                  {BEDROOMS.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
                </select>
              </label>
            </div>

            <div className="pn-search-actions">
              <button type="submit" className="pn-btn pn-btn-primary">Explore Properties</button>
              <button type="button" className="pn-btn pn-btn-secondary" onClick={() => navigate(buildPropertiesUrl({ match: true }))}>Find My Match</button>
            </div>

            <p className="pn-search-help">{purposeCopy.helper}</p>
          </form>
        </div>

        <div className="pn-hero-visual" aria-hidden="true">
          <div className="pn-hero-image-wrap">
            <img src={HERO_IMAGE} alt="" className="pn-hero-image" loading="eager" />
          </div>
          <div className="pn-hero-panel pn-hero-panel-main">
            <span className="pn-hero-panel-label">Live inventory</span>
            <strong>{liveListingsLabel}</strong>
            <span>{featuredSource === 'fallback' ? 'Sample showcase until live inventory is available.' : 'Featured properties pulled from the live platform.'}</span>
          </div>
          <div className="pn-hero-panel pn-hero-panel-secondary">
            <span className="pn-hero-panel-label">Search intent</span>
            <strong>{purposeCopy.title}</strong>
            <span>{purposeCopy.subtitle}</span>
          </div>
        </div>
      </section>

      <section className="pn-section pn-intro-grid" aria-label="Platform highlights">
        <article className="pn-highlight-card">
          <span className="pn-section-label">01</span>
          <h2>Property discovery built for decision making.</h2>
          <p>Search by purpose, budget, bedroom count and location without losing the broader market context.</p>
        </article>
        <article className="pn-highlight-card">
          <span className="pn-section-label">02</span>
          <h2>Structured for intelligence later.</h2>
          <p>The homepage already separates search, discovery and future market signals so recommendations can plug in cleanly.</p>
        </article>
      </section>

      <section className="pn-section">
        <div className="pn-section-head">
          <div>
            <span className="pn-section-label">Featured properties</span>
            <h2>Featured Properties</h2>
          </div>
          <p>Public listings from the platform when available, with a clearly isolated sample fallback to keep the homepage useful in development.</p>
        </div>

        {loading ? (
          <div className="pn-skeleton-grid" aria-live="polite" aria-busy="true">
            {Array.from({ length: 6 }).map((_, index) => (
              <article key={index} className="pn-skeleton-card card">
                <Skeleton height={220} style={{ borderRadius: 18 }} />
                <div style={{ padding: 16 }}>
                  <Skeleton width="44%" height={12} />
                  <Skeleton width="72%" height={22} style={{ marginTop: 10 }} />
                  <Skeleton width="60%" height={14} style={{ marginTop: 10 }} />
                  <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(3, 1fr)', marginTop: 16 }}>
                    <Skeleton height={48} />
                    <Skeleton height={48} />
                    <Skeleton height={48} />
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <>
            {error && <div className="pn-inline-state pn-inline-state-warning" role="status">{error}</div>}
            <div className="pn-featured-grid" aria-live="polite">
              {featuredCards.map((property) => (
                <PropertyCard
                  key={property.id}
                  p={property}
                  variant="featured"
                  onFavoriteToggle={toggleSaved}
                  isSaved={savedIds.includes(property.id)}
                />
              ))}
            </div>
            <div className="pn-section-footer">
              <span>{portfolioUnits != null ? `${portfolioUnits} managed units in the public inventory` : 'Inventory available on the public platform'}</span>
              <div className="pn-section-footer-actions">
                <Link to="/properties" className="pn-btn pn-btn-ghost">View All Properties</Link>
                <Link to="/buy" className="pn-btn pn-btn-ghost">Browse Buy</Link>
              </div>
            </div>
          </>
        )}
      </section>

      <section className="pn-section">
        <div className="pn-section-head">
          <div>
            <span className="pn-section-label">Matchmaker</span>
            <h2>Don't Just Search. Find Your Match.</h2>
          </div>
          <p>Describe what you need now. The structure is ready for intelligent recommendations later.</p>
        </div>

        <form className="pn-match-panel" onSubmit={(event) => {
          event.preventDefault()
          navigate(buildPropertiesUrl({ match: true }))
        }}>
          <div className="pn-search-grid pn-search-grid-match">
            <label className="pn-field">
              <span>Location</span>
              <input type="text" value={search.location} onChange={(event) => setSearch((current) => ({ ...current, location: event.target.value }))} placeholder="Where do you want to live or invest?" />
            </label>
            <label className="pn-field">
              <span>Budget</span>
              <select value={search.budget} onChange={(event) => setSearch((current) => ({ ...current, budget: event.target.value }))}>
                {BUDGETS.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
              </select>
            </label>
            <label className="pn-field">
              <span>Bedrooms</span>
              <select value={search.bedrooms} onChange={(event) => setSearch((current) => ({ ...current, bedrooms: event.target.value }))}>
                {BEDROOMS.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
              </select>
            </label>
            <label className="pn-field">
              <span>Property type</span>
              <select value={search.propertyType} onChange={(event) => setSearch((current) => ({ ...current, propertyType: event.target.value }))}>
                {PROPERTY_TYPES.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
              </select>
            </label>
            <label className="pn-field">
              <span>Purpose</span>
              <select value={search.purpose} onChange={(event) => setSearch((current) => ({ ...current, purpose: event.target.value as PropertyPurpose }))}>
                <option value="buy">Buy</option>
                <option value="rent">Rent</option>
                <option value="invest">Invest</option>
              </select>
            </label>
          </div>
          <div className="pn-search-actions">
            <button type="submit" className="pn-btn pn-btn-primary">Find My Property</button>
            <button type="button" className="pn-btn pn-btn-secondary" onClick={() => navigate(buildPropertiesUrl({ match: true, purpose: search.purpose }))}>Use My Current Match</button>
          </div>
        </form>
      </section>

      <section className="pn-section">
        <div className="pn-section-head">
          <div>
            <span className="pn-section-label">Locations</span>
            <h2>Explore by Location</h2>
          </div>
          <p>Move directly into the places people already search for most.</p>
        </div>
        <div className="pn-location-grid">
          {PUBLIC_HOME_LOCATIONS.map((location) => (
            <Link key={location.label} to={location.to} className="pn-location-card">
              <span className="pn-location-name">{location.label}</span>
              <span className="pn-location-note">{location.note}</span>
              <span className="pn-location-action">Explore listings</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="pn-section">
        <div className="pn-section-head">
          <div>
            <span className="pn-section-label">Intelligence</span>
            <h2>Understand the Market. Make Better Decisions.</h2>
          </div>
          <p>These capabilities are being structured for future market data and recommendation feeds without pretending the intelligence layer already exists.</p>
        </div>
        <div className="pn-intelligence-grid">
          {PUBLIC_HOME_INTELLIGENCE.map((item) => (
            <Link key={item.title} to="/features" className="pn-intelligence-card">
              <span className="pn-card-status">{item.status}</span>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              <span className="pn-card-link">Learn more</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="pn-section">
        <div className="pn-section-head">
          <div>
            <span className="pn-section-label">How it works</span>
            <h2>How It Works</h2>
          </div>
          <p>A clean path from discovery to action, designed for future client workflows too.</p>
        </div>
        <div className="pn-steps-grid">
          {PUBLIC_HOME_STEPS.map((step) => (
            <article key={step.step} className="pn-step-card">
              <span className="pn-step-number">{step.step}</span>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="pn-section pn-cta-panel">
        <div>
          <span className="pn-section-label">Next step</span>
          <h2>Your Next Property Starts Here.</h2>












































          
          <p>Explore listings or create an account to unlock the next layer of the real estate operating system.</p>
        </div>
        <div className="pn-search-actions">
          <Link to="/properties" className="pn-btn pn-btn-primary">Explore Properties</Link>
          <Link to="/register" className="pn-btn pn-btn-secondary">Create Account</Link>
        </div>
      </section>
    </div>
  )
}