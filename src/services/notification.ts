import { api } from './api'

export interface Notification {
  id: number
  recipient_id: number
  notification_type: string
  title: string
  message: string
  priority: string
  related_entity_type: string | null
  related_entity_id: number | null
  is_read: boolean
  created_at: string
  read_at: string | null
}

export interface UnreadCountResponse {
  unread_count: number
}

export const notificationService = {
  // Get all notifications
  async getNotifications(params?: { 
    skip?: number
    limit?: number
    notification_type?: string
    priority?: string
  }): Promise<Notification[]> {
    const queryString = new URLSearchParams()
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    if (params?.notification_type) queryString.append('notification_type', params.notification_type)
    if (params?.priority) queryString.append('priority', params.priority)
    
    const url = `/notifications${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  // Get unread notifications
  async getUnreadNotifications(params?: {
    skip?: number
    limit?: number
  }): Promise<Notification[]> {
    const queryString = new URLSearchParams()
    if (params?.skip !== undefined) queryString.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryString.append('limit', params.limit.toString())
    
    const url = `/notifications/unread${queryString.toString() ? '?' + queryString.toString() : ''}`
    return api.request(url)
  },

  // Get unread count
  async getUnreadCount(): Promise<UnreadCountResponse> {
    return api.request('/notifications/unread/count')
  },

  // Get single notification
  async getNotification(notificationId: number): Promise<Notification> {
    return api.request(`/notifications/${notificationId}`)
  },

  // Mark as read
  async markAsRead(notificationId: number): Promise<Notification> {
    return api.request(`/notifications/${notificationId}/read`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
  },

  // Mark as unread
  async markAsUnread(notificationId: number): Promise<Notification> {
    return api.request(`/notifications/${notificationId}/unread`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
  },

  // Mark all as read
  async markAllAsRead(): Promise<{ message: string; count: number }> {
    return api.request('/notifications/read-all', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
  },

  // Delete notification
  async deleteNotification(notificationId: number): Promise<{ message: string }> {
    return api.request(`/notifications/${notificationId}`, {
      method: 'DELETE'
    })
  }
}

export type { Notification, UnreadCountResponse }
