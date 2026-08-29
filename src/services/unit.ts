import { api } from './api'

export interface Unit {
  id: number
  property_id: number
  unit_number: string
  unit_type?: string | null
  bedrooms?: number | null
  bathrooms?: number | null
  area?: string | null
  rent?: string | null
  status: string
  availability_date?: string | null
  created_at?: string
  updated_at?: string
}

export interface UnitCreate {
  property_id: number
  unit_number: string
  unit_type?: string
  bedrooms?: number
  bathrooms?: number
  area?: string
  rent?: string
  status?: string
  availability_date?: string
}

export interface UnitUpdate {
  unit_number?: string
  unit_type?: string
  bedrooms?: number
  bathrooms?: number
  area?: string
  rent?: string
  status?: string
  availability_date?: string
}

// FIX: removed the hardcoded `/api/` prefix — see lease.ts for the full
// explanation. VITE_API_BASE already includes `/api`, so these calls were
// resolving to `.../api/api/units/...` and 404ing.
export const unitService = {
  list: async (params?: {
    skip?: number
    limit?: number
    property_id?: number
    status?: string
    unit_type?: string
    bedrooms?: number
    min_rent?: string
    max_rent?: string
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.property_id) queryParams.append('property_id', params.property_id.toString())
    if (params?.status) queryParams.append('status', params.status)
    if (params?.unit_type) queryParams.append('unit_type', params.unit_type)
    if (params?.bedrooms) queryParams.append('bedrooms', params.bedrooms.toString())
    if (params?.min_rent) queryParams.append('min_rent', params.min_rent)
    if (params?.max_rent) queryParams.append('max_rent', params.max_rent)

    return api.request<Unit[]>(`/units/?${queryParams}`)
  },

  get: async (unitId: number) => {
    return api.request<Unit>(`/units/${unitId}`)
  },

  create: async (data: UnitCreate) => {
    return api.request<Unit>(`/units/`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  update: async (unitId: number, data: UnitUpdate) => {
    return api.request<Unit>(`/units/${unitId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  delete: async (unitId: number) => {
    return api.request<void>(`/units/${unitId}`, {
      method: 'DELETE'
    })
  },

  getPropertyUnits: async (propertyId: number, params?: {
    skip?: number
    limit?: number
    status?: string
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.status) queryParams.append('status', params.status)

    return api.request<Unit[]>(`/units/properties/${propertyId}/units?${queryParams}`)
  }
}
