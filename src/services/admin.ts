import { api } from './api'

interface DashboardStats {
  users: {
    total: number
    by_role: Record<string, number>
  }
  properties: {
    total: number
    active: number
    by_purpose: Record<string, number>
  }
  inquiries: {
    total: number
    by_status: Record<string, number>
  }
  recent_activity: {
    properties: Array<{
      id: number
      name: string
      city: string | null
      owner_id: number
      created_at: string | null
    }>
    inquiries: Array<{
      id: number
      user_id: number
      property_id: number
      status: string
      created_at: string | null
    }>
  }
}

interface AdminUser {
  id: number
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string | null
}

interface AdminProperty {
  id: number
  name: string
  city: string | null
  owner_id: number
  status: string
  purpose: string | null
  property_type: string | null
  units_count: number | null
  price_label: string | null
  created_at: string | null
}

interface AdminInquiry {
  id: number
  user_id: number
  property_id: number
  message: string
  status: string
  created_at: string | null
  updated_at: string | null
}

interface MarketInsights {
  total_properties: number
  by_purpose: Record<string, number>
  by_type: Record<string, number>
  top_locations: Array<{ city: string; count: number }>
  by_status: Record<string, number>
}

export const adminService = {
  async getDashboard(): Promise<DashboardStats> {
    return api.request('/admin/dashboard')
  },

  async getUsers(params?: { role?: string; skip?: number; limit?: number }): Promise<AdminUser[]> {
    const queryString = new URLSearchParams()
    if (params?.role) queryString.append('role', params.role)
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/admin/users${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  async getProperties(params?: { status?: string; skip?: number; limit?: number }): Promise<AdminProperty[]> {
    const queryString = new URLSearchParams()
    if (params?.status) queryString.append('status', params.status)
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/admin/properties${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  async getInquiries(params?: { status?: string; skip?: number; limit?: number }): Promise<AdminInquiry[]> {
    const queryString = new URLSearchParams()
    if (params?.status) queryString.append('status', params.status)
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/admin/inquiries${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  async getMarketInsights(): Promise<MarketInsights> {
    return api.request('/admin/market-insights')
  }
}