let _token: string | null = null

export function getToken(){
  return _token
}

export function setToken(t: string | null){
  _token = t
  try{ if(t) localStorage.setItem('access_token', t); else localStorage.removeItem('access_token') }catch(e){}
}

export function clearToken(){
  _token = null
  try{ localStorage.removeItem('access_token') }catch(e){}
}

// initialize from storage
try{
  const existing = localStorage.getItem('access_token')
  if(existing) _token = existing
}catch(e){}
