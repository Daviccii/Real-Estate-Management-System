import { api } from './api'
import { Property, Lead, Viewing, RentalApplication } from '../types'

export interface AgentWorkspaceData {
  total_leads: number
  active_listings: number
  upcoming_viewings: number
  pending_applications: number
  total_commissions_earned: number
}

export async function getAgentWorkspace(): Promise<AgentWorkspaceData> {
  return api.request<AgentWorkspaceData>('/api/agent/workspace')
}

export async function getAgentListings(): Promise<Property[]> {
  return api.request<Property[]>('/api/agent/listings')
}

export async function getAgentCommissions(): Promise<{ leads: Lead[]; total_commission: number }> {
  return api.request<{ leads: Lead[]; total_commission: number }>('/api/agent/commissions')
}
