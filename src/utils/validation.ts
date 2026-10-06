export function isEmail(v?: string){
  if(!v) return false
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v)
}

export function validateAuth(email?: string, password?: string){
  const errors: Record<string,string> = {}
  if(!email) errors.email = 'Email is required'
  else if(!isEmail(email)) errors.email = 'Invalid email'
  if(!password) errors.password = 'Password is required'
  else if(password.length < 6) errors.password = 'Password must be at least 6 characters'
  return errors
}

export function validateProperty(payload:any){
  const errors: Record<string,string> = {}
  if(!payload?.name?.trim()) errors.name = 'Name is required'
  if (!['buy', 'rent', 'invest'].includes(payload?.purpose)) errors.purpose = 'Select a valid purpose'
  if(payload?.units_count != null && (!Number.isInteger(Number(payload.units_count)) || Number(payload.units_count) < 0)) errors.units_count = 'Units must be a whole number of 0 or more'
  for (const field of ['bedrooms', 'bathrooms']) {
    if (payload?.[field] != null && (!Number.isInteger(Number(payload[field])) || Number(payload[field]) < 0)) {
      errors[field] = `${field === 'bedrooms' ? 'Bedrooms' : 'Bathrooms'} must be a whole number of 0 or more`
    }
  }
  if (payload?.status && !['active', 'inactive', 'pending', 'sold', 'rented'].includes(payload.status)) errors.status = 'Select a valid status'
  if (payload?.construction_status && !['completed', 'under_construction', 'planned'].includes(payload.construction_status)) errors.construction_status = 'Select a valid construction status'
  for (const field of ['image_url', 'showroom_url', 'planned_finish_image_url']) {
    if (payload?.[field] && !/^https?:\/\/\S+$/i.test(payload[field])) errors[field] = 'Use a valid http(s) URL'
  }
  if (payload?.construction_status && payload.construction_status !== 'completed' && !payload?.completion_date) {
    errors.completion_date = 'Completion date is required for unfinished property'
  }
  return errors
}
