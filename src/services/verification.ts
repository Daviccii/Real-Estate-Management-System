import { api } from './api'
import { VerificationRecord } from '../types'

export interface VerificationSubmitPayload {
  verification_type: 'identity' | 'ownership' | 'agency_license' | 'contractor_license'
  id_type?: string
  id_number?: string
  document_url: string
  property_id?: number
  business_name?: string
  license_number?: string
}

export interface VerificationReviewPayload {
  status: 'approved' | 'rejected'
  review_notes?: string
}

export async function submitVerification(payload: VerificationSubmitPayload): Promise<VerificationRecord> {
  return api.request<VerificationRecord>('/api/verifications/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function getMyVerifications(): Promise<VerificationRecord[]> {
  return api.request<VerificationRecord[]>('/api/verifications/my')
}

export async function getPendingVerifications(): Promise<VerificationRecord[]> {
  return api.request<VerificationRecord[]>('/api/verifications/pending')
}

export async function reviewVerification(id: number, payload: VerificationReviewPayload): Promise<VerificationRecord> {
  return api.request<VerificationRecord>(`/api/verifications/${id}/review`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}
