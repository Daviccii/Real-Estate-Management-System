import { api } from './api'
import { Lead } from '../types'

export interface LeadCreatePayload {
  property_id?: number
  prospect_id?: number
  inquiry_id?: number
  prospect_name?: string
  prospect_email?: string
  prospect_phone?: string
  estimated_budget?: string
  preferred_location?: string
  notes?: string
  stage?: string
}

export interface LeadStageUpdatePayload {
  stage: 'new' | 'contacted' | 'interested' | 'viewing' | 'applied' | 'approved' | 'closed' | 'lost'
  notes?: string
  commission_amount?: string
}

export async function getLeads(stage?: string): Promise<Lead[]> {
  const query = stage ? `?stage=${stage}` : ''
  return api.request<Lead[]>(`/api/leads/${query}`)
}

export async function createLead(payload: LeadCreatePayload): Promise<Lead> {
  return api.request<Lead>('/api/leads/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function updateLeadStage(id: number, payload: LeadStageUpdatePayload): Promise<Lead> {
  return api.request<Lead>(`/api/leads/${id}/stage`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function convertInquiryToLead(inquiryId: number): Promise<Lead> {
  return api.request<Lead>(`/api/leads/from-inquiry/${inquiryId}`, {
    method: 'POST'
  })
}
