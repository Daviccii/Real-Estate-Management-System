import { api } from './api'
import { getToken } from './token'

export interface DeletionRequestInfo {
  id: number
  user_id: number | null
  status: 'pending' | 'completed' | 'cancelled' | 'declined'
  reason: string | null
  requested_at: string | null
  processed_at: string | null
  notes: string | null
}

export interface ConsentPayload {
  consent_type: 'cookie_analytics' | 'cookie_marketing' | 'tos'
  granted: boolean
  policy_version?: string
  client_id?: string
}

export async function exportMyData(): Promise<void> {
  // The endpoint responds with an attachment; the token must travel in the
  // header, so we fetch through the same base+auth logic rather than a link.
  const token = getToken()
  const base = (import.meta.env.VITE_API_BASE || 'http://localhost:8000').replace(/\/+$/, '')
  const res = await fetch(`${base}/api/v1/privacy/export`, {
    credentials: 'include',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error('Could not download your data export')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'propnoxa-data-export.json'
  a.click()
  URL.revokeObjectURL(url)
}

export async function recordConsent(payload: ConsentPayload): Promise<void> {
  await api.request('/privacy/consent', { method: 'POST', body: JSON.stringify(payload) })
}

export async function getMyDeletionRequest(): Promise<{ request: DeletionRequestInfo | null }> {
  return api.request('/privacy/delete-request')
}

export async function requestAccountDeletion(reason?: string): Promise<{ request: DeletionRequestInfo; created: boolean; message: string }> {
  return api.request('/privacy/delete-request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason: reason || null }),
  })
}

export async function cancelAccountDeletion(): Promise<void> {
  await api.request('/privacy/delete-request', { method: 'DELETE' })
}

export async function listDeletionRequests(): Promise<{ requests: DeletionRequestInfo[] }> {
  return api.request('/privacy/admin/deletion-requests')
}

export async function executeDeletionRequest(id: number): Promise<{ status: string }> {
  return api.request(`/privacy/admin/deletion-requests/${id}/execute`, { method: 'POST' })
}

export async function declineDeletionRequest(id: number, notes?: string): Promise<{ request: DeletionRequestInfo }> {
  return api.request(`/privacy/admin/deletion-requests/${id}/decline`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes: notes || null }),
  })
}
