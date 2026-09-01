import React, { useEffect, useState } from 'react'
import { adminService } from '../../services/admin'
import type { AdminUser } from '../../services/admin'
import { useToast } from '../../components/ToastProvider'

interface RoleUsersProps {
  role: string
  title: string
  description: string
}

const RoleUsers: React.FC<RoleUsersProps> = ({ role, title, description }) => {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const { addToast } = useToast()

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await adminService.getUsers({ role })
      setUsers(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleStatus = async (user: AdminUser) => {
    try {
      await adminService.updateUserStatus(user.id, !user.is_active)
      addToast({ message: `${user.email} ${!user.is_active ? 'reactivated' : 'suspended'}`, type: 'success' })
      loadUsers()
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to update account status', type: 'error' })
    }
  }

  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchTerm || 
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.full_name && user.full_name.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  // FIX: 'manager' used var(--primary), which renders near-invisible against
  // this table's white background (same root cause as the "BUY" purpose
  // badge bug on the Properties Management page). Explicit hex values here
  // instead of depending on a CSS var whose actual resolved value wasn't
  // verified.
  const getRoleBadgeColor = (userRole: string) => {
    const colors: Record<string, string> = {
      admin: '#dc2626',
      manager: '#2648e6',
      agent: '#16a34a',
      tenant: '#d97706',
      user: '#64748b'
    }
    return colors[userRole] || '#64748b'
  }

  if (loading) {
    return (
      <div className="page">
        <h1>{title}</h1>
        <div className="empty">Loading {role}s…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>{title}</h1>
        <div className="card" style={{ color: 'var(--danger)' }}>
          Failed to load {role}s: {error}
          <button className="button" onClick={loadUsers} style={{ marginTop: 12 }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>{title}</h1>
      <p style={{ color: 'var(--muted)', marginBottom: 16 }}>{description}</p>
      
      {/* Search */}
      <div className="card" style={{ marginBottom: 16 }}>
        <input
          type="text"
          className="input"
          placeholder={`Search ${role}s by email or name...`}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{ width: '100%' }}
        />
      </div>

      {/* Users Table */}
      {filteredUsers.length === 0 ? (
        <div className="empty">
          {searchTerm ? `No ${role}s match your search` : `No ${role}s found`}
        </div>
      ) : (
        <div className="card">
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>ID</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Email</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Name</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Role</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Status</th>
                <th style={{ textAlign: 'left', padding: 12, fontWeight: 600 }}>Created</th>
                <th style={{ textAlign: 'right', padding: 12, fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr key={user.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: 12 }}>{user.id}</td>
                  <td style={{ padding: 12 }}>{user.email}</td>
                  <td style={{ padding: 12 }}>{user.full_name || '—'}</td>
                  <td style={{ padding: 12 }}>
                    <span style={{ 
                      color: 'white',
                      background: getRoleBadgeColor(user.role),
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: 600
                    }}>
                      {user.role.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: 12 }}>
                    <span style={{ 
                      color: user.is_active ? 'var(--success)' : 'var(--danger)',
                      fontWeight: 600
                    }}>
                      {user.is_active ? 'Active' : 'Suspended'}
                    </span>
                  </td>
                  <td style={{ padding: 12, fontSize: 12 }}>
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td style={{ padding: 12, textAlign: 'right' }}>
                    <button
                      className={user.is_active ? 'button danger' : 'button'}
                      style={{ padding: '4px 8px', fontSize: 12 }}
                      onClick={() => handleToggleStatus(user)}
                    >
                      {user.is_active ? 'Suspend' : 'Reactivate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default RoleUsers