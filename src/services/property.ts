import { api } from './api'
import { Property } from '../types'
import { getToken } from './token'

const list = async (params?: { skip?: number; limit?: number; search?: string; property_type?: string; city?: string; status?: string; sort?: string; purpose?: string }): Promise<Property[]> => {
  const qs = new URLSearchParams()
  if (typeof params?.skip === 'number') qs.set('skip', String(params.skip))
  if (typeof params?.limit === 'number') qs.set('limit', String(params.limit))
  if (params?.search) qs.set('search', params.search)
  if (params?.property_type) qs.set('property_type', params.property_type)
  if (params?.city) qs.set('city', params.city)
  if (params?.status) qs.set('status', params.status)
  if (params?.sort) qs.set('sort', params.sort)
  if (params?.purpose) qs.set('purpose', params.purpose)
  const base = getToken() ? '/properties' : '/properties/public'
  const query = qs.toString()
  return api.request(query ? `${base}?${query}` : base)
}

const pagedList = async (page = 1, limit = 6, params?: { search?: string; property_type?: string; city?: string; status?: string; sort?: string; purpose?: string }): Promise<Property[]> => {
  const skip = Math.max(0, (page - 1) * limit)
  return list(Object.assign({}, params || {}, { skip, limit }))
}

const meta = async (): Promise<{ total: number; total_units: number } | null> => {
  const base = getToken() ? '/properties' : '/properties/public'
  return api.request(`${base}/meta`)
}

const marketInsights = async (): Promise<{
  total_properties: number
  by_purpose: Record<string, number>
  by_type: Record<string, number>
  top_locations: Array<{ city: string; count: number }>
  by_status: Record<string, number>
} | null> => {
  const base = getToken() ? '/properties' : '/properties/public'
  return api.request(`${base}/market-insights`)
}

const get = async (id: number): Promise<Property | null> => {
  return api.request(`/properties/${id}`)
}

const create = async (payload: Partial<Property>): Promise<Property | null> => {
  return api.request('/properties/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

const update = async (id: number, payload: Partial<Property>): Promise<Property | null> => {
  return api.request(`/properties/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

const remove = async (id: number): Promise<boolean> => {
  await api.request(`/properties/${id}`, { method: 'DELETE' })
  return true
}

export const propertyService = { list, pagedList, meta, marketInsights, get, create, update, delete: remove }
