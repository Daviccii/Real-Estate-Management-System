import { api } from './api'
import { AuditLog } from '../types'

export async function getAuditLogs(params?: { entity_type?: string; action?: string; limit?: number }): Promise<AuditLog[]> {
  const q = new URLSearchParams()
  if (params?.entity_type) q.append('entity_type', params.entity_type)
  if (params?.action) q.append('action', params.action)
  if (params?.limit) q.append('limit', String(params.limit))
  const qs = q.toString() ? `?${q.toString()}` : ''
  return api.request<AuditLog[]>(`/api/audit-logs/${qs}`)
}
