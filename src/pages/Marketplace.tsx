import React, { useEffect, useState } from 'react'

import { useAuth } from '../contexts/AuthContext'
import { getMarketplaceProviders, getProviderReviews } from '../services/serviceMarketplace'
import type { Paginated, ProviderReviewPage, ServiceProviderProfile } from '../types'

const SPECIALTIES = [
  'Plumbing',
  'Electrical',
  'HVAC',
  'Carpentry',
  'Painting',
  'Masonry',
  'Roofing',
  'Cleaning',
  'Security',
  'Appliance Repair',
  'General Maintenance',
]

const SORTS: { value: 'rating' | 'jobs' | 'newest' | 'name'; label: string }[] = [
  { value: 'rating', label: 'Top rated' },
  { value: 'jobs', label: 'Most jobs completed' },
  { value: 'newest', label: 'Newest' },
  { value: 'name', label: 'Name (A–Z)' },
]

const ROLE_HEADINGS: Record<string, { title: string; eyebrow: string }> = {
  admin: { title: 'Service Marketplace', eyebrow: 'Platform marketplace' },
  manager: { title: 'Service Marketplace', eyebrow: 'Vendor network' },
  owner: { title: 'Service Marketplace', eyebrow: 'Vendor network' },
  landlord: { title: 'Service Marketplace', eyebrow: 'Vendor network' },
}

const stars = (score: number | null): string => {
  if (score === null || score === undefined) return '☆☆☆☆☆'
  const filled = Math.max(0, Math.min(5, Math.round(score)))
  return '★'.repeat(filled) + '☆'.repeat(5 - filled)
}

const formatMoney = (value?: string | null): string => {
  if (value === null || value === undefined || value === '') return '—'
  const numeric = Number(value)
  return Number.isFinite(numeric) ? `KSh ${numeric.toLocaleString()}` : `KSh ${value}`
}

