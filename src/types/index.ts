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
  image_url?: string | null
  price_label?: string | null
  price?: string | number | null
  bedrooms?: number | null
  bathrooms?: number | null
  area?: string | number | null
  purpose?: string | null
}

export type UserRole = 'user' | 'tenant' | 'agent' | 'manager' | 'admin'

export interface User {
  id: number
  email: string
  full_name?: string | null
  is_active: boolean
  role: UserRole
}
