import React from 'react'
import { useAuth } from '../../contexts/AuthContext'

const AdminSettings: React.FC = () => {
  const { user } = useAuth()

  return (
    <div className="page">
      <h1>Admin Settings</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
        {/* Account Settings */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Account Settings</h3>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>
              Email
            </label>
            <div style={{ padding: 8, background: 'var(--bg-secondary)', borderRadius: 4 }}>
              {user?.email || 'N/A'}
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>
              Name
            </label>
            <div style={{ padding: 8, background: 'var(--bg-secondary)', borderRadius: 4 }}>
              {user?.full_name || 'N/A'}
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>
              Role
            </label>
            <div style={{ padding: 8, background: 'var(--bg-secondary)', borderRadius: 4 }}>
              {user?.role || 'N/A'}
            </div>
          </div>
          <button className="button muted" disabled>
            Edit Profile (Requires Backend)
          </button>
        </div>

        {/* Platform Settings */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Platform Settings</h3>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'not-allowed' }}>
              <input type="checkbox" disabled />
              <span>Enable user registration</span>
            </label>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
              Requires backend implementation
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'not-allowed' }}>
              <input type="checkbox" disabled />
              <span>Require email verification</span>
            </label>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
              Requires backend implementation
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'not-allowed' }}>
              <input type="checkbox" disabled />
              <span>Enable property moderation</span>
            </label>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
              Requires backend implementation
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Security Settings</h3>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>
              Session Timeout
            </label>
            <select className="input" disabled style={{ width: '100%' }}>
              <option>60 minutes (Current)</option>
              <option>30 minutes</option>
              <option>120 minutes</option>
            </select>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
              Requires backend implementation
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>
              Password Policy
            </label>
            <div style={{ padding: 8, background: 'var(--bg-secondary)', borderRadius: 4 }}>
              Minimum 8 characters (Current)
            </div>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
              Requires backend implementation
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Notification Settings</h3>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'not-allowed' }}>
              <input type="checkbox" disabled />
              <span>Email notifications for new users</span>
            </label>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
              Requires backend implementation
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'not-allowed' }}>
              <input type="checkbox" disabled />
              <span>Email notifications for new inquiries</span>
            </label>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
              Requires backend implementation
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'not-allowed' }}>
              <input type="checkbox" disabled />
              <span>Email notifications for property updates</span>
            </label>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
              Requires backend implementation
            </div>
          </div>
        </div>
      </div>

      {/* Information */}
      <div className="card" style={{ marginTop: 24 }}>
        <h3 style={{ marginBottom: 12 }}>Platform Information</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 8, fontSize: 14 }}>
          <span style={{ color: 'var(--muted)' }}>Version:</span>
          <span>1.0.0</span>
          <span style={{ color: 'var(--muted)' }}>Environment:</span>
          <span>Development</span>
          <span style={{ color: 'var(--muted)' }}>Database:</span>
          <span>SQLite (Development)</span>
        </div>
      </div>
    </div>
  )
}

export default AdminSettings