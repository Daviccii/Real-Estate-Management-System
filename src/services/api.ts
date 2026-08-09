import { getToken } from './token'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

async function request(path: string, opts: RequestInit = {}){
  const url = API_BASE + path
  const headers = new Headers(opts.headers as Record<string,string> || {})
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(url, {credentials: 'include', ...opts, headers})
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json().catch(()=>null)
}

export const api = { request }
