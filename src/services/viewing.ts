import { api } from './api'
import { Viewing } from '../types'

export interface ViewingCreatePayload {
  property_id: number
  unit_id?: number | null
  viewing_date?: string
  start_time?: string
  end_time?: string
  scheduled_time?: string
  viewing_type?: string
  notes?: string
}

export interface ViewingStatusUpdatePayload {
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'rescheduled'
  cancellation_reason?: string
  feedback?: string
}

export interface AvailableSlotsResponse {
  property_id: number
  date: string
  host_id?: number
  available_slots: { start_time: string; end_time: string }[]
}

export async function getAvailableSlots(propertyId: number, date: string): Promise<AvailableSlotsResponse> {
  return api.request<AvailableSlotsResponse>(`/api/viewings/available-slots?property_id=${propertyId}&date=${date}`)
}

export async function requestViewing(payload: ViewingCreatePayload): Promise<Viewing> {
  return api.request<Viewing>('/api/viewings/book', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function getMyViewings(): Promise<Viewing[]> {
  return api.request<Viewing[]>('/api/viewings/my-viewings')
}

export async function getPropertyViewings(propertyId: number): Promise<Viewing[]> {
  return api.request<Viewing[]>(`/api/viewings/property/${propertyId}`)
}

export async function updateViewingStatus(id: number, payload: ViewingStatusUpdatePayload): Promise<Viewing> {
  return api.request<Viewing>(`/api/viewings/${id}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}
