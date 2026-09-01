import React, { useEffect, useState } from 'react'
import { Property } from '../types'
import { Link } from 'react-router-dom'
import { useFavorites } from '../contexts/FavoriteContext'
import { useAuth } from '../contexts/AuthContext'
import { NON_RESIDENTIAL_TYPES } from '../data/propertySearchOptions'
import { resolvePropertyImage, placeholderPropertyImage } from '../utils/propertyImages'

type PropertyCardProps = {
  p: Property
  variant?: 'default' | 'featured'
  onFavoriteToggle?: (property: Property) => void
  isSaved?: boolean
  fromPath?: string
}

function formatArea(area?: string | number | null) {
  if (area === null || area === undefined || area === '') return null
  return typeof area === 'number' ? `${area} sqm` : area
}

function formatPrice(property: Property) {
  if (property.price_label) return property.price_label
  if (typeof property.price === 'number') return new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES', maximumFractionDigits: 0 }).format(property.price)
  if (typeof property.price === 'string' && property.price.trim()) return property.price
  return null
}

// FIX: a warehouse or a plot of land showing "0 beds · 0 baths" reads as a
// data error rather than as "not applicable". Hide those badges entirely for
// property types that don't logically carry a bedroom/bathroom count instead
// of displaying zero.
function isResidentialType(propertyType?: string | null): boolean {
  if (!propertyType) return true
  return !NON_RESIDENTIAL_TYPES.includes(propertyType)
}

const PropertyCard: React.FC<PropertyCardProps> = ({p, variant = 'default', onFavoriteToggle, isSaved = false, fromPath}) => {
  const { user } = useAuth()
  const { isFavorite: checkFavorite, addFavorite, removeFavorite } = useFavorites()
  const actuallyIsFavorite = checkFavorite(p.id) || isSaved
  const canFavorite = user && onFavoriteToggle

  // Show a stable placeholder immediately, then swap in a real Pexels photo
  // once resolved (or an explicit image_url, which resolvePropertyImage
  // always prefers). Never blocks the card's initial render on the network.
  const [img, setImg] = useState(() => placeholderPropertyImage(p))
  useEffect(() => {
    let cancelled = false
    setImg(placeholderPropertyImage(p))
    resolvePropertyImage(p).then((url) => { if (!cancelled) setImg(url) })
    return () => { cancelled = true }
  }, [p.id, p.image_url, p.property_type, p.purpose])

  const price = formatPrice(p)
  const area = formatArea(p.area)
  const location = [p.city, p.country].filter(Boolean).join(', ') || p.address || 'Location available on request'
  const variantLabel = variant === 'featured' ? 'Featured listing' : p.status || 'Listing'
  const showBedBath = isResidentialType(p.property_type)
  const summaryItems = [
    showBedBath && typeof p.bedrooms === 'number' ? `${p.bedrooms} bed${p.bedrooms === 1 ? '' : 's'}` : null,
    showBedBath && typeof p.bathrooms === 'number' ? `${p.bathrooms} bath${p.bathrooms === 1 ? '' : 's'}` : null,
    area,
    p.units_count != null ? `${p.units_count} units` : null,
  ].filter(Boolean) as string[]

  async function handleFavoriteClick() {
    if (!user) return
    
    try {
      if (actuallyIsFavorite) {
        await removeFavorite(p.id)
      } else {
        await addFavorite(p.id)
      }
      if (onFavoriteToggle) onFavoriteToggle(p)
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
    }
  }

  return (
    <article className={`property-card card ${variant === 'featured' ? 'property-card--featured' : ''}`}>
      <div className="property-card-media" style={{ backgroundImage: `url(${img})` }} aria-hidden="true">
        <div className="property-card-overlay" />
        <div className="property-card-media-top">
          <span className="property-card-pill">{variantLabel}</span>
          {price && <span className="property-card-price-badge">{price}</span>}
        </div>
        {canFavorite && (
          <button
            type="button"
            className={`property-card-save ${actuallyIsFavorite ? 'is-saved' : ''}`}
            aria-pressed={actuallyIsFavorite}
            onClick={handleFavoriteClick}
          >
            {actuallyIsFavorite ? 'Saved' : 'Save'}
          </button>
        )}
      </div>

      <div className="property-card-body">
        <div className="property-card-header">
          <div>
            <p className="property-card-type">{p.property_type || 'Property'}</p>
            <h3 className="property-card-title">{p.name}</h3>
          </div>
          <span className="property-card-status">{p.status || 'active'}</span>
        </div>

        <p className="property-card-location">{location}</p>

        {variant === 'featured' ? (
          <>
            <div className="property-card-price">{price || 'Price on request'}</div>
            <dl className="property-card-specs" aria-label="Property details">
              {summaryItems.slice(0, 4).map((item) => (
                <div key={item} className="property-card-spec">
                  <dt>{item.split(' ')[1] ?? 'Detail'}</dt>
                  <dd>{item}</dd>
                </div>
              ))}
            </dl>
          </>
        ) : (
          <div className="property-card-meta">
            {summaryItems.length > 0 ? summaryItems.join(' • ') : `${p.units_count ?? 0} units`}
          </div>
        )}

        <div className="property-card-actions">
          <Link 
            to={`/properties/${p.id}${fromPath ? `?from=${encodeURIComponent(fromPath)}` : ''}`} 
            className="button nav-cta-ghost property-card-action"
          >
            View Details
          </Link>
          {variant === 'default' && (
            <Link to={`/app/properties/${p.id}/edit`} className="button muted property-card-action">Manage</Link>
          )}
          {variant === 'featured' && canFavorite && (
            <button type="button" className={`button muted property-card-action ${actuallyIsFavorite ? 'is-saved' : ''}`} onClick={handleFavoriteClick}>
              {actuallyIsFavorite ? 'Saved' : 'Save listing'}
            </button>
          )}
        </div>
      </div>
    </article>
  )
}

export default PropertyCard