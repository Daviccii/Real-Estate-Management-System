import { api } from './api'
import { Property, Payment, Maintenance } from '../types'

export interface OwnerPortfolioSummary {
  total_properties: number
  total_units: number
  occupied_units: number
  vacant_units: number
  occupancy_rate: number
  total_revenue_collected: number
  pending_payments: number
  active_maintenance: number
}

export interface AssignManagerAgentPayload {
  manager_id?: number | null
  agent_id?: number | null
}

export async function getOwnerPortfolioSummary(): Promise<OwnerPortfolioSummary> {
  return api.request<OwnerPortfolioSummary>('/api/owner/portfolio-summary')
}

export async function getOwnerProperties(): Promise<Property[]> {
  return api.request<Property[]>('/api/owner/properties')
}

export async function getOwnerFinancialLedger(): Promise<{ payments: Payment[]; total_collected: number; total_pending: number }> {
  return api.request<{ payments: Payment[]; total_collected: number; total_pending: number }>('/api/owner/financials')
}

export async function getOwnerMaintenance(): Promise<Maintenance[]> {
  return api.request<Maintenance[]>('/api/owner/maintenance')
}

export async function assignPropertyStaff(propertyId: number, payload: AssignManagerAgentPayload): Promise<Property> {
  return api.request<Property>(`/api/owner/properties/${propertyId}/assign`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}
