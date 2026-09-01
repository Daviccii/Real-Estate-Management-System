import React from 'react'
import { Notification } from '../services/notification'

interface NotificationItemProps {
  notification: Notification
  onMarkAsRead?: (id: number) => void
  onDelete?: (id: number) => void
  onClose?: () => void
  compact?: boolean
}

const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onMarkAsRead,
  onDelete,
  onClose,
  compact = false,
}) => {
  const getPriorityColor = (priority: string) => {
    switch (priority?.toUpperCase()) {
      case 'CRITICAL':
        return '#d32f2f'
      case 'HIGH':
        return '#f57c00'
      case 'NORMAL':
        return '#1976d2'
      case 'LOW':
        return '#388e3c'
      default:
        return '#666'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type?.toUpperCase()) {
      case 'PAYMENT':
        return '💳'
      case 'LEASE':
        return '📋'
      case 'MAINTENANCE':
        return '🔧'
      case 'PROPERTY':
        return '🏠'
      case 'INQUIRY':
        return '❓'
      case 'LEAD':
        return '🎯'
      case 'APPOINTMENT':
        return '📅'
      case 'SYSTEM':
        return '⚙️'
      case 'SECURITY':
        return '🔒'
      case 'INVESTMENT':
        return '💰'
      default:
        return '📬'
    }
  }

  const createdAt = new Date(notification.created_at)
  const now = new Date()
  const diffMs = now.getTime() - createdAt.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  let timeAgo = ''
  if (diffMins < 1) timeAgo = 'Just now'
  else if (diffMins < 60) timeAgo = `${diffMins}m ago`
  else if (diffHours < 24) timeAgo = `${diffHours}h ago`
  else if (diffDays < 7) timeAgo = `${diffDays}d ago`
  else timeAgo = createdAt.toLocaleDateString()

  return (
    <div
      style={{
        padding: compact ? '12px' : '16px',
        borderBottom: '1px solid #e0e0e0',
        backgroundColor: !notification.is_read ? '#f5f5f5' : '#ffffff',
        cursor: 'pointer',
        transition: 'background-color 0.2s',
        display: 'flex',
        gap: '12px',
        alignItems: 'flex-start',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = !notification.is_read ? '#eeeeee' : '#fafafa'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = !notification.is_read ? '#f5f5f5' : '#ffffff'
      }}
    >
      {/* Icon */}
      <div style={{ fontSize: compact ? 20 : 24, flexShrink: 0 }}>
        {getTypeIcon(notification.notification_type)}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '4px',
          }}
        >
          <h4
            style={{
              margin: 0,
              fontSize: compact ? 13 : 14,
              fontWeight: notification.is_read ? 'normal' : 'bold',
              color: '#333',
            }}
          >
            {notification.title}
          </h4>
          <span
            style={{
              display: 'inline-block',
              padding: '2px 6px',
              backgroundColor: getPriorityColor(notification.priority),
              color: 'white',
              borderRadius: '3px',
              fontSize: '10px',
              fontWeight: 'bold',
              textTransform: 'uppercase',
              flexShrink: 0,
            }}
          >
            {notification.priority}
          </span>
        </div>

        <p
          style={{
            margin: '4px 0',
            fontSize: compact ? 12 : 13,
            color: '#666',
            lineHeight: '1.4',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {notification.message}
        </p>

        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '6px',
          }}
        >
          <span style={{ fontSize: '11px', color: '#999' }}>
            {timeAgo}
          </span>

          {!notification.is_read && (
            <span
              style={{
                display: 'inline-block',
                width: '8px',
                height: '8px',
                backgroundColor: '#2196f3',
                borderRadius: '50%',
                flexShrink: 0,
              }}
            />
          )}
        </div>
      </div>

      {/* Actions */}
      <div
        style={{
          display: 'flex',
          gap: '4px',
          flexShrink: 0,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {!notification.is_read && onMarkAsRead && (
          <button
            onClick={() => onMarkAsRead(notification.id)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px',
              fontSize: '12px',
              color: '#2196f3',
              fontWeight: 'bold',
              transition: 'color 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = '#1976d2'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = '#2196f3'
            }}
            title="Mark as read"
          >
            ✓
          </button>
        )}

        {onDelete && (
          <button
            onClick={() => onDelete(notification.id)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px',
              fontSize: '12px',
              color: '#d32f2f',
              fontWeight: 'bold',
              transition: 'color 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = '#b71c1c'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = '#d32f2f'
            }}
            title="Delete notification"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  )
}

export default NotificationItem
