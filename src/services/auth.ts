import { api } from './api'
import { setToken, clearToken } from './token'

async function fetchUser(){
  return api.request('/users/me')
}

export interface TenantRegistrationData {
  email: string
  password: string
  full_name: string
  phone?: string
  preferred_locations?: string
  min_budget?: number
  max_budget?: number
  preferred_bedrooms?: number
  preferred_property_type?: string
  desired_move_in_date?: string
  household_size?: number
  has_pets?: string
  employment_status?: string
  monthly_income?: number
  employer_name?: string
  job_title?: string
}

export interface OwnerRegistrationData {
  email: string
  password: string
  full_name: string
  phone?: string
  owner_type?: string
  company_name?: string
  tax_pin?: string
  national_id_number?: string
  payout_phone?: string
  bank_name?: string
  bank_account_number?: string
  bank_account_name?: string
  emergency_contact?: string
}

export interface AgentRegistrationData {
  email: string
  password: string
  full_name: string
  phone?: string
  agency_name?: string
  license_number?: string
  operating_areas?: string
  specialties?: string
  years_experience?: number
  bio?: string
  commission_rate?: number
}

export interface ProviderRegistrationData {
  email: string
  password: string
  full_name: string
  phone?: string
  business_name: string
  specialty: string
  license_number?: string
  hourly_rate?: string
  years_experience?: number
  bio?: string
  service_areas?: string
}

export const authService = {
  async register(email: string, password: string, full_name?: string){
    return api.request('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name })
    })
  },

  async registerTenant(data: TenantRegistrationData){
    const res = await api.request('/auth/register/tenant', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (res?.access_token) {
      setToken(res.access_token)
    }
    return res
  },

  async registerOwner(data: OwnerRegistrationData){
    const res = await api.request('/auth/register/owner', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (res?.access_token) {
      setToken(res.access_token)
    }
    return res
  },

  async registerAgent(data: AgentRegistrationData){
    const res = await api.request('/auth/register/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (res?.access_token) {
      setToken(res.access_token)
    }
    return res
  },

  async registerProvider(data: ProviderRegistrationData){
    const res = await api.request('/auth/register/provider', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (res?.access_token) {
      setToken(res.access_token)
    }
    return res
  },

  async login(email: string, password: string){
    const data = await api.request('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    if (data?.access_token){
      setToken(data.access_token)
      let user = data.user
      if (!user) {
        user = await fetchUser()
      }
      return { user, redirect_url: data.redirect_url || '/app' }
    }
    throw new Error('Login failed')
  },

  async refresh(){
    const data = await api.request('/auth/refresh', { method: 'POST' })
    if (data?.access_token){
      setToken(data.access_token)
      const user = await fetchUser()
      return user
    }
    clearToken()
    throw new Error('Not authenticated')
  },

  async logout(){
    try {
      await api.request('/auth/logout', { method: 'POST' })
    } catch(e) {
      // ignore
    }
    clearToken()
  }
}

