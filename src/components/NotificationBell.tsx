import React, { useEffect } from 'react'
import { useNotifications } from '../contexts/NotificationContext'

interface NotificationBellProps {
  onClick?: () => void
  showLabel?: boolean
}

const NotificationBell: React.FC<NotificationBellProps> = ({ onClick, showLabel = false }) => {
  const { unreadCount, refreshUnreadCount } = useNotifications()

  // Refresh unread count every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      refreshUnreadCount()
    }, 30000)
    return () => clearInterval(interval)
  }, [refreshUnreadCount])

  return (
    <button
      onClick={onClick}
      style={{
        position: 'relative',
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        fontSize: 20,
        padding: 0,
        margin: 0,
        color: 'inherit',
      }}
      aria-label="Notifications"
    >
      🔔
      {unreadCount > 0 && (
        <span
          style={{
            position: 'absolute',
            top: -8,
            right: -8,
            background: '#d32f2f',
            color: 'white',
            borderRadius: '50%',
            width: 20,
            height: 20,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 12,
            fontWeight: 'bold',
            border: '2px solid white',
          }}
        >
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
      {showLabel && unreadCount > 0 && (
        <span style={{ marginLeft: 8, fontSize: 12 }}>
          {unreadCount} new
        </span>
      )}
    </button>
  )
}

export default NotificationBell
