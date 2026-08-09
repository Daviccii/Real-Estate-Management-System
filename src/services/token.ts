let _token: string | null = null

export function getToken(){
  return _token
}

export function setToken(t: string | null){
  _token = t
}

export function clearToken(){
  _token = null
}
