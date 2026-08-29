import React from 'react'
import { useLocation } from 'react-router-dom'
import { Property } from '../types'
import PropertyCard from './PropertyCard'
import Skeleton from './Skeleton'
import './PropertyGrid.css'

interface PropertyGridProps {
  properties: Property[]
  loading?: boolean
  error?: string | null
  emptyMessage?: string
}

const SKELETON_COUNT = 6

const PropertyGrid: React.FC<PropertyGridProps> = ({ 
  properties, 
  loading = false, 
  error = null,
  emptyMessage = 'No properties found'
}) => {
  const location = useLocation()
  const currentPath = location.pathname

  if (loading) {
    return (
      <div className="pn-grid-skeleton" aria-live="polite" aria-busy="true">
        {Array.from({ length: SKELETON_COUNT }).map((_, index) => (
          <article key={index} className="pn-grid-skeleton-card card">
            <Skeleton height={200} style={{ borderRadius: 16 }} />
            <div style={{ padding: 16 }}>
              <Skeleton width="40%" height={12} />
              <Skeleton width="70%" height={20} style={{ marginTop: 10 }} />
              <Skeleton width="55%" height={14} style={{ marginTop: 10 }} />
            </div>
          </article>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="pn-grid-state pn-grid-state-error" role="alert">
        <span className="pn-grid-state-icon" aria-hidden="true">⚠</span>
        <p>{error}</p>
      </div>
    )
  }

  if (!properties || properties.length === 0) {
    return (
      <div className="pn-grid-state" role="status">
        <span className="pn-grid-state-icon" aria-hidden="true">🏠</span>
        <p>{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="pn-grid">
      {properties.map(property => (
        <PropertyCard key={property.id} p={property} fromPath={currentPath} />
      ))}
    </div>
  )
}

export default PropertyGrid