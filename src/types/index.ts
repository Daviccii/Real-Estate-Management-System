export type UserRole = 'user' | 'tenant' | 'agent' | 'manager' | 'owner' | 'service_provider' | 'admin'

export interface User {
  id: number
  email: string
  full_name?: string | null
  is_active: boolean
  role: UserRole
  roles_csv?: string | null
  phone?: string | null
  avatar_url?: string | null
  is_verified?: boolean
  created_at?: string
  updated_at?: string
}

export interface Property {
  id: number
  owner_id: number
  manager_id?: number | null
  agent_id?: number | null
  building_id?: number | null
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
  deposit?: string | null
  lease_term?: string | null
  availability_date?: string | null
  amenities?: string | null
  furnishing?: string | null
  parking_spaces?: number | null
  is_verified?: boolean
  created_at?: string
  updated_at?: string
}

export interface Building {
  id: number
  property_id: number
  name: string
  total_floors?: number | null
  units_count?: number | null
  amenities?: string | null
  year_built?: number | null
  description?: string | null
  created_at?: string
  updated_at?: string
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
  property_name?: string
  unit_number?: string
  tenant_name?: string
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
  property_name?: string
  unit_number?: string
  tenant_name?: string
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
  property_name?: string
  unit_number?: string
  tenant_name?: string
}

export interface RentalApplication {
  id: number
  applicant_id: number
  property_id: number
  unit_id?: number | null
  status: 'draft' | 'submitted' | 'under_review' | 'info_required' | 'approved' | 'rejected' | 'withdrawn'
  desired_move_in_date?: string | null
  monthly_income?: string | null
  employment_status?: string | null
  employer_name?: string | null
  job_title?: string | null
  credit_score_range?: string | null
  occupants_count?: number | null
  has_pets?: string | null
  emergency_contact_name?: string | null
  emergency_contact_phone?: string | null
  references_json?: string | null
  documents_json?: string | null
  reviewed_by_id?: number | null
  review_notes?: string | null
  reviewed_at?: string | null
  created_at: string
  updated_at: string
  property_name?: string
  unit_number?: string
  applicant_name?: string
  applicant_email?: string
}

export interface ApplicationReviewHistory {
  id: number
  application_id: number
  previous_status?: string | null
  new_status: string
  changed_by_id?: number | null
  notes?: string | null
  created_at: string
}

export interface Viewing {
  id: number
  property_id: number
  unit_id?: number | null
  prospect_id: number
  host_user_id?: number | null
  viewing_date: string
  start_time: string
  end_time: string
  status: 'pending' | 'requested' | 'confirmed' | 'completed' | 'cancelled' | 'rescheduled'
  notes?: string | null
  cancellation_reason?: string | null
  feedback?: string | null
  created_at: string
  property_name?: string
  prospect_name?: string
  host_name?: string
}

export interface Lead {
  id: number
  agent_id: number
  prospect_id?: number | null
  property_id?: number | null
  inquiry_id?: number | null
  stage: 'new' | 'contacted' | 'interested' | 'viewing' | 'applied' | 'approved' | 'closed' | 'lost'
  prospect_name?: string | null
  prospect_email?: string | null
  prospect_phone?: string | null
  estimated_budget?: string | null
  preferred_location?: string | null
  notes?: string | null
  commission_amount?: string | null
  created_at: string
  updated_at: string
  property_name?: string | null
}

export interface Conversation {
  id: number
  subject?: string | null
  property_id?: number | null
  created_at: string
  updated_at: string
  last_message?: string
  participants?: { user_id: number; role?: string; full_name?: string; email?: string }[]
  messages?: Message[]
}

export interface Message {
  id: number
  conversation_id: number
  sender_id: number
  body: string
  attachment_url?: string | null
  is_read: boolean
  created_at: string
  sender_name?: string
  sender_email?: string
}

export interface ServiceProviderProfile {
  id: number
  user_id: number
  company_name: string
  categories: string[]
  service_areas: string[]
  hourly_rate?: string | null
  license_number?: string | null
  insurance_verified: boolean
  rating_avg: number
  completed_jobs_count: number
  is_available: boolean
  created_at: string
  user_name?: string
  user_email?: string
  user_phone?: string
}

export interface MaintenanceQuote {
  id: number
  request_id: number
  provider_id: number
  quoted_amount: string
  estimated_hours?: number | null
  scope_description: string
  status: 'pending' | 'accepted' | 'rejected'
  created_at: string
  provider_name?: string
  company_name?: string
}

export interface MaintenanceWorkOrder {
  id: number
  request_id: number
  property_id: number
  unit_id?: number | null
  provider_id: number
  assigned_by_id: number
  status: 'assigned' | 'in_progress' | 'completed' | 'verified' | 'cancelled'
  scheduled_date?: string | null
  approved_budget?: string | null
  notes?: string | null
  before_photos_json?: string | null
  after_photos_json?: string | null
  completion_notes?: string | null
  created_at: string
  updated_at: string
  property_name?: string
  provider_company?: string
  request_title?: string
}

export interface VerificationRecord {
  id: number
  user_id: number
  verification_type: 'identity' | 'ownership' | 'agency_license' | 'contractor_license'
  status: 'pending' | 'approved' | 'rejected'
  id_type?: string | null
  id_number?: string | null
  document_url: string
  property_id?: number | null
  business_name?: string | null
  license_number?: string | null
  reviewed_by_id?: number | null
  review_notes?: string | null
  reviewed_at?: string | null
  created_at: string
  user_email?: string
  user_name?: string
}

export interface AuditLog {
  id: number
  user_id?: number | null
  user_email?: string | null
  action: string
  entity_type: string
  entity_id?: number | null
  details_json?: string | null
  ip_address?: string | null
  created_at: string
}

export interface PropertyMatchCriteria {
  max_budget?: number
  preferred_city?: string
  min_bedrooms?: number
  property_type?: string
  purpose?: string
  household_size?: number
  require_parking?: boolean
  require_security?: boolean
  require_balcony?: boolean
  furnishing?: string
  amenities?: string[]
}

export interface PropertyMatchResult {
  property: Property
  match_score: number
  match_reasons: string[]
}

export interface Building {
  id: number
  property_id: number
  name: string
  total_floors?: number | null
  units_count?: number | null
  amenities?: string | null
  year_built?: number | null
  description?: string | null
  created_at: string
  updated_at: string
  property_title?: string | null
}

