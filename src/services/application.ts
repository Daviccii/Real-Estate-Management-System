import { api } from './api'
import { RentalApplication } from '../types'

export interface ApplicationCreatePayload {
  property_id: number
  unit_id?: number | null
  desired_move_in_date?: string | null
  monthly_income?: string | null
  employment_status?: string | null
  employer_name?: string | null
  job_title?: string | null
  credit_score_range?: string | null
  occupants_count?: number
  has_pets?: string | null
  emergency_contact_name?: string | null
  emergency_contact_phone?: string | null
  references_json?: string | null
  documents_json?: string | null
}

export interface ApplicationStatusUpdatePayload {
  status: 'draft' | 'submitted' | 'under_review' | 'info_required' | 'approved' | 'rejected' | 'withdrawn'
  review_notes?: string
}

export interface ConvertToLeasePayload {
  unit_id?: number
  start_date: string
  end_date: string
  rent_amount: string
  deposit?: string
  payment_due_date?: number
}

export async function submitApplication(payload: ApplicationCreatePayload): Promise<RentalApplication> {
  return api.request<RentalApplication>('/api/applications/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function getMyApplications(): Promise<RentalApplication[]> {
  return api.request<RentalApplication[]>('/api/applications/my')
}

export async function getPropertyApplications(propertyId: number): Promise<RentalApplication[]> {
  return api.request<RentalApplication[]>(`/api/applications/property/${propertyId}`)
}

export async function getApplicationDetails(id: number): Promise<RentalApplication> {
  return api.request<RentalApplication>(`/api/applications/${id}`)
}

export async function updateApplicationStatus(id: number, payload: ApplicationStatusUpdatePayload): Promise<RentalApplication> {
  return api.request<RentalApplication>(`/api/applications/${id}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function convertToLease(id: number, payload: ConvertToLeasePayload): Promise<any> {
  return api.request<any>(`/api/applications/${id}/convert-to-lease`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}
