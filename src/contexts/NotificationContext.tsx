import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { notificationService, type Notification } from '../services/notification'

interface NotificationContextType {
  notifications: Notification[]
  unreadCount: number
  loading: boolean
  error: string | null
  
  loadNotifications: () => Promise<void>
  loadUnreadNotifications: () => Promise<void>
  refreshUnreadCount: () => Promise<void>
  markAsRead: (notificationId: number) => Promise<void>
  markAsUnread: (notificationId: number) => Promise<void>
  markAllAsRead: () => Promise<void>
  deleteNotification: (notificationId: number) => Promise<void>
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadNotifications = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await notificationService.getNotifications({ limit: 100 })
      setNotifications(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load notifications')
    } finally {
      setLoading(false)
    }
  }, [])

  const loadUnreadNotifications = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await notificationService.getUnreadNotifications({ limit: 100 })
      setNotifications(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load unread notifications')
    } finally {
      setLoading(false)
    }
  }, [])

  const refreshUnreadCount = useCallback(async () => {
    try {
      const response = await notificationService.getUnreadCount()
      setUnreadCount(response.unread_count)
    } catch (err) {
      console.error('Failed to refresh unread count:', err)
    }
  }, [])

  const markAsRead = useCallback(async (notificationId: number) => {
    try {
      await notificationService.markAsRead(notificationId)
      // Update local state
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (err: any) {
      setError(err?.message || 'Failed to mark notification as read')
    }
  }, [])

  const markAsUnread = useCallback(async (notificationId: number) => {
    try {
      await notificationService.markAsUnread(notificationId)
      // Update local state
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: false } : n)
      )
      setUnreadCount(prev => prev + 1)
    } catch (err: any) {
      setError(err?.message || 'Failed to mark notification as unread')
    }
  }, [])

  const markAllAsRead = useCallback(async () => {
    try {
      await notificationService.markAllAsRead()
      // Update local state
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch (err: any) {
      setError(err?.message || 'Failed to mark all as read')
    }
  }, [])

  const deleteNotification = useCallback(async (notificationId: number) => {
    try {
      await notificationService.deleteNotification(notificationId)
      // Update local state
      const notification = notifications.find(n => n.id === notificationId)
      setNotifications(prev => prev.filter(n => n.id !== notificationId))
      if (notification && !notification.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1))
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to delete notification')
    }
  }, [notifications])

  // Load unread count on mount
  useEffect(() => {
    refreshUnreadCount()
  }, [refreshUnreadCount])

  const value: NotificationContextType = {
    notifications,
    unreadCount,
    loading,
    error,
    loadNotifications,
    loadUnreadNotifications,
    refreshUnreadCount,
    markAsRead,
    markAsUnread,
    markAllAsRead,
    deleteNotification,
  }

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  )
}

export const useNotifications = () => {
  const context = useContext(NotificationContext)
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider')
  }
  return context
}
