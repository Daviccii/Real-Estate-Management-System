import { api } from './api'

export interface Payment {
  id: number
  tenant_id: number
  lease_id: number
  property_id: number
  unit_id: number
  amount: string
  due_date: string
  payment_type?: string | null
  payment_date?: string | null
  payment_method?: string | null
  status: string
  reference?: string | null
  notes?: string | null
  created_at?: string
  updated_at?: string
}

export interface PaymentCreate {
  tenant_id: number
  lease_id: number
  property_id: number
  unit_id: number
  amount: string
  due_date: string
  payment_type?: string
  payment_date?: string
  payment_method?: string
  status?: string
  reference?: string
  notes?: string
}

export interface PaymentUpdate {
  amount?: string
  payment_date?: string
  payment_method?: string
  status?: string
  reference?: string
  notes?: string
}

export interface PaymentOverview {
  total_collected: string
  outstanding_balance: string
  overdue_amount: string
  total_revenue: string
  pending_payments: number
  paid_payments: number
  overdue_payments: number
}

export const paymentService = {
  list: async (params?: {
    skip?: number
    limit?: number
    property_id?: number
    unit_id?: number
    tenant_id?: number
    lease_id?: number
    status?: string
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.property_id) queryParams.append('property_id', params.property_id.toString())
    if (params?.unit_id) queryParams.append('unit_id', params.unit_id.toString())
    if (params?.tenant_id) queryParams.append('tenant_id', params.tenant_id.toString())
    if (params?.lease_id) queryParams.append('lease_id', params.lease_id.toString())
    if (params?.status) queryParams.append('status', params.status)
    
    return api.request<Payment[]>(`/api/payments/?${queryParams}`)
  },

  get: async (paymentId: number) => {
    return api.request<Payment>(`/api/payments/${paymentId}`)
  },

  create: async (data: PaymentCreate) => {
    return api.request<Payment>('/api/payments/', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  update: async (paymentId: number, data: PaymentUpdate) => {
    return api.request<Payment>(`/api/payments/${paymentId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' }
    })
  },

  delete: async (paymentId: number) => {
    return api.request<void>(`/api/payments/${paymentId}`, {
      method: 'DELETE'
    })
  },

  getTenantPayments: async (tenantId: number, params?: {
    skip?: number
    limit?: number
    status?: string
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.status) queryParams.append('status', params.status)
    
    return api.request<Payment[]>(`/api/payments/tenants/${tenantId}/payments?${queryParams}`)
  },

  getPropertyPayments: async (propertyId: number, params?: {
    skip?: number
    limit?: number
    status?: string
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.status) queryParams.append('status', params.status)
    
    return api.request<Payment[]>(`/api/payments/properties/${propertyId}/payments?${queryParams}`)
  },

  getLeasePayments: async (leaseId: number, params?: {
    skip?: number
    limit?: number
    status?: string
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.status) queryParams.append('status', params.status)
    
    return api.request<Payment[]>(`/api/payments/leases/${leaseId}/payments?${queryParams}`)
  },

  getOverview: async (params?: {
    property_id?: number
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.property_id) queryParams.append('property_id', params.property_id.toString())
    
    return api.request<PaymentOverview>(`/api/payments/overview?${queryParams}`)
  }
}