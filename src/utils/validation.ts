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
  if(!payload?.name) errors.name = 'Name is required'
  if(payload?.units_count != null && Number(payload.units_count) < 0) errors.units_count = 'Units must be 0 or more'
  return errors
}
