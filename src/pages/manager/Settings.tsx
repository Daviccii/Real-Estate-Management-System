import React from 'react'
import { useAuth } from '../../contexts/AuthContext'

const ManagerSettings: React.FC = () => {
  const { user } = useAuth()

  return (
    <div className="management-container">
      <div className="management-header">
        <h1>Settings</h1>
        <p>Manage your manager account settings</p>
      </div>

      <div className="settings-section">
        <div className="setting-card">
          <h3>Profile Information</h3>
          <div className="form-group">
            <label>Name</label>
            <input
              type="text"
              value={user?.full_name || ''}
              disabled
              className="input"
            />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="input"
            />
          </div>
          <div className="form-group">
            <label>Role</label>
            <input
              type="text"
              value={user?.role || ''}
              disabled
              className="input"
            />
          </div>
        </div>

        <div className="setting-card">
          <h3>Preferences</h3>
          <div className="form-group">
            <label>
              <input type="checkbox" disabled /> Email Notifications
            </label>
          </div>
          <div className="form-group">
            <label>
              <input type="checkbox" disabled /> SMS Alerts
            </label>
          </div>
          <div className="form-group">
            <label>
              <input type="checkbox" disabled /> Maintenance Notifications
            </label>
          </div>
        </div>

        <div className="setting-card">
          <h3>Account Security</h3>
          <button className="button" disabled>Change Password</button>
          <button className="button secondary" style={{ marginLeft: 8 }} disabled>
            Enable Two-Factor Authentication
          </button>
        </div>
      </div>

      <div style={{ marginTop: 24, padding: 16, backgroundColor: '#f5f5f5', borderRadius: 8 }}>
        <p style={{ fontSize: 12, color: '#666' }}>
          For now, account settings are read-only. Please contact an administrator to make changes.
        </p>
      </div>
    </div>
  )
}

export default ManagerSettings
