import { api } from './api'

export interface Maintenance {
  id: number
  property_id: number
  title: string
  description?: string | null
  category?: string | null
  priority: string
  status: string
  tenant_id?: number | null
  unit_id?: number | null
  assigned_manager_id?: number | null
  cost?: string | null
  notes?: string | null
  created_at?: string
  updated_at?: string
  resolved_at?: string | null
}

export interface MaintenanceCreate {
  property_id: number
  title: string
  description?: string
  category?: string
  priority?: string
  status?: string
  tenant_id?: number
  unit_id?: number
  assigned_manager_id?: number
  cost?: string
  notes?: string
}

export interface MaintenanceUpdate {
  title?: string
  description?: string
  category?: string
  priority?: string
  status?: string
  assigned_manager_id?: number
  cost?: string
  notes?: string
  resolved_at?: string
}

export interface MaintenanceAssign {
  assigned_manager_id: number
  notes?: string
}

export interface MaintenanceResolve {
  resolution_notes?: string
  cost?: string
}

export const maintenanceService = {
  list: async (params?: {
    skip?: number
    limit?: number
    property_id?: number
    unit_id?: number
    tenant_id?: number
    status?: string
    priority?: string
    assigned_manager_id?: number
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.property_id) queryParams.append('property_id', params.property_id.toString())
    if (params?.unit_id) queryParams.append('unit_id', params.unit_id.toString())
    if (params?.tenant_id) queryParams.append('tenant_id', params.tenant_id.toString())
    if (params?.status) queryParams.append('status', params.status)
    if (params?.priority) queryParams.append('priority', params.priority)
    if (params?.assigned_manager_id) queryParams.append('assigned_manager_id', params.assigned_manager_id.toString())
    
    return api.request<Maintenance[]>(`/api/maintenance/?${queryParams}`)
  },

  get: async (requestId: number) => {
    return api.request<Maintenance>(`/api/maintenance/${requestId}`)
  },

  create: async (data: MaintenanceCreate) => {
    return api.request<Maintenance>('/api/maintenance/', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  update: async (requestId: number, data: MaintenanceUpdate) => {
    return api.request<Maintenance>(`/api/maintenance/${requestId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  delete: async (requestId: number) => {
    return api.request<void>(`/api/maintenance/${requestId}`, {
      method: 'DELETE'
    })
  },

  assign: async (requestId: number, data: MaintenanceAssign) => {
    return api.request<Maintenance>(`/api/maintenance/${requestId}/assign`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  resolve: async (requestId: number, data: MaintenanceResolve) => {
    return api.request<Maintenance>(`/api/maintenance/${requestId}/resolve`, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  getTenantMaintenance: async (tenantId: number, params?: {
    skip?: number
    limit?: number
    status?: string
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.status) queryParams.append('status', params.status)
    
    return api.request<Maintenance[]>(`/api/maintenance/tenants/${tenantId}/maintenance?${queryParams}`)
  },

  getPropertyMaintenance: async (propertyId: number, params?: {
    skip?: number
    limit?: number
    status?: string
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.status) queryParams.append('status', params.status)
    
    return api.request<Maintenance[]>(`/api/maintenance/properties/${propertyId}/maintenance?${queryParams}`)
  }
}