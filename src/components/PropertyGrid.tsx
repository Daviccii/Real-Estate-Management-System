import React from 'react'
import { useLocation } from 'react-router-dom'
import { Property } from '../types'
import PropertyCard from './PropertyCard'

interface PropertyGridProps {
  properties: Property[]
  loading?: boolean
  error?: string | null
  emptyMessage?: string
}

const PropertyGrid: React.FC<PropertyGridProps> = ({ 
  properties, 
  loading = false, 
  error = null,
  emptyMessage = 'No properties found'
}) => {
  const location = useLocation()
  const currentPath = location.pathname

  if (loading) {
    return <div className="empty">Loading properties…</div>
  }

  if (error) {
    return <div style={{color:'var(--danger)'}}>{error}</div>
  }

  if (!properties || properties.length === 0) {
    return <div className="empty">{emptyMessage}</div>
  }

  return (
    <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))',gap:16}}>
      {properties.map(property => (
        <PropertyCard key={property.id} p={property} fromPath={currentPath} />
      ))}
    </div>
  )
}

export default PropertyGrid