import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import './Home.css'
import { propertyService } from '../services/property'
import { Property } from '../types'
import PropertyCard from '../components/PropertyCard'
import Skeleton from '../components/Skeleton'
import { PUBLIC_FEATURED_PROPERTIES_FALLBACK, PUBLIC_HOME_INTELLIGENCE, PUBLIC_HOME_LOCATIONS, PUBLIC_HOME_STEPS, PUBLIC_PURPOSE_COPY, PropertyPurpose } from '../data/publicHomeContent'
import { PROPERTY_TYPES, BUDGETS, BEDROOMS } from '../data/propertySearchOptions'
import { useTranslation } from '../i18n/LanguageContext'

// FIX: source.unsplash.com (Unsplash Source) was deprecated and shut down in
// 2023 — this hero image was silently failing to load. picsum.photos is a
// stable, still-active placeholder service; a fixed seed keeps the hero
// looking the same on every load instead of changing randomly.
const HERO_IMAGE = 'https://picsum.photos/seed/propnoxa-hero/1200/800'

type SearchState = {
  location: string
  propertyType: string
  budget: string
  bedrooms: string
  purpose: PropertyPurpose
}

export default function Home() {
  const { t } = useTranslation()
  const [search, setSearch] = useState<SearchState>({
    location: '',
    propertyType: '',
    budget: '',
    bedrooms: '',
    purpose: 'buy',
  })
  const [featured, setFeatured] = useState<Property[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [errorKey, setErrorKey] = useState<string | null>(null)
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
    setErrorKey(null)
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
          setErrorKey('home.featured.errorUnavailable')
        } else {
          setErrorKey('home.featured.errorEmpty')
        }
        setFeatured(PUBLIC_FEATURED_PROPERTIES_FALLBACK)
        setFeaturedSource('fallback')
      }
    }).catch(() => {
      if (!mounted) return
      setErrorKey('home.featured.errorFallback')
      setFeatured(PUBLIC_FEATURED_PROPERTIES_FALLBACK)
      setFeaturedSource('fallback')
    }).finally(() => {
      if (mounted) setLoading(false)
    })
    return () => { mounted = false }
  }, [])

  const purposeCopy = PUBLIC_PURPOSE_COPY[search.purpose]

  const liveListingsLabel = typeof portfolioTotal === 'number'
    ? t('home.hero.liveListings', { count: portfolioTotal })
    : t('home.hero.curatedInventory')

  const featuredCards = featured && featured.length > 0 ? featured : PUBLIC_FEATURED_PROPERTIES_FALLBACK

  function toggleSaved(property: Property) {
    setSavedIds((current) => current.includes(property.id) ? current.filter((id) => id !== property.id) : [...current, property.id])
  }

  return (
    <div className="pn-home">
      <section className="pn-hero">
        <div className="pn-hero-copy">
          <span className="pn-kicker">{t('home.kicker')}</span>
          <h1 className="pn-hero-title">{t('home.title')}</h1>
          <p className="pn-hero-lead">{t('home.lead')}</p>

          <div className="pn-purpose-switcher" role="tablist" aria-label={t('home.purpose.aria')}>
            {(['buy', 'rent', 'invest'] as PropertyPurpose[]).map((purpose) => (
              <button
                key={purpose}
                type="button"
                role="tab"
                aria-selected={search.purpose === purpose}
                className={search.purpose === purpose ? 'is-active' : ''}
                onClick={() => setSearch((current) => ({ ...current, purpose }))}
              >
                {t(`nav.${purpose}`)}
              </button>
            ))}
          </div>

          <div className="pn-purpose-copy">
            <strong>{t(purposeCopy.titleKey)}</strong>
            <span>{t(purposeCopy.subtitleKey)}</span>
          </div>

          <form className="pn-search-panel" onSubmit={handleSearch} role="search" aria-label={t('home.search.aria')}>
            <div className="pn-search-grid">
              <label className="pn-field">
                <span>{t('home.search.location')}</span>
                <input
                  type="text"
                  value={search.location}
                  onChange={(event) => setSearch((current) => ({ ...current, location: event.target.value }))}
                  placeholder={t('home.search.locationPlaceholder')}
                  aria-label={t('home.search.location')}
                />
              </label>

              <label className="pn-field">
                <span>{t('home.search.propertyType')}</span>
                <select
                  value={search.propertyType}
                  onChange={(event) => setSearch((current) => ({ ...current, propertyType: event.target.value }))}
                  aria-label={t('home.search.propertyType')}
                >
                  {PROPERTY_TYPES.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
                </select>
              </label>

              <label className="pn-field">
                <span>{t('home.search.budget')}</span>
                <select
                  value={search.budget}
                  onChange={(event) => setSearch((current) => ({ ...current, budget: event.target.value }))}
                  aria-label={t('home.search.budget')}
                >
                  {BUDGETS.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
                </select>
              </label>

              <label className="pn-field">
                <span>{t('home.search.bedrooms')}</span>
                <select
                  value={search.bedrooms}
                  onChange={(event) => setSearch((current) => ({ ...current, bedrooms: event.target.value }))}
                  aria-label={t('home.search.bedrooms')}
                >
                  {BEDROOMS.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
                </select>
              </label>
            </div>

            <div className="pn-search-actions">
              <button type="submit" className="pn-btn pn-btn-primary">{t('home.search.explore')}</button>
              <button type="button" className="pn-btn pn-btn-secondary" onClick={() => navigate(buildPropertiesUrl({ match: true }))}>{t('home.search.findMatch')}</button>
            </div>

            <p className="pn-search-help">{t(purposeCopy.helperKey)}</p>
          </form>
        </div>

        <div className="pn-hero-visual" aria-hidden="true">
          <div className="pn-hero-image-wrap">
            <img src={HERO_IMAGE} alt="" className="pn-hero-image" loading="eager" />
          </div>
          <div className="pn-hero-panel pn-hero-panel-main">
            <span className="pn-hero-panel-label">{t('home.hero.liveInventory')}</span>
            <strong>{liveListingsLabel}</strong>
            <span>{featuredSource === 'fallback' ? t('home.hero.sampleNote') : t('home.hero.liveNote')}</span>
          </div>
          <div className="pn-hero-panel pn-hero-panel-secondary">
            <span className="pn-hero-panel-label">{t('home.hero.searchIntent')}</span>
            <strong>{t(purposeCopy.titleKey)}</strong>
            <span>{t(purposeCopy.subtitleKey)}</span>
          </div>
        </div>
      </section>

      <section className="pn-section pn-intro-grid" aria-label={t('home.intro.aria')}>
        <article className="pn-highlight-card">
          <span className="pn-section-label">01</span>
          <h2>{t('home.intro.card1.title')}</h2>
          <p>{t('home.intro.card1.body')}</p>
        </article>
        <article className="pn-highlight-card">
          <span className="pn-section-label">02</span>
          <h2>{t('home.intro.card2.title')}</h2>
          <p>{t('home.intro.card2.body')}</p>
        </article>
      </section>

      <section className="pn-section">
        <div className="pn-section-head">
          <div>
            <span className="pn-section-label">{t('home.featured.label')}</span>
            <h2>{t('home.featured.title')}</h2>
          </div>
          <p>{t('home.featured.body')}</p>
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
            {errorKey && <div className="pn-inline-state pn-inline-state-warning" role="status">{t(errorKey)}</div>}
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
              <span>{portfolioUnits != null ? t('home.featured.units', { count: portfolioUnits }) : t('home.featured.inventory')}</span>
              <div className="pn-section-footer-actions">
                <Link to="/properties" className="pn-btn pn-btn-ghost">{t('home.featured.viewAll')}</Link>
                <Link to="/buy" className="pn-btn pn-btn-ghost">{t('home.featured.browseBuy')}</Link>
              </div>
            </div>
          </>
        )}
      </section>

      <section className="pn-section">
        <div className="pn-section-head">
          <div>
            <span className="pn-section-label">{t('home.match.label')}</span>
            <h2>{t('home.match.title')}</h2>
          </div>
          <p>{t('home.match.body')}</p>
        </div>

        <form className="pn-match-panel" onSubmit={(event) => {
          event.preventDefault()
          navigate(buildPropertiesUrl({ match: true }))
        }}>
          <div className="pn-search-grid pn-search-grid-match">
            <label className="pn-field">
              <span>{t('home.search.location')}</span>
              <input type="text" value={search.location} onChange={(event) => setSearch((current) => ({ ...current, location: event.target.value }))} placeholder={t('home.match.locationPlaceholder')} />
            </label>
            <label className="pn-field">
              <span>{t('home.search.budget')}</span>
              <select value={search.budget} onChange={(event) => setSearch((current) => ({ ...current, budget: event.target.value }))}>
                {BUDGETS.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
              </select>
            </label>
            <label className="pn-field">
              <span>{t('home.search.bedrooms')}</span>
              <select value={search.bedrooms} onChange={(event) => setSearch((current) => ({ ...current, bedrooms: event.target.value }))}>
                {BEDROOMS.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
              </select>
            </label>
            <label className="pn-field">
              <span>{t('home.search.propertyType')}</span>
              <select value={search.propertyType} onChange={(event) => setSearch((current) => ({ ...current, propertyType: event.target.value }))}>
                {PROPERTY_TYPES.map((option) => <option key={option.label} value={option.value}>{option.label}</option>)}
              </select>
            </label>
            <label className="pn-field">
              <span>{t('home.search.purpose')}</span>
              <select value={search.purpose} onChange={(event) => setSearch((current) => ({ ...current, purpose: event.target.value as PropertyPurpose }))}>
                <option value="buy">{t('nav.buy')}</option>
                <option value="rent">{t('nav.rent')}</option>
                <option value="invest">{t('nav.invest')}</option>
              </select>
            </label>
          </div>
          <div className="pn-search-actions">
            <button type="submit" className="pn-btn pn-btn-primary">{t('home.match.findProperty')}</button>
            <button type="button" className="pn-btn pn-btn-secondary" onClick={() => navigate(buildPropertiesUrl({ match: true, purpose: search.purpose }))}>{t('home.match.useCurrent')}</button>
          </div>
        </form>
      </section>

      <section className="pn-section">
        <div className="pn-section-head">
          <div>
            <span className="pn-section-label">{t('home.locations.label')}</span>
            <h2>{t('home.locations.title')}</h2>
          </div>
          <p>{t('home.locations.body')}</p>
        </div>
        <div className="pn-location-grid">
          {PUBLIC_HOME_LOCATIONS.map((location) => (
            <Link key={location.label} to={location.to} className="pn-location-card">
              <span className="pn-location-name">{location.label}</span>
              <span className="pn-location-note">{t(location.noteKey)}</span>
              <span className="pn-location-action">{t('home.locations.explore')}</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="pn-section">
        <div className="pn-section-head">
          <div>
            <span className="pn-section-label">{t('home.intel.label')}</span>
            <h2>{t('home.intel.title')}</h2>
          </div>
          <p>{t('home.intel.body')}</p>
        </div>
        <div className="pn-intelligence-grid">
          {PUBLIC_HOME_INTELLIGENCE.map((item) => (
            <Link key={item.titleKey} to="/features" className="pn-intelligence-card">
              <span className="pn-card-status">{t(item.statusKey)}</span>
              <h3>{t(item.titleKey)}</h3>
              <p>{t(item.descriptionKey)}</p>
              <span className="pn-card-link">{t('home.intel.learnMore')}</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="pn-section">
        <div className="pn-section-head">
          <div>
            <span className="pn-section-label">{t('home.steps.label')}</span>
            <h2>{t('home.steps.title')}</h2>
          </div>
          <p>{t('home.steps.body')}</p>
        </div>
        <div className="pn-steps-grid">
          {PUBLIC_HOME_STEPS.map((step) => (
            <article key={step.step} className="pn-step-card">
              <span className="pn-step-number">{step.step}</span>
              <h3>{t(step.titleKey)}</h3>
              <p>{t(step.descriptionKey)}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="pn-section pn-cta-panel">
        <div>
          <span className="pn-section-label">{t('home.cta.label')}</span>
          <h2>{t('home.cta.title')}</h2>
          <p>{t('home.cta.body')}</p>
        </div>
        <div className="pn-search-actions">
          <Link to="/properties" className="pn-btn pn-btn-primary">{t('home.search.explore')}</Link>
          <Link to="/register" className="pn-btn pn-btn-secondary">{t('common.createAccount')}</Link>
        </div>
      </section>
    </div>
  )
}