const Marketplace: React.FC = () => {
  const { user } = useAuth()
  const [searchInputs, setSearchInputs] = useState({ q: '', city: '' })
  const [category, setCategory] = useState('')
  const [sort, setSort] = useState<'rating' | 'jobs' | 'newest' | 'name'>('rating')
  const [availableOnly, setAvailableOnly] = useState(false)
  const [applied, setApplied] = useState({ q: '', city: '' })
  const [page, setPage] = useState(1)

  const [result, setResult] = useState<Paginated<ServiceProviderProfile> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [selected, setSelected] = useState<ServiceProviderProfile | null>(null)
  const [reviews, setReviews] = useState<ProviderReviewPage | null>(null)
  const [reviewPage, setReviewPage] = useState(1)
  const [reviewsLoading, setReviewsLoading] = useState(false)
  const [reviewsError, setReviewsError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getMarketplaceProviders({
      q: applied.q || undefined,
      city: applied.city || undefined,
      category: category || undefined,
      available_only: availableOnly || undefined,
      sort,
      page,
      page_size: 12,
    })
      .then((response) => {
        if (!cancelled) setResult(response)
      })
      .catch((err: any) => {
        if (!cancelled) setError(err?.message || 'Failed to load service providers')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [applied, category, availableOnly, sort, page])

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    setReviewsLoading(true)
    setReviewsError(null)
    getProviderReviews(selected.id, reviewPage, 10)
      .then((response) => {
        if (!cancelled) setReviews(response)
      })
      .catch((err: any) => {
        if (!cancelled) setReviewsError(err?.message || 'Failed to load reviews')
      })
      .finally(() => {
        if (!cancelled) setReviewsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [selected, reviewPage])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setApplied({ q: searchInputs.q.trim(), city: searchInputs.city.trim() })
    setPage(1)
  }

  const openProvider = (provider: ServiceProviderProfile) => {
    setSelected(provider)
    setReviews(null)
    setReviewPage(1)
  }

  const role = (user?.role || '').toLowerCase()
  const heading = ROLE_HEADINGS[role] || { title: 'Service Marketplace', eyebrow: 'Vendor network' }
  const eyebrowClass = ['admin', 'manager', 'owner', 'landlord'].includes(role) ? `${role}-eyebrow` : 'manager-eyebrow'

  const totalPages = result ? Math.max(1, Math.ceil(result.total / result.page_size)) : 1
  const reviewTotalPages = reviews ? Math.max(1, Math.ceil(reviews.total / reviews.page_size)) : 1

  return (
    <div className="management-container">
      <div className="management-header">
        <span className={eyebrowClass}>{heading.eyebrow}</span>
        <h1>{heading.title}</h1>
        <p>Verified contractors with real customer ratings, completed job counts and coverage areas.</p>
      </div>

      <form onSubmit={handleSearch} className="controls-section" role="search" style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          className="input"
          placeholder="Search business, trade or area…"
          aria-label="Search providers"
          value={searchInputs.q}
          onChange={(e) => setSearchInputs((prev) => ({ ...prev, q: e.target.value }))}
          style={{ minWidth: 220 }}
        />
        <input
          className="input"
          placeholder="City / area"
          aria-label="Filter by city"
          value={searchInputs.city}
          onChange={(e) => setSearchInputs((prev) => ({ ...prev, city: e.target.value }))}
          style={{ width: 150 }}
        />
        <select
          className="input"
          aria-label="Filter by specialty"
          value={category}
          onChange={(e) => {
            setCategory(e.target.value)
            setPage(1)
          }}
        >
          <option value="">All specialties</option>
          {SPECIALTIES.map((specialty) => (
            <option key={specialty} value={specialty}>{specialty}</option>
          ))}
        </select>
        <select
          className="input"
          aria-label="Sort providers"
          value={sort}
          onChange={(e) => {
            setSort(e.target.value as typeof sort)
            setPage(1)
          }}
        >
          {SORTS.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--muted)' }}>
          <input
            type="checkbox"
            checked={availableOnly}
            onChange={(e) => {
              setAvailableOnly(e.target.checked)
              setPage(1)
            }}
          />
          Available now
        </label>
        <button type="submit" className="button">Search</button>
      </form>

      {loading && <div className="empty">Loading service providers…</div>}
      {error && <div className="empty error">{error}</div>}

      {!loading && !error && result && (
        <>
          <div style={{ fontSize: 13, color: 'var(--muted)', margin: '4px 0 12px' }}>
            {result.total} provider{result.total === 1 ? '' : 's'} found
          </div>

          {result.items.length === 0 ? (
            <div className="empty">No providers match these filters yet.</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: 16 }}>
              {result.items.map((provider) => (
                <div key={provider.id} className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontWeight: 800, fontSize: 15 }}>{provider.company_name}</div>
                      <div style={{ fontSize: 12, color: 'var(--muted)' }}>{provider.specialty || provider.categories?.[0]}</div>
                    </div>
                    {provider.insurance_verified && (
                      <span className="badge" title="Platform-verified credentials" style={{ background: '#d1fae5', color: '#047857' }}>✓ Verified</span>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                    <span style={{ color: '#d97706', letterSpacing: 1 }}>{stars(provider.rating_avg)}</span>
                    <span style={{ fontWeight: 700 }}>
                      {provider.rating_avg !== null && provider.rating_avg !== undefined ? provider.rating_avg.toFixed(1) : 'New'}
                    </span>
                    <span style={{ color: 'var(--muted)' }}>
                      ({provider.reviews_count} review{provider.reviews_count === 1 ? '' : 's'})
                    </span>
                  </div>

                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                    {provider.completed_jobs_count} completed job{provider.completed_jobs_count === 1 ? '' : 's'}
                    {' · '}{formatMoney(provider.hourly_rate)}/hr
                  </div>

                  {(provider.service_areas || []).length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {provider.service_areas.slice(0, 4).map((area) => (
                        <span key={area} className="badge" style={{ fontSize: 11 }}>{area}</span>
                      ))}
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: 8 }}>
                    <span className={`badge ${provider.is_available ? 'status-resolved' : ''}`} style={!provider.is_available ? { background: '#e2e8f0', color: '#475569' } : undefined}>
                      {provider.is_available ? 'Available' : 'Unavailable'}
                    </span>
                    <button type="button" className="button small" onClick={() => openProvider(provider)}>
                      View reviews
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, marginTop: 20 }}>
              <button type="button" className="button small" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>← Prev</button>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>Page {page} of {totalPages}</span>
              <button type="button" className="button small" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next →</button>
            </div>
          )}
        </>
      )}

      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal-content" style={{ maxWidth: 640 }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2 style={{ margin: 0 }}>{selected.company_name}</h2>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                  {selected.specialty || selected.categories?.[0]} · {selected.completed_jobs_count} completed jobs
                </div>
              </div>
              <button onClick={() => setSelected(null)} className="close-button" aria-label="Close">✕</button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '10px 0 16px' }}>
              <span style={{ fontSize: 20, color: '#d97706', letterSpacing: 2 }}>{stars(selected.rating_avg)}</span>
              <span style={{ fontWeight: 800, fontSize: 18 }}>
                {selected.rating_avg !== null && selected.rating_avg !== undefined ? selected.rating_avg.toFixed(1) : '—'}
              </span>
              <span style={{ color: 'var(--muted)', fontSize: 13 }}>
                {selected.reviews_count} review{selected.reviews_count === 1 ? '' : 's'}
              </span>
            </div>

            {selected.bio && (
              <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 14 }}>{selected.bio}</p>
            )}

            {reviewsLoading && <div className="empty">Loading reviews…</div>}
            {reviewsError && <div className="empty error">{reviewsError}</div>}
            {!reviewsLoading && !reviewsError && reviews && (
              <>
                {reviews.items.length === 0 ? (
                  <div className="empty">No reviews yet — ratings appear after completed work orders.</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {reviews.items.map((review) => (
                      <div key={review.id} style={{ border: '1px solid var(--border, rgba(15,23,42,.08))', borderRadius: 14, padding: '12px 14px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 700, fontSize: 13 }}>{review.reviewer_name}</span>
                          <span style={{ color: '#d97706', letterSpacing: 1 }}>{stars(review.score)}</span>
                        </div>
                        {review.comment && (
                          <p style={{ fontSize: 13, margin: '8px 0 0' }}>{review.comment}</p>
                        )}
                        <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 8 }}>
                          {review.maintenance_title ? `${review.maintenance_title} · ` : ''}
                          {review.created_at ? new Date(review.created_at).toLocaleDateString() : ''}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {reviewTotalPages > 1 && (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, marginTop: 16 }}>
                    <button type="button" className="button small" disabled={reviewPage <= 1} onClick={() => setReviewPage((p) => p - 1)}>← Newer</button>
                    <span style={{ fontSize: 12, color: 'var(--muted)' }}>Page {reviewPage} of {reviewTotalPages}</span>
                    <button type="button" className="button small" disabled={reviewPage >= reviewTotalPages} onClick={() => setReviewPage((p) => p + 1)}>Older →</button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default Marketplace
