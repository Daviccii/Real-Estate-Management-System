import { api } from './api'
import { Property } from '../types'

export const propertyService = {
  async list(): Promise<Property[]> {
    try {
      return await api.request('/properties/')
    } catch (e) {
      console.error(e)
      return []
    }
  }
}
