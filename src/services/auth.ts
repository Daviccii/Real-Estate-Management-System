import { api } from './api'
import { setToken, clearToken } from './token'

async function fetchUser(){
  return api.request('/users/me')
}

export const authService = {
  async register(email: string, password: string, full_name?: string){
    return api.request('/auth/register', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email,password,full_name})})
  },
  async login(email: string, password: string){
    const data = await api.request('/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email,password})})
    if (data?.access_token){
      setToken(data.access_token)
      const user = await fetchUser()
      return user
    }
    throw new Error('Login failed')
  },
  async refresh(){
    const data = await api.request('/auth/refresh', {method:'POST'})
    if (data?.access_token){
      setToken(data.access_token)
      const user = await fetchUser()
      return user
    }
    // no access token -> not authenticated
    clearToken()
    throw new Error('Not authenticated')
  },
  logout(){
    clearToken()
  }
}
