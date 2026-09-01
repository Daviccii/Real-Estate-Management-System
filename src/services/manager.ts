import { api } from './api'

interface ManagerProperty {
  id: number
  name: string
  city: string | null
  owner_id: number
  manager_id: number | null
  status: string
  purpose: string | null
  property_type: string | null
  units_count: number | null
  address: string | null
  bedrooms: number | null
  bathrooms: number | null
  price_label: string | null
  image_url: string | null
  created_at: string | null
  updated_at: string | null
}

interface ManagerTenant {
  id: number
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string | null
}

interface ManagerLease {
  id: number
  tenant_id: number
  property_id: number
  unit_id: number | null
  start_date: string | null
  end_date: string | null
  rent_amount: number
  deposit: number
  status: string
  payment_due_date: string | null
  created_at: string | null
}

interface ManagerPayment {
  id: number
  tenant_id: number
  lease_id: number
  property_id: number
  amount: number
  payment_date: string | null
  due_date: string | null
  status: string
  payment_type: string
  reference: string | null
  created_at: string | null
}

interface ManagerMaintenance {
  id: number
  tenant_id: number
  property_id: number
  unit_id: number | null
  title: string
  description: string | null
  category: string | null
  priority: string | null
  status: string
  assigned_manager_id: number | null
  cost: number
  created_at: string | null
  resolved_at: string | null
}

interface ManagerInquiry {
  id: number
  user_id: number
  property_id: number
  message: string | null
  status: string
  created_at: string | null
}

interface ManagerUnit {
  id: number
  property_id: number
  unit_number: string
  unit_type: string | null
  bedrooms: number | null
  bathrooms: number | null
  area: string | null
  rent: number
  status: string | null
  availability_date: string | null
  created_at: string | null
}

interface ManagerDashboard {
  properties: {
    total: number
    occupied: number
    vacant: number
    by_status: Record<string, number>
  }
  leases: {
    total: number
    active: number
    expiring_soon: number
  }
  tenants: {
    total: number
  }
  payments: {
    total: number
    pending: number
    overdue: number
    total_amount: number
    pending_amount: number
  }
  maintenance: {
    total: number
    open: number
    in_progress: number
  }
  inquiries: {
    total: number
    pending: number
  }
  recent_activity: {
    properties: Array<{
      id: number
      name: string
      city: string | null
      status: string
      updated_at: string | null
    }>
    leases: Array<{
      id: number
      tenant_id: number
      property_id: number
      status: string
      start_date: string | null
      end_date: string | null
      created_at: string | null
    }>
    maintenance: Array<{
      id: number
      property_id: number
      title: string
      status: string
      priority: string | null
      created_at: string | null
    }>
    payments: Array<{
      id: number
      tenant_id: number
      amount: number
      status: string
      payment_date: string | null
      created_at: string | null
    }>
  }
}

interface PaymentsOverview {
  total: number
  paid: number
  pending: number
  overdue: number
  total_amount: number
}

export const managerService = {
  // DASHBOARD
  async getDashboard(): Promise<ManagerDashboard> {
    return api.request('/manager/dashboard')
  },

  // PROPERTIES
  async getProperties(params?: { status?: string; skip?: number; limit?: number }): Promise<ManagerProperty[]> {
    const queryString = new URLSearchParams()
    if (params?.status) queryString.append('status', params.status)
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/manager/properties${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  async getProperty(propertyId: number): Promise<ManagerProperty> {
    return api.request(`/manager/properties/${propertyId}`)
  },

  async updateProperty(propertyId: number, data: Partial<ManagerProperty>): Promise<ManagerProperty> {
    return api.request(`/manager/properties/${propertyId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
  },

  // TENANTS
  async getTenants(params?: { skip?: number; limit?: number }): Promise<ManagerTenant[]> {
    const queryString = new URLSearchParams()
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/manager/tenants${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  // LEASES
  async getLeases(params?: { status?: string; skip?: number; limit?: number }): Promise<ManagerLease[]> {
    const queryString = new URLSearchParams()
    if (params?.status) queryString.append('status', params.status)
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/manager/leases${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  // PAYMENTS
  async getPayments(params?: { status?: string; skip?: number; limit?: number }): Promise<ManagerPayment[]> {
    const queryString = new URLSearchParams()
    if (params?.status) queryString.append('status', params.status)
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/manager/payments${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  async getPaymentsOverview(): Promise<PaymentsOverview> {
    return api.request('/manager/payments/overview')
  },

  // MAINTENANCE
  async getMaintenance(params?: { status?: string; skip?: number; limit?: number }): Promise<ManagerMaintenance[]> {
    const queryString = new URLSearchParams()
    if (params?.status) queryString.append('status', params.status)
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/manager/maintenance${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  async updateMaintenanceStatus(maintenanceId: number, status: string): Promise<{ id: number; status: string; message: string }> {
    return api.request(`/manager/maintenance/${maintenanceId}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    })
  },

  // INQUIRIES
  async getInquiries(params?: { status?: string; skip?: number; limit?: number }): Promise<ManagerInquiry[]> {
    const queryString = new URLSearchParams()
    if (params?.status) queryString.append('status', params.status)
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/manager/inquiries${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  // UNITS
  async getUnits(params?: { skip?: number; limit?: number }): Promise<ManagerUnit[]> {
    const queryString = new URLSearchParams()
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/manager/units${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  }
}

export type {
  ManagerProperty,
  ManagerTenant,
  ManagerLease,
  ManagerPayment,
  ManagerMaintenance,
  ManagerInquiry,
  ManagerUnit,
  ManagerDashboard,
  PaymentsOverview
}
