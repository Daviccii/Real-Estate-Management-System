export interface Property {
  id: number
  owner_id: number
  name: string
  property_type?: string | null
  description?: string | null
  address?: string | null
  city?: string | null
  county?: string | null
  country?: string | null
  status: string
  units_count?: number | null
}
