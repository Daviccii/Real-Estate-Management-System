import { api } from './api'
import { getToken } from './token'

interface Inquiry {
  id: number
  user_id: number
  property_id: number
  message: string
  status: string
  created_at: string
  updated_at: string
}

interface InquiryCreate {
  property_id: number
  message: string
  status?: string
}

const create = async (data: InquiryCreate): Promise<Inquiry> => {
  return api.request('/inquiries/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

const list = async (): Promise<Inquiry[]> => {
  return api.request('/inquiries/')
}

const get = async (id: number): Promise<Inquiry> => {
  return api.request(`/inquiries/${id}`)
}

const update = async (id: number, data: Partial<InquiryCreate>): Promise<Inquiry> => {
  return api.request(`/inquiries/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

const remove = async (id: number): Promise<void> => {
  return api.request(`/inquiries/${id}`, { method: 'DELETE' })
}

export const inquiryService = { create, list, get, update, delete: remove }