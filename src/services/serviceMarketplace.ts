import { api } from './api'
import { ServiceProviderProfile, MaintenanceQuote, MaintenanceWorkOrder } from '../types'

export interface ProviderProfileUpdatePayload {
  company_name: string
  categories: string[]
  service_areas: string[]
  hourly_rate?: string
  license_number?: string
  is_available?: boolean
}

export interface QuoteCreatePayload {
  request_id: number
  quoted_amount: string
  estimated_hours?: number
  scope_description: string
}

export interface WorkOrderCreatePayload {
  request_id: number
  property_id: number
  unit_id?: number
  provider_id: number
  scheduled_date?: string
  approved_budget?: string
  notes?: string
}

export async function getMarketplaceProviders(category?: string): Promise<ServiceProviderProfile[]> {
  const query = category ? `?category=${category}` : ''
  return api.request<ServiceProviderProfile[]>(`/api/service-marketplace/providers${query}`)
}

export async function getProviderProfile(providerId: number): Promise<ServiceProviderProfile> {
  return api.request<ServiceProviderProfile>(`/api/service-marketplace/providers/${providerId}`)
}

export async function updateMyProviderProfile(payload: ProviderProfileUpdatePayload): Promise<ServiceProviderProfile> {
  return api.request<ServiceProviderProfile>('/api/service-marketplace/providers/profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function submitQuote(payload: QuoteCreatePayload): Promise<MaintenanceQuote> {
  return api.request<MaintenanceQuote>('/api/service-marketplace/quotes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function getQuotesForRequest(requestId: number): Promise<MaintenanceQuote[]> {
  return api.request<MaintenanceQuote[]>(`/api/service-marketplace/quotes/request/${requestId}`)
}

export async function acceptQuote(quoteId: number): Promise<MaintenanceWorkOrder> {
  return api.request<MaintenanceWorkOrder>(`/api/service-marketplace/quotes/${quoteId}/accept`, {
    method: 'POST'
  })
}

export async function getWorkOrders(status?: string): Promise<MaintenanceWorkOrder[]> {
  const query = status ? `?status=${status}` : ''
  return api.request<MaintenanceWorkOrder[]>(`/api/service-marketplace/work-orders${query}`)
}

export async function createWorkOrder(payload: WorkOrderCreatePayload): Promise<MaintenanceWorkOrder> {
  return api.request<MaintenanceWorkOrder>('/api/service-marketplace/work-orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function updateWorkOrderStatus(
  workOrderId: number,
  status: string,
  completionNotes?: string
): Promise<MaintenanceWorkOrder> {
  return api.request<MaintenanceWorkOrder>(`/api/service-marketplace/work-orders/${workOrderId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, completion_notes: completionNotes })
  })
}
