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

export interface Unit {
  id: number
  property_id: number
  unit_number: string
  unit_type?: string | null
  bedrooms?: number | null
  bathrooms?: number | null
  area?: string | null
  rent?: string | null
  status: string
  availability_date?: string | null
  created_at?: string
  updated_at?: string
}

export interface Lease {
  id: number
  tenant_id: number
  unit_id: number
  property_id: number
  start_date: string
  end_date: string
  rent_amount: string
  deposit?: string | null
  payment_due_date?: number | null
  status: string
  notes?: string | null
  created_at?: string
  updated_at?: string
}

export interface Payment {
  id: number
  tenant_id: number
  lease_id: number
  property_id: number
  unit_id: number
  amount: string
  due_date: string
  payment_type?: string | null
  payment_date?: string | null
  payment_method?: string | null
  status: string
  reference?: string | null
  notes?: string | null
  created_at?: string
  updated_at?: string
}

export interface Maintenance {
  id: number
  property_id: number
  title: string
  description?: string | null
  category?: string | null
  priority: string
  status: string
  tenant_id?: number | null
  unit_id?: number | null
  assigned_manager_id?: number | null
  cost?: string | null
  notes?: string | null
  created_at?: string
  updated_at?: string
  resolved_at?: string | null
}
