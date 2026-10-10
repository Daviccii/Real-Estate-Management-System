import { api } from './api'
import {
  ServiceProviderProfile,
  MaintenanceQuote,
  MaintenanceWorkOrder,
  ProviderReviewPage,
  OpenMaintenanceRequest,
  Paginated
} from '../types'

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

export interface ProviderSearchParams {
  q?: string
  category?: string
  city?: string
  available_only?: boolean
  sort?: 'rating' | 'jobs' | 'newest' | 'name'
  page?: number
  page_size?: number
}

export interface OpenRequestSearchParams {
  q?: string
  category?: string
  city?: string
  page?: number
  page_size?: number
}

function toQueryString(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') search.set(key, String(value))
  })
  const query = search.toString()
  return query ? `?${query}` : ''
}

export async function getMarketplaceProviders(
  params: ProviderSearchParams = {}
): Promise<Paginated<ServiceProviderProfile>> {
  return api.request<Paginated<ServiceProviderProfile>>(
    `/api/service-marketplace/providers${toQueryString({ ...params })}`
  )
}

export async function getProviderProfile(providerId: number): Promise<ServiceProviderProfile> {
  return api.request<ServiceProviderProfile>(`/api/service-marketplace/providers/${providerId}`)
}

export async function getProviderReviews(
  providerId: number,
  page = 1,
  pageSize = 10
): Promise<ProviderReviewPage> {
  return api.request<ProviderReviewPage>(
    `/api/service-marketplace/providers/${providerId}/reviews${toQueryString({ page, page_size: pageSize })}`
  )
}

export async function getOpenRequests(
  params: OpenRequestSearchParams = {}
): Promise<Paginated<OpenMaintenanceRequest>> {
  return api.request<Paginated<OpenMaintenanceRequest>>(
    `/api/service-marketplace/open-requests${toQueryString({ ...params })}`
  )
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

export async function getWorkOrders(
  status?: string,
  maintenanceId?: number
): Promise<MaintenanceWorkOrder[]> {
  const params: Record<string, string | number | undefined> = {}
  if (status) params.status = status
  if (maintenanceId !== undefined) params.maintenance_id = maintenanceId
  return api.request<MaintenanceWorkOrder[]>(
    `/api/service-marketplace/work-orders${toQueryString(params)}`
  )
}

export async function submitWorkOrderReview(
  workOrderId: number,
  score: number,
  comment?: string
): Promise<ProviderReviewPage['items'][number]> {
  return api.request(`/api/service-marketplace/work-orders/${workOrderId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ score, comment })
  })
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
