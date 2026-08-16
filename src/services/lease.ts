import { api } from './api'

export interface Lease {
  id: number
  tenant_id: number
  unit_id: number
  property_id: number
  start_date: string
  end_date: string
  rent_amount: string
  deposit?: string | null
  payment_due_date?: number | null
  status: string
  notes?: string | null
  created_at?: string
  updated_at?: string
}

export interface LeaseCreate {
  tenant_id: number
  unit_id: number
  property_id: number
  start_date: string
  end_date: string
  rent_amount: string
  deposit?: string
  payment_due_date?: number
  status?: string
  notes?: string
}

export interface LeaseUpdate {
  start_date?: string
  end_date?: string
  rent_amount?: string
  deposit?: string
  payment_due_date?: number
  status?: string
  notes?: string
}

export interface LeaseRenew {
  new_end_date: string
  new_rent_amount?: string
  notes?: string
}

export interface LeaseTerminate {
  termination_date: string
  reason?: string
  notes?: string
}

export const leaseService = {
  list: async (params?: {
    skip?: number
    limit?: number
    property_id?: number
    unit_id?: number
    tenant_id?: number
    status?: string
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.property_id) queryParams.append('property_id', params.property_id.toString())
    if (params?.unit_id) queryParams.append('unit_id', params.unit_id.toString())
    if (params?.tenant_id) queryParams.append('tenant_id', params.tenant_id.toString())
    if (params?.status) queryParams.append('status', params.status)
    
    return api.request<Lease[]>(`/api/leases/?${queryParams}`)
  },

  get: async (leaseId: number) => {
    return api.request<Lease>(`/api/leases/${leaseId}`)
  },

  create: async (data: LeaseCreate) => {
    return api.request<Lease>('/api/leases/', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  update: async (leaseId: number, data: LeaseUpdate) => {
    return api.request<Lease>(`/api/leases/${leaseId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  delete: async (leaseId: number) => {
    return api.request<void>(`/api/leases/${leaseId}`, {
      method: 'DELETE'
    })
  },

  renew: async (leaseId: number, data: LeaseRenew) => {
    return api.request<Lease>(`/api/leases/${leaseId}/renew`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  terminate: async (leaseId: number, data: LeaseTerminate) => {
    return api.request<Lease>(`/api/leases/${leaseId}/terminate`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  getExpiringSoon: async (params?: {
    days?: number
    skip?: number
    limit?: number
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.days) queryParams.append('days', params.days.toString())
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    
    return api.request<Lease[]>(`/api/leases/expiring-soon?${queryParams}`)
  }
}