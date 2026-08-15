import { getToken } from './token'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number
  data: any
  constructor(message: string, status = 500, data: any = null){
    super(message)
    this.status = status
    this.data = data
  }
}

async function request(path: string, opts: RequestInit = {}){
  const url = API_BASE + path
  const headers = new Headers(opts.headers as Record<string,string> || {})
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(url, {credentials: 'include', ...opts, headers})
  const text = await res.text()
  let data: any = null
  try{ data = text ? JSON.parse(text) : null }catch(e){ data = text }
  if (!res.ok) {
    const message = (data && (data.detail || data.message)) || res.statusText || 'Request failed'
    throw new ApiError(message, res.status, data)
  }
  return data
}

export const api = { request }
