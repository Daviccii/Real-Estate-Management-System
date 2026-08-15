import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { favoriteService } from '../services/favorite'
import { useAuth } from './AuthContext'

interface FavoriteContextType {
  favorites: number[]
  addFavorite: (propertyId: number) => Promise<void>
  removeFavorite: (propertyId: number) => Promise<void>
  isFavorite: (propertyId: number) => boolean
  loading: boolean
  refreshFavorites: () => Promise<void>
}

const FavoriteContext = createContext<FavoriteContextType | undefined>(undefined)

export const useFavorites = () => {
  const context = useContext(FavoriteContext)
  if (!context) {
    throw new Error('useFavorites must be used within a FavoriteProvider')
  }
  return context
}

export const FavoriteProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [favorites, setFavorites] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const { user } = useAuth()

  const refreshFavorites = useCallback(async () => {
    if (!user) {
      setFavorites([])
      return
    }

    try {
      setLoading(true)
      const userFavorites = await favoriteService.list()
      setFavorites(userFavorites.map(f => f.property_id))
    } catch (error) {
      console.error('Failed to load favorites:', error)
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    refreshFavorites()
  }, [refreshFavorites])

  const addFavorite = useCallback(async (propertyId: number) => {
    if (!user) {
      throw new Error('User not authenticated')
    }

    try {
      await favoriteService.add(propertyId)
      setFavorites(prev => [...prev, propertyId])
    } catch (error) {
      console.error('Failed to add favorite:', error)
      throw error
    }
  }, [user])

  const removeFavorite = useCallback(async (propertyId: number) => {
    if (!user) {
      throw new Error('User not authenticated')
    }

    try {
      await favoriteService.remove(propertyId)
      setFavorites(prev => prev.filter(id => id !== propertyId))
    } catch (error) {
      console.error('Failed to remove favorite:', error)
      throw error
    }
  }, [user])

  const isFavorite = useCallback((propertyId: number) => {
    return favorites.includes(propertyId)
  }, [favorites])

  const value: FavoriteContextType = {
    favorites,
    addFavorite,
    removeFavorite,
    isFavorite,
    loading,
    refreshFavorites,
  }

  return (
    <FavoriteContext.Provider value={value}>
      {children}
    </FavoriteContext.Provider>
  )
}