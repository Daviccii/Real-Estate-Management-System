import { api } from './api'
import { Building } from '../types'

export interface BuildingCreatePayload {
  property_id: number
  name: string
  total_floors?: number
  units_count?: number
  amenities?: string
  year_built?: number
  description?: string
}

export interface BuildingUpdatePayload {
  name?: string
  total_floors?: number
  units_count?: number
  amenities?: string
  year_built?: number
  description?: string
}

export async function getBuildings(propertyId?: number): Promise<Building[]> {
  const query = propertyId ? `?property_id=${propertyId}` : ''
  return api.request<Building[]>(`/api/buildings${query}`)
}

export async function getBuilding(id: number): Promise<Building> {
  return api.request<Building>(`/api/buildings/${id}`)
}

export async function createBuilding(payload: BuildingCreatePayload): Promise<Building> {
  return api.request<Building>('/api/buildings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function updateBuilding(id: number, payload: BuildingUpdatePayload): Promise<Building> {
  return api.request<Building>(`/api/buildings/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function deleteBuilding(id: number): Promise<void> {
  return api.request<void>(`/api/buildings/${id}`, {
    method: 'DELETE'
  })
}
