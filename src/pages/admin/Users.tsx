import React, { useEffect, useState } from 'react'
import { adminService } from '../../services/admin'
import type { AdminUser } from '../../services/admin'
import ConfirmDialog from '../../components/ConfirmDialog'
import { useToast } from '../../components/ToastProvider'

const UsersManagement: React.FC = () => {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showEditRole, setShowEditRole] = useState(false)
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null)
  const [newRole, setNewRole] = useState('')
  const { addToast } = useToast()

  useEffect(() => {
    loadUsers()
  }, [roleFilter])

  const loadUsers = async () => {
    setLoading(true)
    setError(null)
    try {
      const params: any = {}
      if (roleFilter) params.role = roleFilter
      const data = await adminService.getUsers(params)
      setUsers(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchTerm || 
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.full_name && user.full_name.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesSearch
  })

  const handleDeleteUser = (user: AdminUser) => {
    setSelectedUser(user)
    setShowDeleteConfirm(true)
  }

  const handleEditRole = (user: AdminUser) => {
    setSelectedUser(user)
    setNewRole(user.role)
    setShowEditRole(true)
  }

  const handleRoleUpdate = async () => {
    if (!selectedUser || !newRole) return
    
    try {
      await adminService.updateUserRole(selectedUser.id, newRole)
      addToast({ 
        message: 'User role updated successfully', 
        type: 'success' 
      })
      setShowEditRole(false)
      setSelectedUser(null)
      loadUsers() // Reload the users list
    } catch (error: any) {
      addToast({ 
        message: error?.message || 'Failed to update user role', 
        type: 'error' 
      })
    }
  }

  const confirmDelete = async () => {
    if (!selectedUser) return
    
    try {
      await adminService.deleteUser(selectedUser.id)
      addToast({ 
        message: 'User deleted successfully', 
        type: 'success' 
      })
      setShowDeleteConfirm(false)
      setSelectedUser(null)
      loadUsers() // Reload the users list
    } catch (error: any) {
      addToast({ 
        message: error?.message || 'Failed to delete user', 
        type: 'error' 
      })
    }
  }

  const getRoleBadgeColor = (role: string) => {
    const colors: Record<string, string> = {
      admin: 'var(--danger)',
      manager: 'var(--primary)',
      agent: 'var(--success)',
      tenant: 'var(--warning)',
      user: 'var(--muted)'
    }
    return colors[role] || 'var(--muted)'
  }

  if (loading) {
    return (
      <div className="page">
        <h1>User Management</h1>
        <div className="empty">Loading users…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <h1>User Management</h1>
        <div className="card" style={{ color: 'var(--danger)' }}>
          Failed to load users: {error}
          <button className="button" onClick={loadUsers} style={{ marginTop: 12 }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>User Management</h1>
      
      {/* Filters */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="admin-filters">
          <input
            type="text"
            className="input"
            placeholder="Search by email or name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1, minWidth: 200 }}
          />
          
          <select
            className="input"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            style={{ minWidth: 150 }}
          >
            <option value="">All Roles</option>
            <option value="admin">Admin</option>
            <option value="manager">Manager</option>
            <option value="agent">Agent</option>
            <option value="tenant">Tenant</option>
            <option value="user">User</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      {filteredUsers.length === 0 ? (
        <div className="empty">
          {searchTerm || roleFilter ? 'No users match your filters' : 'No users found'}
        </div>
      ) : (
        <div className="card admin-table-container">
          <table className="admin-table">
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
                  <td data-label="ID" style={{ padding: 12 }}>{user.id}</td>
                  <td data-label="Email" style={{ padding: 12 }}>{user.email}</td>
                  <td data-label="Name" style={{ padding: 12 }}>{user.full_name || '—'}</td>
                  <td data-label="Role" style={{ padding: 12 }}>
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
                  <td data-label="Status" style={{ padding: 12 }}>
                    <span style={{ 
                      color: user.is_active ? 'var(--success)' : 'var(--danger)',
                      fontWeight: 600
                    }}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td data-label="Created" style={{ padding: 12, fontSize: 12 }}>
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td data-label="Actions" style={{ padding: 12, textAlign: 'right' }}>
                    <div className="admin-actions">
                      <button 
                        className="button muted" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleEditRole(user)}
                      >
                        Edit Role
                      </button>
                      <button 
                        className="button danger" 
                        style={{ padding: '4px 8px', fontSize: 12 }}
                        onClick={() => handleDeleteUser(user)}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog 
        open={showDeleteConfirm}
        title="Delete User"
        description={`Are you sure you want to delete ${selectedUser?.email}? This action cannot be undone.`}
        onConfirm={confirmDelete}
        onCancel={() => {
          setShowDeleteConfirm(false)
          setSelectedUser(null)
        }}
      />

      <ConfirmDialog 
        open={showEditRole}
        title="Edit User Role"
        description={`Change role for ${selectedUser?.email}`}
        onConfirm={handleRoleUpdate}
        onCancel={() => {
          setShowEditRole(false)
          setSelectedUser(null)
          setNewRole('')
        }}
      >
        <div style={{ marginTop: 16 }}>
          <label style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>Select Role:</label>
          <select
            className="input"
            value={newRole}
            onChange={(e) => setNewRole(e.target.value)}
            style={{ width: '100%' }}
          >
            <option value="user">User</option>
            <option value="tenant">Tenant</option>
            <option value="agent">Agent</option>
            <option value="manager">Manager</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </ConfirmDialog>
    </div>
  )
}

export default UsersManagement