import { api } from './api'
import { Lease, Payment, Maintenance, RentalApplication } from '../types'

export interface TenantDashboardData {
  active_lease?: Lease | null
  pending_payments: Payment[]
  active_maintenance: Maintenance[]
  applications: RentalApplication[]
}

export async function getTenantDashboard(): Promise<TenantDashboardData> {
  return api.request<TenantDashboardData>('/api/tenant/dashboard')
}

export async function getMyTenancy(): Promise<Lease | null> {
  return api.request<Lease | null>('/api/tenant/my-tenancy')
}

export async function getMyPayments(): Promise<Payment[]> {
  return api.request<Payment[]>('/api/tenant/payments')
}

export async function getMyMaintenance(): Promise<Maintenance[]> {
  return api.request<Maintenance[]>('/api/tenant/maintenance')
}
