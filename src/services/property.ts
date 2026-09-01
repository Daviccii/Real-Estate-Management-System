import { api } from './api'
import { Property } from '../types'
import { getToken } from './token'

// Always uses the public endpoint for browsing — see list() below for why.
const buildQuery = (params?: { skip?: number; limit?: number; search?: string; property_type?: string; city?: string; status?: string; sort?: string; purpose?: string }) => {
  const qs = new URLSearchParams()
  if (typeof params?.skip === 'number') qs.set('skip', String(params.skip))
  if (typeof params?.limit === 'number') qs.set('limit', String(params.limit))
  if (params?.search) qs.set('search', params.search)
  if (params?.property_type) qs.set('property_type', params.property_type)
  if (params?.city) qs.set('city', params.city)
  if (params?.status) qs.set('status', params.status)
  if (params?.sort) qs.set('sort', params.sort)
  if (params?.purpose) qs.set('purpose', params.purpose)
  return qs.toString()
}

// FIX: previously branched to the authenticated '/properties' endpoint
// whenever getToken() returned truthy — including a stale/expired token left
// over from a previous session. That made GET /properties run through
// get_current_user, which 401s on an invalid token with "Could not validate
// credentials", and the raw error surfaced on Buy/Rent/Invest/Explore instead
// of a graceful empty/results state. property_repo.list_properties() doesn't
// filter by owner_id, so the authenticated route has no benefit here anyway —
// always use the public endpoint for browsing, same as meta() and
// marketInsights() below already do.
const list = async (params?: { skip?: number; limit?: number; search?: string; property_type?: string; city?: string; status?: string; sort?: string; purpose?: string }): Promise<Property[]> => {
  const query = buildQuery(params)
  return api.request(query ? `/properties/public?${query}` : '/properties/public')
}

const pagedList = async (page = 1, limit = 6, params?: { search?: string; property_type?: string; city?: string; status?: string; sort?: string; purpose?: string }): Promise<Property[]> => {
  const skip = Math.max(0, (page - 1) * limit)
  return list(Object.assign({}, params || {}, { skip, limit }))
}

// Total count of properties matching the given filters (no skip/limit/sort) —
// backs real "Page X of Y" pagination instead of inferring from a full page.
const count = async (params?: { search?: string; property_type?: string; city?: string; status?: string; purpose?: string }): Promise<number> => {
  const query = buildQuery(params)
  const res = await api.request<{ total: number }>(query ? `/properties/public/count?${query}` : '/properties/public/count')
  return res?.total ?? 0
}

// FIX: previously this branched on getToken() the same way `list()` used to,
// calling `/properties/meta` when logged in. But properties.py only defines
// `/properties/public/meta` — there is no authenticated `/properties/meta`
// route — so every logged-in user (including admins) hit a 404 here. Since
// this endpoint returns non-sensitive aggregate counts, it's safe to always
// hit the public route regardless of auth state.
const meta = async (): Promise<{ total: number; total_units: number } | null> => {
  return api.request('/properties/public/meta')
}

// FIX: same issue and same fix as meta() above — there is no authenticated
// `/properties/market-insights` route, only `/properties/public/market-insights`.
const marketInsights = async (): Promise<{
  total_properties: number
  by_purpose: Record<string, number>
  by_type: Record<string, number>
  top_locations: Array<{ city: string; count: number }>
  by_status: Record<string, number>
} | null> => {
  return api.request('/properties/public/market-insights')
}

// Authenticated single-property lookup — used by the owner/admin edit flow
// only (PropertyEdit.tsx). Enforces the ownership/admin check server-side.
const get = async (id: number): Promise<Property | null> => {
  return api.request(`/properties/${id}`)
}

// FIX: new — public single-property lookup with no auth/ownership check.
// PropertyDetailsPage should use this instead of get(), since any visitor
// viewing a listing (not just its owner) needs to see its details.
const getPublic = async (id: number): Promise<Property | null> => {
  return api.request(`/properties/public/${id}`)
}

const create = async (payload: Partial<Property>): Promise<Property | null> => {
  return api.request('/properties/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

const update = async (id: number, payload: Partial<Property>): Promise<Property | null> => {
  return api.request(`/properties/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

const remove = async (id: number): Promise<boolean> => {
  await api.request(`/properties/${id}`, { method: 'DELETE' })
  return true
}

export const propertyService = { list, pagedList, count, meta, marketInsights, get, getPublic, create, update, delete: remove }