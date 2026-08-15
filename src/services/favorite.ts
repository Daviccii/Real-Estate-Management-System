import { api } from './api'
import { getToken } from './token'

interface Favorite {
  id: number
  user_id: number
  property_id: number
  created_at: string
}

const add = async (propertyId: number): Promise<Favorite> => {
  return api.request('/favorites/', {
    method: 'POST',
    body: JSON.stringify({ property_id }),
  })
}

const remove = async (propertyId: number): Promise<void> => {
  return api.request(`/favorites/${propertyId}`, { method: 'DELETE' })
}

const list = async (): Promise<Favorite[]> => {
  return api.request('/favorites/')
}

const check = async (propertyId: number): Promise<{ is_favorite: boolean }> => {
  return api.request(`/favorites/${propertyId}`)
}

export const favoriteService = { add, remove, list, check }