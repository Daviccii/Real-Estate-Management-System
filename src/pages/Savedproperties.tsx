import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { propertyService } from '../services/property'
import { useFavorites } from '../contexts/FavoriteContext'
import { useAuth } from '../contexts/AuthContext'
import { Property } from '../types'
import PropertyGrid from '../components/PropertyGrid'

const SavedPropertiesPage: React.FC = () => {
  const { user } = useAuth()
  const { favorites, loading: favoritesLoading } = useFavorites()
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return
    if (favorites.length === 0) {
      setProperties([])
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    // FavoriteContext only tracks property ids, not full property records, so
    // each favorited id is resolved individually via the public detail
    // endpoint. Failed lookups (e.g. a since-deleted property) are dropped
    // rather than failing the whole page.
    Promise.all(favorites.map((id) => propertyService.getPublic(id).catch(() => null)))
      .then((results) => {
        if (cancelled) return
        setProperties(results.filter((p): p is Property => p !== null))
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load saved properties')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [favorites, user])

  if (!user) {
    return (
      <div className="page">
        <h2>Saved Properties</h2>
        <div className="empty">
          Please <Link to="/login" style={{color:'var(--primary)'}}>sign in</Link> to view properties you've saved.
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div style={{marginBottom:12}}>
        <h2>Saved Properties</h2>
        <p style={{color:'var(--text-secondary)',margin:0}}>Properties you've saved for later</p>
      </div>

      <PropertyGrid
        properties={properties}
        loading={loading || favoritesLoading}
        error={error}
        emptyMessage="You haven't saved any properties yet. Browse listings and tap Save to add them here."
      />
    </div>
  )
}

export default SavedPropertiesPage