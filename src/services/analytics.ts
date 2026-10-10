import { api } from './api'

// Type aliases (not interfaces) so the chart components can accept these
// points as Record<string, number | string>: TS gives implicit index
// signatures only to object-literal type aliases, never to interfaces.
export type FinancialPoint = {
  month: string
  income: number
  expenses: number
  net: number
}

export type PaymentsPoint = {
  month: string
  expected: number
  collected: number
  outstanding: number
}

export type MaintenancePoint = {
  month: string
  requests: number
  resolved: number
  cost: number
}

export interface AnalyticsKpis {
  properties: number
  total_units: number
  occupied_units: number
  vacant_units: number
  occupancy_rate: number
  active_leases: number
  leases_expiring_soon: number
  open_maintenance: number
  overdue_payments: number
  period_expected: number
  period_collected: number
  period_collection_rate: number
  period_expenses: number
  period_net: number
}

export interface PropertyLeaderboardRow {
  property_id: number
  name: string
  city: string
  units: number
  occupied: number
  occupancy_rate: number
  collected: number
  outstanding: number
}

export interface CityDistributionRow {
  city: string
  count: number
}

export interface CategoryDistributionRow {
  category: string
  requests: number
  open: number
  cost: number
}

export interface AnalyticsEnvelope {
  generated_at: string
  months: number
  period: { start: string; end: string }
  kpis: AnalyticsKpis
  series: {
    financial: FinancialPoint[]
    payments: PaymentsPoint[]
    maintenance: MaintenancePoint[]
  }
  distributions: {
    units_by_status: Record<string, number>
    leases_by_status: Record<string, number>
    properties_by_city: CityDistributionRow[]
    maintenance_by_category: CategoryDistributionRow[]
  }
  top_properties: PropertyLeaderboardRow[]
}

export async function getAnalyticsDashboard(months: number): Promise<AnalyticsEnvelope> {
  return api.request(`/analytics/dashboard?months=${months}`)
}
