import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import MfaPanel from '../../components/MfaPanel'
import { api } from '../../services/api'
import { useToast } from '../../components/ToastProvider'

const ManagerSettings: React.FC = () => {
  const { user } = useAuth()
  const { addToast } = useToast()

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [changingPassword, setChangingPassword] = useState(false)
  const [showPasswordForm, setShowPasswordForm] = useState(false)

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (newPassword !== confirmPassword) {
      addToast({ message: 'New passwords do not match', type: 'error' })
      return
    }
    if (newPassword.length < 8) {
      addToast({ message: 'Password must be at least 8 characters', type: 'error' })
      return
    }
    setChangingPassword(true)
    try {
      await api.request('/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      })
      addToast({ message: 'Password changed successfully', type: 'success' })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setShowPasswordForm(false)
    } catch (err: any) {
      addToast({ message: err?.message || 'Failed to change password', type: 'error' })
    } finally {
      setChangingPassword(false)
    }
  }

  return (
    <div className="management-container">
      <div className="management-header">
       <span className="manager-eyebrow">Workspace preferences</span>
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
          {!showPasswordForm ? (
            <button className="button" onClick={() => setShowPasswordForm(true)}>Change Password</button>
          ) : (
            <form onSubmit={handleChangePassword} style={{ display: 'grid', gap: 12 }}>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>Current Password</label>
                <input
                  type="password"
                  className="input"
                  value={currentPassword}
                  onChange={e => setCurrentPassword(e.target.value)}
                  required
                  disabled={changingPassword}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>New Password</label>
                <input
                  type="password"
                  className="input"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  required
                  disabled={changingPassword}
                  placeholder="Min 8 characters, uppercase, lowercase, digit, special char"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontSize: 12, fontWeight: 600 }}>Confirm New Password</label>
                <input
                  type="password"
                  className="input"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  required
                  disabled={changingPassword}
                />
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  type="submit"
                  className="button"
                  disabled={changingPassword || !currentPassword || !newPassword || !confirmPassword}
                >
                  {changingPassword ? 'Changing...' : 'Change Password'}
                </button>
                <button
                  type="button"
                  className="button muted"
                  onClick={() => setShowPasswordForm(false)}
                  disabled={changingPassword}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>

        <MfaPanel />
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
