import { api } from './api'
import { getToken } from './token'

export type ReportType = 'occupancy' | 'payments' | 'maintenance' | 'financial'

export interface ReportColumn {
  key: string
  label: string
}

export interface ReportSummaryItem {
  key: string
  label: string
  value: number | string | null
}

export type ReportCell = number | string | null

export interface ReportEnvelope {
  report_type: ReportType
  generated_at: string
  filters: {
    date_from: string | null
    date_to: string | null
    property_id: number | null
  }
  summary: ReportSummaryItem[]
  columns: ReportColumn[]
  rows: Array<Record<string, ReportCell>>
}

export interface ReportParams {
  date_from?: string
  date_to?: string
  property_id?: number
}

function buildQuery(params: ReportParams): string {
  const query = new URLSearchParams()
  if (params.date_from) query.append('date_from', params.date_from)
  if (params.date_to) query.append('date_to', params.date_to)
  if (params.property_id !== undefined) query.append('property_id', String(params.property_id))
  return query.toString()
}

export async function getReport(reportType: ReportType, params: ReportParams = {}): Promise<ReportEnvelope> {
  const query = buildQuery(params)
  return api.request(`/reports/${reportType}${query ? '?' + query : ''}`)
}

export async function downloadReportCsv(reportType: ReportType, params: ReportParams = {}): Promise<void> {
  // CSV is an attachment, so it is fetched raw with the bearer token (the
  // JSON-only api.request helper cannot read it) — mirrors the privacy export.
  const token = getToken()
  const base = (import.meta.env.VITE_API_BASE || 'http://localhost:8000').replace(/\/+$/, '')
  const query = buildQuery(params)
  const res = await fetch(`${base}/api/v1/reports/${reportType}?${query ? query + '&' : ''}format=csv`, {
    credentials: 'include',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error('Could not download the report')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  a.download = `propnoxa_${reportType}_report_${stamp}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
